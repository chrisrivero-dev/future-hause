"""State manager for cognition_state.json"""

import json
from pathlib import Path
from datetime import datetime

STATE_PATH = Path("state/cognition_state.json")


def load_state():
    if not STATE_PATH.exists():
        raise FileNotFoundError("Cognition state not initialized.")
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state):
    state["meta"]["last_updated"] = datetime.utcnow().isoformat()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ─────────────────────────────────────────────
# Ingestion Layer
# ─────────────────────────────────────────────

def append_input(input_object):
    state = load_state()
    state["perception"]["inputs"].append(input_object)
    save_state(state)


def get_inputs():
    state = load_state()
    return state["perception"]["inputs"]


# ─────────────────────────────────────────────
# Signal Layer
# ─────────────────────────────────────────────

def get_intel_signals():
    state = load_state()
    return state["perception"]["signals"]


def replace_intel_signals(signals):
    state = load_state()
    state["perception"]["signals"] = signals
    save_state(state)


# ─────────────────────────────────────────────
# Proposal Layer
# ─────────────────────────────────────────────

def get_kb_candidates():
    state = load_state()
    return state["proposals"]["kb_candidates"]


def get_projects():
    state = load_state()
    return state["state_mutations"]["projects"]


# ─────────────────────────────────────────────
# Action Log
# ─────────────────────────────────────────────

def append_action(action_entry):
    state = load_state()
    state["state_mutations"]["action_log"].append(action_entry)
    save_state(state)


def get_action_log():
    state = load_state()
    return state["state_mutations"]["action_log"]
