import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import requests


LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lmstudio")
DEFAULT_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-14b-instruct-mlx")


def run(cmd: List[str], cwd: Optional[str] = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout


def repo_root() -> str:
    return run(["git", "rev-parse", "--show-toplevel"]).strip()


def git_status(root: str) -> str:
    return run(["git", "status", "--porcelain=v1"], cwd=root).strip()


def git_ls_files(root: str) -> List[str]:
    out = run(["git", "ls-files"], cwd=root)
    return [line.strip() for line in out.splitlines() if line.strip()]


def read_text(path: Path, max_chars: int) -> str:
    data = path.read_text(encoding="utf-8", errors="replace")
    if len(data) <= max_chars:
        return data
    # Keep head+tail to preserve definitions and endings
    head = data[: max_chars // 2]
    tail = data[-max_chars // 2 :]
    return head + "\n\n# ... (truncated) ...\n\n" + tail


def load_contract(root: str) -> str:
    p = Path(root) / "AI_CONTRACT.md"
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace").strip()
    # Fallback contract (still strict)
    return (
        "You are a coding assistant under strict constraints.\n"
        "Rules:\n"
        "1) Output unified diff patch only.\n"
        "2) Modify ONLY provided files.\n"
        "3) Minimal diff; no refactors unless requested.\n"
        "4) Fully-indented valid code.\n"
    ).strip()


def build_prompt(root: str, task: str, files: List[str], max_file_chars: int) -> str:
    root_path = Path(root)
    blocks = []

    blocks.append("## TASK\n" + task.strip())

    status = git_status(root)
    blocks.append("## GIT_STATUS_PORCELAIN\n" + (status if status else "(clean)"))

    blocks.append("## FILES_PROVIDED\n" + "\n".join(files) if files else "## FILES_PROVIDED\n(none)")

    for rel in files:
        fp = root_path / rel
        if not fp.exists():
            blocks.append(f"## FILE: {rel}\n# ERROR: file not found\n")
            continue
        if fp.is_dir():
            blocks.append(f"## FILE: {rel}\n# ERROR: is a directory\n")
            continue
        content = read_text(fp, max_chars=max_file_chars)
        blocks.append(f"## FILE: {rel}\n```text\n{content}\n```")

    blocks.append(
        "## OUTPUT_REQUIREMENTS\n"
        "- Return ONLY a unified diff patch.\n"
        "- Include --- and +++ headers.\n"
        "- Do not include explanations.\n"
        "- Do not modify files not provided.\n"
    )

    return "\n\n".join(blocks).strip()


def is_unified_diff(text: str) -> bool:
    t = text.lstrip()
    # Accept common unified diff / git diff formats
    return (
        t.startswith("diff --git ")
        or (("--- " in t) and ("+++ " in t) and ("@@ " in t))
        or (t.startswith("--- ") and "+++ " in t)
    )


def call_lmstudio(system: str, user: str, model: str) -> str:
    url = f"{LMSTUDIO_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {LMSTUDIO_API_KEY}"}
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=300)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def save_patch(root: str, patch_text: str, slug: str) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", slug)[:60].strip("-") or "patch"
    out_dir = Path(root) / ".local_assistant" / "patches"
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{ts}_{safe}.patch"
    p.write_text(patch_text, encoding="utf-8")
    return p


def git_apply_check(root: str, patch_path: Path) -> str:
    return run(["git", "apply", "--check", str(patch_path)], cwd=root)


def git_apply(root: str, patch_path: Path) -> str:
    return run(["git", "apply", "--whitespace=nowarn", str(patch_path)], cwd=root)


def main() -> int:
    ap = argparse.ArgumentParser(description="Local git-aware patch assistant (LM Studio).")
    ap.add_argument("task", help="What change to make (be specific + scoped).")
    ap.add_argument("--files", nargs="*", default=[], help="Repo-relative file paths to include.")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="LM Studio model id.")
    ap.add_argument("--max-file-chars", type=int, default=14000, help="Max chars per file to send.")
    ap.add_argument("--dry-run", action="store_true", help="Run git apply --check on the patch.")
    ap.add_argument("--apply", action="store_true", help="Apply patch via git apply.")
    ap.add_argument("--show", action="store_true", help="Print patch to stdout.")
    args = ap.parse_args()

    root = repo_root()
    contract = load_contract(root)

    if not args.files:
        # Safe default: don't guess files. Force explicit scoping.
        print("ERROR: No --files provided. This assistant is safe-by-default.", file=sys.stderr)
        print("Provide target files, e.g.: --files app.py intent_classifier.py", file=sys.stderr)
        return 2

    prompt = build_prompt(root, args.task, args.files, args.max_file_chars)

    system = (
        "You are a senior software engineer generating a unified diff patch.\n\n"
        f"{contract}\n\n"
        "ABSOLUTE REQUIREMENT: Output unified diff patch ONLY. No explanations.\n"
        "If you cannot comply, output an empty diff.\n"
    )

    patch = call_lmstudio(system=system, user=prompt, model=args.model).strip()

    # ---- CLEAN MARKDOWN FENCES ----
    if patch.startswith("```"):
        lines = patch.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        patch = "\n".join(lines).strip()

    # ---- NORMALIZE DIFF FORMAT ----
    lines = patch.splitlines()

    if lines:
        # Case 1: Starts with --- engine/... (no a/ prefix)
        if lines[0].startswith("--- ") and not lines[0].startswith("--- a/"):
            file_path = lines[0].replace("--- ", "").strip()
            lines.insert(0, f"diff --git a/{file_path} b/{file_path}")
            lines[1] = f"--- a/{file_path}"
            if len(lines) > 2 and lines[2].startswith("+++ "):
                lines[2] = f"+++ b/{file_path}"

        # Case 2: Starts with --- a/... but missing diff --git header
        elif lines[0].startswith("--- a/") and not lines[0].startswith("diff --git"):
            file_path = lines[0].replace("--- a/", "").strip()
            lines.insert(0, f"diff --git a/{file_path} b/{file_path}")

    patch = "\n".join(lines).strip()

        # ---- VALIDATE DIFF ----
    if not is_unified_diff(patch):
        print("ERROR: Model did not return a unified diff patch.", file=sys.stderr)
        return 3

    # Reject multiple hunks (too risky for v1)
    if patch.count("@@") > 1:
        print("ERROR: Multiple patch hunks detected. Rejecting for safety.", file=sys.stderr)
        return 3


    patch_path = save_patch(root, patch, slug=args.task)

    if args.show:
        print(patch)

    if args.dry_run:
        try:
            git_apply_check(root, patch_path)
            print(f"OK: git apply --check passed for {patch_path}")
        except Exception as e:
            print(f"ERROR: git apply --check failed for {patch_path}\n{e}", file=sys.stderr)
            return 4

    if args.apply:
        try:
            git_apply(root, patch_path)
            print(f"APPLIED: {patch_path}")
        except Exception as e:
            print(f"ERROR: git apply failed for {patch_path}\n{e}", file=sys.stderr)
            return 5
    else:
        print(f"SAVED PATCH: {patch_path}")
        print("Tip: run with --dry-run first, then --apply if it looks correct.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
