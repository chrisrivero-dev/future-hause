import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .resolve_animation import resolve_animation


# ============================
# Paths
# ============================

CONFIG_PATH = Path("config/future_hause.yaml")
STATE_PATH = Path("engine/state.json")
LOG_PATH = Path("engine/log.json")
RAW_REDDIT_PATH = Path("data/raw/reddit_stub.json")


# ============================
# Utilities
# ============================

def write_state(payload: dict):
    """
    Write engine state to engine/state.json
    """
    if not isinstance(payload, dict):
        raise TypeError("write_state expects a dict payload")

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(payload, indent=2)
    )



def log_event(message: str):
    """
    Append an event to engine/log.json
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    if LOG_PATH.exists():
        logs = json.loads(LOG_PATH.read_text())

    logs.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "message": message
    })


    LOG_PATH.write_text(
        json.dumps(logs, indent=2)
    )


def load_config() -> dict:
    """
    Load config/future_hause.yaml
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("Missing config/future_hause.yaml")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================
# Collectors (v0.1 stubs)
# ============================

def run_reddit_collector_stub():
    """
    Stub collector for Reddit.
    Writes placeholder raw data.
    No network calls.
    """
    RAW_REDDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    stub_payload = {
        "source": "reddit",
        "type": "stub",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "posts": []
    }


    RAW_REDDIT_PATH.write_text(
        json.dumps(stub_payload, indent=2)
    )

    log_event("Reddit raw data stub written to data/raw/reddit_stub.json")


# ============================
# Engine Runner
# ============================

def run():
    # --- Initial state ---
    current_state = "collecting"

    log_event("Future Hause run started")

    # --- Resolve animation ---
    current_animation = resolve_animation(
        "engine_status",
        current_state
    )


    write_state({
        "state": current_state,
        "current_animation": current_animation,
        "updated_at": datetime.now(timezone.utc).isoformat()
    })

    # --- Load config ---
    config = load_config()
    fh_config = config.get("future_hause", {})
    scope = fh_config.get("scope", {})
    collect_scope = scope.get("collect", {})

    log_event(f"Loaded config version: {fh_config.get('version', 'unknown')}")
    log_event(f"Collection scope: {collect_scope}")

    # --- Run collectors ---
    if collect_scope.get("reddit", False):
        run_reddit_collector_stub()
    else:
        log_event("Reddit collector disabled by config")

    # --- v0.1 scope ends here ---
    log_event("No analysis or drafting executed (v0.1 scope)")

       # --- Final state ---
    write_state({
        "state": "done",
        "current_animation": resolve_animation(
            "engine_status",
            "done"
        ),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })

    log_event("Future Hause run completed")


# ============================
# Entrypoint
# ============================

if __name__ == "__main__":
    run()
