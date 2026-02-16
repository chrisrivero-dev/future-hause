import os
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


REPO_ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())

LM_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
LM_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lmstudio")
LM_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-14b-instruct-mlx")

MAX_ATTEMPTS = int(os.getenv("LOCAL_CLAUDE_MAX_ATTEMPTS", "6"))


@dataclass
class Job:
    id: str
    prompt: str
    files: str
    status: str  # queued|running|needs_review|failed|applied|rejected
    attempt: int
    last_error: str
    patch: str


JOBS: Dict[str, Job] = {}
LOCK = threading.Lock()


def _read_contract() -> str:
    # Support both names
    for name in ["AI_CONTRACT.md", "ai_contract.md"]:
        p = REPO_ROOT / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace").strip()
    return (
        "HARD RULES:\n"
        "1) Output MUST be a git-style unified diff (diff --git, --- a/, +++ b/).\n"
        "2) Modify ONLY the provided files.\n"
        "3) Minimal diff. No refactors unless requested.\n"
        "4) No commentary. Patch only.\n"
    ).strip()


def _call_llm(system: str, user: str) -> str:
    url = f"{LM_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {LM_API_KEY}"}
    payload = {
        "model": LM_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return t


def _ensure_git_headers(patch: str) -> str:
    """
    Normalize common LLM diff output into git-apply friendly format.
    - Strips markdown fences
    - Ensures diff --git a/ b/ headers exist when possible
    """
    patch = _strip_markdown_fences(patch)
    lines = patch.splitlines()

    if not lines:
        return ""

    # If it already starts with diff --git, trust it.
    if lines[0].startswith("diff --git "):
        return patch.strip()

    # If it starts with --- <path> / +++ <path>, inject diff --git + a/ b/
    if lines[0].startswith("--- ") and len(lines) > 1 and lines[1].startswith("+++ "):
        oldp = lines[0].replace("--- ", "").strip()
        newp = lines[1].replace("+++ ", "").strip()

        # Prefer same path; otherwise keep oldp for header
        path = oldp if oldp == newp else oldp

        # Rewrite headers to a/ b/
        lines[0] = f"--- a/{path}"
        lines[1] = f"+++ b/{path}"
        lines.insert(0, f"diff --git a/{path} b/{path}")
        return "\n".join(lines).strip()

    return patch.strip()


def _git_apply_check(patch_text: str) -> Optional[str]:
    p = subprocess.run(
        ["git", "apply", "--check", "--whitespace=nowarn", "-"],
        cwd=str(REPO_ROOT),
        input=patch_text,
        text=True,
        capture_output=True,
    )
    if p.returncode == 0:
        return None
    return (p.stderr or p.stdout or "git apply --check failed").strip()


def _git_apply(patch_text: str) -> Optional[str]:
    p = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=str(REPO_ROOT),
        input=patch_text,
        text=True,
        capture_output=True,
    )
    if p.returncode == 0:
        return None
    return (p.stderr or p.stdout or "git apply failed").strip()


def _build_context(files_csv: str) -> str:
    files = [f.strip() for f in files_csv.split(",") if f.strip()]
    blocks = []
    blocks.append(f"REPO_ROOT: {REPO_ROOT}")
    blocks.append("FILES_PROVIDED:\n" + "\n".join(files))

    for rel in files:
        fp = REPO_ROOT / rel
        if not fp.exists() or fp.is_dir():
            blocks.append(f"\nFILE: {rel}\nERROR: not found or is directory\n")
            continue
        content = fp.read_text(encoding="utf-8", errors="replace")
        # keep it reasonable; local models drift with huge context
        if len(content) > 18000:
            content = content[:9000] + "\n\n# ...TRUNCATED...\n\n" + content[-9000:]
        blocks.append(f"\nFILE: {rel}\n```text\n{content}\n```")

    return "\n".join(blocks)


def _agent_a_prompt(user_prompt: str, files_csv: str) -> str:
    ctx = _build_context(files_csv)
    return f"{ctx}\n\nTASK:\n{user_prompt}\n\nOUTPUT: git-style unified diff ONLY."


