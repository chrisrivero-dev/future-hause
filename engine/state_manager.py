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
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def append_action(action_entry):
    state = load_state()
    state["state_mutations"]["action_log"].append(action_entry)
    save_state(state)

def get_action_log():
    state = load_state()
    return state["state_mutations"]["action_log"]
