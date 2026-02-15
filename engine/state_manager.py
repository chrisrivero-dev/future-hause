"""State manager for cognition_state.json"""
import json
from pathlib import Path

STATE_PATH = Path("state/cognition_state.json")

# Full baseline schema for initialization
BASELINE_SCHEMA = {
    "meta": {"version": "1.0", "last_updated": None},
    "perception": {"inputs": [], "signals": [], "sources": []},
    "interpretation": {"summaries": [], "classifications": [], "confidence_scores": []},
    "proposals": {"kb_candidates": [], "project_candidates": [], "action_candidates": []},
    "decisions": {"approved": [], "rejected": [], "modified": []},
    "state_mutations": {"projects": [], "kb": [], "action_log": []},
    "memory_links": {"related_sessions": [], "related_entities": [], "embedding_ids": []},
    "system_health": {"errors": [], "latency_ms": None, "model_used": None},
    "focus": {"active_project_id": None},
    "advisories": [],
}


def load_state():
    """Load cognition state from disk."""
    if not STATE_PATH.exists():
        # Initialize with full baseline schema
        save_state(BASELINE_SCHEMA)
        return BASELINE_SCHEMA.copy()
    with open(STATE_PATH, "r") as f:
        state = json.load(f)
    # Validate schema integrity
    if "state_mutations" not in state or "action_log" not in state.get("state_mutations", {}):
        raise ValueError("cognition_state.json missing required schema fields (state_mutations.action_log)")
    return state


def save_state(state):
    """Save cognition state to disk."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ─────────────────────────────────────────────
# Action Log Functions
# ─────────────────────────────────────────────

def append_action(action_entry):
    """Append an action entry to state_mutations.action_log."""
    state = load_state()
    state["state_mutations"]["action_log"].append(action_entry)
    save_state(state)


def get_action_log():
    """Get action log from state_mutations.action_log."""
    state = load_state()
    return state["state_mutations"]["action_log"]


# ─────────────────────────────────────────────
# Intel Functions
# ─────────────────────────────────────────────

def get_intel_signals():
    """Get intel signals from perception.signals."""
    state = load_state()
    return state["perception"]["signals"]


def replace_intel_signals(signals):
    """Replace intel signals in perception.signals."""
    state = load_state()
    state["perception"]["signals"] = signals
    save_state(state)


# ─────────────────────────────────────────────
# Focus Functions
# ─────────────────────────────────────────────

def get_focus():
    """Get current focus state."""
    state = load_state()
    return state.get("focus", {"active_project_id": None})


def set_active_project(project_id: str | None):
    """Set the active project ID."""
    state = load_state()
    if "focus" not in state:
        state["focus"] = {"active_project_id": None}
    state["focus"]["active_project_id"] = project_id
    save_state(state)
    return state["focus"]


# ─────────────────────────────────────────────
# Advisory Functions
# ─────────────────────────────────────────────

def get_advisories():
    """Get all advisories."""
    state = load_state()
    return state.get("advisories", [])


def set_advisories(advisories: list):
    """Replace all advisories."""
    state = load_state()
    state["advisories"] = advisories
    save_state(state)


def dismiss_advisory(advisory_id: str):
    """Mark an advisory as dismissed."""
    state = load_state()
    advisories = state.get("advisories", [])
    for advisory in advisories:
        if advisory.get("id") == advisory_id:
            advisory["status"] = "dismissed"
    state["advisories"] = advisories
    save_state(state)
    return advisories
