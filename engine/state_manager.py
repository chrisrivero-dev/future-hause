"""State manager for cognition_state.json"""
import json
from pathlib import Path

STATE_PATH = Path(__file__).parent.parent / "state" / "cognition_state.json"


def load_state():
    """Load cognition state from disk."""
    if not STATE_PATH.exists():
        return {"perception": {"signals": []}}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state):
    """Save cognition state to disk."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def get_intel_signals():
    """Get intel signals from perception.signals."""
    state = load_state()
    return state["perception"]["signals"]


def replace_intel_signals(signals):
    """Replace intel signals in perception.signals."""
    state = load_state()
    state["perception"]["signals"] = signals
    save_state(state)