def _agent_b_prompt(user_prompt: str, files_csv: str, bad_patch: str, err: str) -> str:
    ctx = _build_context(files_csv)
    return (
        f"{ctx}\n\nTASK:\n{user_prompt}\n\n"
        f"BAD_PATCH:\n{bad_patch}\n\n"
        f"VALIDATION_ERROR:\n{err}\n\n"
        "Fix the patch to pass `git apply --check`.\n"
        "Return git-style unified diff ONLY. No commentary."
    )


def _run_job(job_id: str) -> None:
    with LOCK:
        job = JOBS[job_id]
        job.status = "running"
        JOBS[job_id] = job

    contract = _read_contract()

    system_a = (
        "You are Agent A (Patch Proposer).\n"
        f"{contract}\n"
        "Return PATCH ONLY.\n"
    )
    system_b = (
        "You are Agent B (Patch Fixer).\n"
        f"{contract}\n"
        "Return PATCH ONLY.\n"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        with LOCK:
            job = JOBS[job_id]
            job.attempt = attempt
            JOBS[job_id] = job

        try:
            # Agent A proposes
            user_a = _agent_a_prompt(job.prompt, job.files)
            raw = _call_llm(system=system_a, user=user_a)
            patch = _ensure_git_headers(raw)

            err = _git_apply_check(patch)
            if err is None:
                with LOCK:
                    job = JOBS[job_id]
                    job.patch = patch
                    job.last_error = ""
                    job.status = "needs_review"
                    JOBS[job_id] = job
                return

            # Agent B tries to repair
            user_b = _agent_b_prompt(job.prompt, job.files, patch, err)
            raw2 = _call_llm(system=system_b, user=user_b)
            patch2 = _ensure_git_headers(raw2)

            err2 = _git_apply_check(patch2)
            if err2 is None:
                with LOCK:
                    job = JOBS[job_id]
                    job.patch = patch2
                    job.last_error = ""
                    job.status = "needs_review"
                    JOBS[job_id] = job
                return

            with LOCK:
                job = JOBS[job_id]
                job.last_error = err2
                job.patch = patch2
                JOBS[job_id] = job

        except Exception as e:
            with LOCK:
                job = JOBS[job_id]
                job.last_error = str(e)
                JOBS[job_id] = job

        time.sleep(0.5)

    with LOCK:
        job = JOBS[job_id]
        job.status = "failed"
        JOBS[job_id] = job


app = FastAPI()

# Serve UI
app.mount("/static", StaticFiles(directory=str(REPO_ROOT / "tools/local_claude_ui/web/static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    html = (REPO_ROOT / "tools/local_claude_ui/web/templates/index.html").read_text(encoding="utf-8")
    return html


@app.get("/api/jobs")
def list_jobs():
    with LOCK:
        return {"jobs": [asdict(j) for j in JOBS.values()]}


@app.post("/api/jobs")
def create_job(payload: dict):
    prompt = (payload.get("prompt") or "").strip()
    files = (payload.get("files") or "").strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    if not files:
        raise HTTPException(status_code=400, detail="files is required (comma-separated)")

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        prompt=prompt,
        files=files,
        status="queued",
        attempt=0,
        last_error="",
        patch="",
    )
    with LOCK:
        JOBS[job_id] = job

    t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    t.start()

    return {"id": job_id}


@app.post("/api/jobs/{job_id}/apply")
def apply_job(job_id: str):
    with LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="job not found")
        job = JOBS[job_id]

    if job.status != "needs_review":
        raise HTTPException(status_code=400, detail=f"job not ready (status={job.status})")

    err = _git_apply(job.patch)
    if err is not None:
        with LOCK:
            job = JOBS[job_id]
            job.status = "failed"
            job.last_error = err
            JOBS[job_id] = job
        raise HTTPException(status_code=400, detail=err)

    with LOCK:
        job = JOBS[job_id]
        job.status = "applied"
        JOBS[job_id] = job

    return {"ok": True}


@app.post("/api/jobs/{job_id}/reject")
def reject_job(job_id: str):
    with LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="job not found")
        job = JOBS[job_id]
        job.status = "rejected"
        JOBS[job_id] = job
    return {"ok": True}
