# engine/snapshot_manager.py
"""
Snapshot Manager for Future Hause

Creates immutable, timestamped snapshots of the cognition_state.json
so intelligence can be regenerated, audited, compared, and rolled back.

Snapshots live under: state/snapshots/
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from engine.state_manager import load_state


SNAPSHOT_DIR = Path("state/snapshots")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_snapshot(trigger: str, extra: dict | None = None) -> dict:
    """
    Create an immutable snapshot of the current cognition state.

    Args:
        trigger: short label for what caused the snapshot (e.g., "signal_extraction", "proposal_generation")
        extra: optional metadata to store alongside the snapshot

    Returns:
        dict: snapshot metadata including snapshot_id and file path
    """
    state = load_state()

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_id = str(uuid.uuid4())
    created_at = _utc_now_iso()
    safe_trigger = (trigger or "unknown").strip().lower().replace(" ", "_")

    filename = f"{created_at.replace(':', '').replace('.', '')}_{safe_trigger}_{snapshot_id[:8]}.json"
    snapshot_path = SNAPSHOT_DIR / filename

    snapshot = {
        "snapshot_id": snapshot_id,
        "created_at": created_at,
        "trigger": safe_trigger,
        "meta": {
            "state_version": state.get("meta", {}).get("version", "unknown"),
            "last_updated": state.get("meta", {}).get("last_updated"),
        },
        "counts": {
            "inputs": len(state.get("perception", {}).get("inputs", [])),
            "signals": len(state.get("perception", {}).get("signals", [])),
            "kb_candidates": len(state.get("proposals", {}).get("kb_candidates", [])),
            "project_candidates": len(state.get("proposals", {}).get("project_candidates", [])),
            "approved": len(state.get("decisions", {}).get("approved", [])),
            "rejected": len(state.get("decisions", {}).get("rejected", [])),
            "projects": len(state.get("state_mutations", {}).get("projects", [])),
            "kb": len(state.get("state_mutations", {}).get("kb", [])),
            "action_log": len(state.get("state_mutations", {}).get("action_log", [])),
        },
        "extra": extra or {},
        "state": state,  # full copy (immutable snapshot)
    }

    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    return {
        "status": "ok",
        "snapshot_id": snapshot_id,
        "trigger": safe_trigger,
        "created_at": created_at,
        "path": str(snapshot_path),
        "counts": snapshot["counts"],
    }
