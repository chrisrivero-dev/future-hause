"""
Signal Extraction Layer

Transforms perception.inputs (raw ingestion objects)
into perception.signals (structured intelligence).
"""

import uuid
from datetime import datetime
from typing import Dict, List

from engine.state_manager import load_state, save_state


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def classify_content(content: str) -> str:
    """
    Simple deterministic classifier.
    Replace or extend with LLM later.
    """
    text = content.lower()

    if "error" in text or "not working" in text:
        return "issue"
    if "how do i" in text or "help" in text:
        return "support_question"
    if "update" in text or "release" in text:
        return "announcement"

    return "discussion"


def summarize_content(content: str) -> str:
    """
    Simple deterministic summary.
    Replace with LLM call later.
    """
    return content[:200]


def create_signal_from_input(input_obj: Dict) -> Dict:
    """
    Transform a single ingestion object into a signal.
    """

    summary = summarize_content(input_obj["content"])
    category = classify_content(input_obj["content"])

    return {
        "id": str(uuid.uuid4()),
        "source_input_id": input_obj["id"],
        "source": input_obj["source"],
        "summary": summary,
        "category": category,
        "confidence": 0.6,  # static for now
        "created_at": utc_now_iso(),
    }


def run_signal_extraction() -> List[Dict]:
    """
    Process all inputs that do not yet have signals.
    """

    state = load_state()

    inputs = state["perception"]["inputs"]
    signals = state["perception"]["signals"]

    existing_input_ids = {s["source_input_id"] for s in signals}

    new_signals = []

    for input_obj in inputs:
        if input_obj["id"] not in existing_input_ids:
            signal = create_signal_from_input(input_obj)
            new_signals.append(signal)

    state["perception"]["signals"].extend(new_signals)
    save_state(state)

    return new_signals
