import json
from datetime import datetime
from pathlib import Path
from engine.resolve_animation import resolve_animation


import yaml


CONFIG_PATH = Path("config/future_hause.yaml")
STATE_PATH = Path("engine/state.json")
LOG_PATH = Path("engine/log.json")
RAW_REDDIT_PATH = Path("data/raw/reddit_stub.json")


def write_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({
        "state": state,
        "updated_at": datetime.utcnow().isoformat()
    }, indent=2))


def log_event(message):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    if LOG_PATH.exists():
        logs = json.loads(LOG_PATH.read_text())

    logs.append({
        "time": datetime.utcnow().isoformat(),
        "message": message
    })

    LOG_PATH.write_text(json.dumps(logs, indent=2))


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("Missing config/future_hause.yaml")

    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def run_reddit_collector_stub():
    """
    Stub collector for Reddit.
    Writes a placeholder raw data file.
    No network calls.
    """
    RAW_REDDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    stub_payload = {
        "source": "reddit",
        "type": "stub",
        "collected_at": datetime.utcnow().isoformat(),
        "posts": []
    }

    RAW_REDDIT_PATH.write_text(json.dumps(stub_payload, indent=2))
    log_event("Reddit raw data stub written to data/raw/reddit_stub.json")


def run():
   current_state = "collecting"

current_animation = resolve_animation(
    panel_name="engine_status",
    engine_state=current_state
)

write_state({
    "state": current_state,
    "current_animation": current_animation
})

log_event("Future Hause run started")

config = load_config()
fh_config = config.get("future_hause", {})
scope = fh_config.get("scope", {})
collect_scope = scope.get("collect", {})


    log_event(f"Loaded config version: {fh_config.get('version', 'unknown')}")
    log_event(f"Collection scope: {collect_scope}")

    if collect_scope.get("reddit", False):
        run_reddit_collector_stub()
    else:
        log_event("Reddit collector disabled by config")

    log_event("No analysis or drafting executed (v0.1 scope)")

    write_state("done")
    log_event("Future Hause run completed")


if __name__ == "__main__":
    run()
