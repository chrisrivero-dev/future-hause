import requests
from datetime import datetime, timezone

from engine.system_identity import SYSTEM_IDENTITY

# ──────────────────────────────────────────────
# Ollama configuration
# ──────────────────────────────────────────────

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2:3b-instruct-q4_1"
TIMEOUT = 60


def run_coach_mode(draft_id: str, draft_text: str) -> dict:
    """
    Generate internal support assets from a verified user pain point.

    This is NOT a reviewer.
    This is NOT a rewriter.
    This is a support-asset generator.
    """

    prompt = f"""
{SYSTEM_IDENTITY}

You are a senior customer support architect.

INPUT:
You will be given a VERIFIED USER PAIN POINT based on real user reports.

TASK:
Generate INTERNAL SUPPORT ASSETS for this pain point.

You MUST produce the following sections, in this order:

### KB_ARTICLE
- Clear title
- Step-by-step troubleshooting
- Escalation guidance
- Warnings or edge cases if relevant

### CANNED_RESPONSE
- Empathetic, concise reply suitable for email or ticket
- Link placeholder to KB article
- Ask at most TWO diagnostic questions

### TAGS
- 3–6 concise, lowercase support tags

### NOTES
- Internal-only observations
- When to escalate
- When reflashing or advanced recovery is justified

RULES:
- Do NOT critique the input.
- Do NOT rewrite the pain point.
- Do NOT ask questions.
- Do NOT apologize.
- Be decisive and practical.
- Assume the reader is a support agent, not a customer.

PAIN POINT:
{draft_text}
""".strip()

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    coach_text = response.json().get("response", "").strip()
    if not coach_text:
        coach_text = "No support assets generated."

    return {
        "draft_id": draft_id,
        "coach_response": coach_text,
        "model": "ollama",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
