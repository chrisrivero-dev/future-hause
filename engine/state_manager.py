"""
State manager for cognition_state.json
"""

import json
from pathlib import Path
from datetime import datetime

STATE_PATH = Path("state/cognition_state.json")


# ─────────────────────────────────────────────
# Core Load / Save
# ─────────────────────────────────────────────

def load_state():
    if not STATE_PATH.exists():
        raise FileNotFoundError("Cognition state not initialized.")

    with open(STATE_PATH, "r") as f:
        state = json.load(f)

    # Ensure required top-level keys exist
    state.setdefault("focus", {"active_project_id": None})
    state.setdefault("kb_drafts", {
        "scaffolded": [],
        "active": [],
        "archived": []
    })
    state.setdefault("advisories", {
        "open": [],
        "resolved": [],
        "dismissed": []
    })
    state.setdefault("meta", {})

    return state


def save_state(state):
    state.setdefault("meta", {})
    state["meta"]["last_updated"] = datetime.utcnow().isoformat()

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ─────────────────────────────────────────────
# Focus Layer
# ─────────────────────────────────────────────

def get_active_project_id():
    state = load_state()
    return state.get("focus", {}).get("active_project_id")


def set_active_project_id(project_id):
    state = load_state()
    state.setdefault("focus", {})
    state["focus"]["active_project_id"] = project_id
    save_state(state)


# ─────────────────────────────────────────────
# KB Draft Layer
# ─────────────────────────────────────────────

def get_kb_drafts():
    state = load_state()
    return state.get("kb_drafts", {})


def append_kb_scaffold(scaffold):
    state = load_state()
    state.setdefault("kb_drafts", {}).setdefault("scaffolded", [])
    state["kb_drafts"]["scaffolded"].append(scaffold)
    save_state(state)


# ─────────────────────────────────────────────
# Ingestion Layer
# ─────────────────────────────────────────────

def append_input(input_object):
    state = load_state()
    state.setdefault("perception", {}).setdefault("inputs", [])
    state["perception"]["inputs"].append(input_object)
    save_state(state)


def get_inputs():
    state = load_state()
    return state.get("perception", {}).get("inputs", [])


# ─────────────────────────────────────────────
# Signal Layer
# ─────────────────────────────────────────────

def get_intel_signals():
    state = load_state()
    return state.get("perception", {}).get("signals", [])


def replace_intel_signals(signals):
    state = load_state()
    state.setdefault("perception", {})
    state["perception"]["signals"] = signals
    save_state(state)


# ─────────────────────────────────────────────
# Proposal Layer
# ─────────────────────────────────────────────

def get_kb_candidates():
    state = load_state()
    return state.get("proposals", {}).get("kb_candidates", [])


def get_projects():
    state = load_state()
    return state.get("state_mutations", {}).get("projects", [])


# ─────────────────────────────────────────────
# Action Log
# ─────────────────────────────────────────────

def append_action(action_entry):
    state = load_state()
    state.setdefault("state_mutations", {}).setdefault("action_log", [])
    state["state_mutations"]["action_log"].append(action_entry)
    save_state(state)


def get_action_log():
    state = load_state()
    return state.get("state_mutations", {}).get("action_log", [])
