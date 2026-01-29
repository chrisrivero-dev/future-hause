import json
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path("config/future_hause.yaml")
STATE_PATH = Path("engine/state.json")
LOG_PATH = Path("engine/log.json")


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


def run():
    write_state("collecting")
    log_event("Future Hause run started")

    # Stub: no collection yet
    log_event("No collectors enabled in v0.1")

    write_state("done")
    log_event("Future Hause run completed")


if __name__ == "__main__":
    run()
