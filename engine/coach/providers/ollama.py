import requests
from datetime import datetime, timezone

from engine.system_identity import SYSTEM_IDENTITY, INTENT_CONTRACT, build_state_context

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2:3b-instruct-q4_1"
TIMEOUT = 60


def run_coach(draft_id: str, draft_text: str) -> dict:
    state_context = build_state_context()

    prompt = (
        SYSTEM_IDENTITY + "\n\n"
        + INTENT_CONTRACT + "\n\n"
        + state_context + "\n\n"
        "You are a writing coach.\n\n"
        "Your job:\n"
        "- Suggest improvements, missing context, or clarity issues.\n"
        "- If the draft is thin or incomplete, infer likely intent and suggest how to expand it.\n"
        "- Be constructive and practical.\n"
        "- Do NOT ask questions unless absolutely necessary.\n\n"
        "If no improvements are needed, say exactly:\n"
        "\"Looks good as-is.\"\n\n"
        f"DRAFT:\n{draft_text}"
    )


    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()

    text = r.json().get("response", "").strip()
    if not text:
        text = "Looks good as-is."

    return {
        "draft_id": draft_id,
        "coach_response": text,
        "model": "ollama",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
