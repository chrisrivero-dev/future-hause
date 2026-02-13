import uuid
import json
from datetime import datetime

import requests

from engine.state_manager import load_state, save_state


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3"  # Change if desired


PROMPT_TEMPLATE = """
You are a strict classification engine.

Classify the following content into structured JSON.

Allowed categories:
- announcement
- discussion
- bug
- confusion
- praise

Respond ONLY in valid JSON with this structure:

{
  "category": "...",
  "summary": "...",
  "confidence": 0.0
}

Content:
\"\"\"
{content}
\"\"\"
"""


def call_llm(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception:
        # Hard fallback if Ollama fails
        return ""


def classify_with_llm(content: str):
    prompt = PROMPT_TEMPLATE.format(content=content)

    raw_response = call_llm(prompt)

    try:
        parsed = json.loads(raw_response)
        return {
            "category": parsed.get("category", "discussion"),
            "summary": parsed.get("summary", content[:120]),
            "confidence": float(parsed.get("confidence", 0.5)),
        }
    except Exception:
        # Fail safe fallback
        return {
            "category": "discussion",
            "summary": content[:120],
            "confidence": 0.5,
        }


def run_signal_extraction():
    state = load_state()

    inputs = state["perception"]["inputs"]
    existing_signal_input_ids = {
        s["source_input_id"] for s in state["perception"]["signals"]
    }

    new_signals = []

    for input_obj in inputs:
        input_id = input_obj["id"]

        if input_id in existing_signal_input_ids:
            continue

        classification = classify_with_llm(input_obj["content"])

        signal = {
            "id": str(uuid.uuid4()),
            "source_input_id": input_id,
            "source": input_obj["source"],
            "summary": classification["summary"],
            "category": classification["category"],
            "confidence": classification["confidence"],
            "created_at": datetime.utcnow().isoformat(),
        }

        state["perception"]["signals"].append(signal)
        new_signals.append(signal)

    save_state(state)

    return new_signals
