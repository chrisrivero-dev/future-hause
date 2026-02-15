"""
Signal Extraction for Future Hause

Reads raw collected data and converts it into perception signals.
Writes signals into cognition_state.json via state_manager.

Deterministic. No LLM calls. No external network calls.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from engine.state_manager import load_state, save_state


RAW_REDDIT_PATH = Path("data/raw/reddit_stub.json")


def _load_raw_reddit() -> list:
    """Load raw reddit data if available."""
    if not RAW_REDDIT_PATH.exists():
        return []
    try:
        with open(RAW_REDDIT_PATH, "r") as f:
            data = json.load(f)
        return data.get("posts", [])
    except (json.JSONDecodeError, KeyError):
        return []


def _post_to_signal(post: dict) -> dict:
    """Convert a raw reddit post into a perception signal."""
    return {
        "id": str(uuid.uuid4()),
        "source": "reddit",
        "category": post.get("category", "discussion"),
        "title": post.get("title", "Untitled"),
        "content": post.get("content", post.get("body", "")),
        "confidence": post.get("confidence", 0.5),
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def _generate_stub_signals() -> list:
    """
    Generate deterministic stub signals for local development.
    Used when no raw data exists yet (v0.1 scope).
    """
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": str(uuid.uuid4()),
            "source": "reddit",
            "category": "discussion",
            "title": "Apollo BTC setup questions",
            "content": "Users asking about optimal PSU and cooling configuration for Apollo BTC miners.",
            "confidence": 0.7,
            "detected_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "source": "reddit",
            "category": "discussion",
            "title": "Firmware update issues reported",
            "content": "Multiple users reporting difficulty applying latest firmware update on Apollo II.",
            "confidence": 0.8,
            "detected_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "source": "reddit",
            "category": "announcement",
            "title": "FutureBit announces new mining pool partnership",
            "content": "Official announcement of partnership with mining pool for optimized hashrate distribution.",
            "confidence": 0.9,
            "detected_at": now,
        },
    ]


def run_signal_extraction() -> dict:
    """
    Extract signals from raw collected data into perception.signals.

    1. Reads raw data from collectors (reddit stub)
    2. Converts raw posts into perception signals
    3. Falls back to stub signals if no raw data exists
    4. Appends new signals to cognition_state.json
    5. Returns count of signals created

    Returns:
        dict with signals_created count and the new signal list.
    """
    state = load_state()

    # Collect existing signal IDs to prevent duplicates
    existing_ids = {s.get("id") for s in state["perception"]["signals"]}

    # Try to extract from raw data first
    raw_posts = _load_raw_reddit()

    if raw_posts:
        new_signals = [_post_to_signal(p) for p in raw_posts]
    else:
        new_signals = _generate_stub_signals()

    # Filter out any signals that already exist (by ID)
    new_signals = [s for s in new_signals if s["id"] not in existing_ids]

    # Append to perception signals
    state["perception"]["signals"].extend(new_signals)

    # Update meta timestamp
    state["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()

    save_state(state)

    return {
        "signals_created": len(new_signals),
        "signals": new_signals,
    }
