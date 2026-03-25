"""State manager for cognition_state.json"""
import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("state/cognition_state.json")

# Freshness threshold in hours (configurable)
FRESHNESS_THRESHOLD_HOURS = 24

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
    "advisories": {"open": [], "resolved": [], "dismissed": []},
}


def _deep_repair(state, schema):
    """
    Recursively repair state to match schema structure.

    - Backfills missing keys at ANY depth
    - Fixes type mismatches (dict → dict, list → list)
    - Does NOT overwrite valid existing values

    Returns:
        tuple: (repaired_state, was_modified)
    """
    modified = False

    if not isinstance(schema, dict):
        # Base case: schema is not a dict, return as-is
        return state, False

    # Ensure state is a dict if schema expects dict
    if not isinstance(state, dict):
        return _deep_copy_schema(schema), True

    for key, default_value in schema.items():
        if key not in state:
            # Key missing: backfill from schema
            state[key] = _deep_copy_schema(default_value)
            modified = True
        elif isinstance(default_value, dict):
            # Schema expects dict
            if not isinstance(state[key], dict):
                # Type mismatch: replace with schema default
                state[key] = _deep_copy_schema(default_value)
                modified = True
            else:
                # Recurse into nested dict
                state[key], nested_modified = _deep_repair(state[key], default_value)
                modified = modified or nested_modified
        elif isinstance(default_value, list):
            # Schema expects list
            if not isinstance(state[key], list):
                # Type mismatch: replace with deep copy of schema default
                state[key] = _deep_copy_schema(default_value)
                modified = True
            # Lists: don't recurse into items, just ensure it's a list

    return state, modified


def _deep_copy_schema(value):
    """
    Deep copy a schema value to avoid reference issues.
    """
    if isinstance(value, dict):
        return {k: _deep_copy_schema(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_deep_copy_schema(item) for item in value]
    else:
        return value


def load_state():
    """Load cognition state from disk. Auto-heals missing fields recursively."""
    if not STATE_PATH.exists():
        # Initialize with full baseline schema
        initial_state = _deep_copy_schema(BASELINE_SCHEMA)
        _save_state_raw(initial_state)
        return initial_state

    with open(STATE_PATH, "r") as f:
        state = json.load(f)

    # Deep recursive repair: fix missing keys and type mismatches at any depth
    state, repaired = _deep_repair(state, BASELINE_SCHEMA)

    # Persist repaired state to disk
    if repaired:
        _save_state_raw(state)

    return state


def _save_state_raw(state):
    """Save cognition state to disk. Internal only — use save_state_validated() instead."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def save_state_validated(state):
    """
    Save cognition state to disk after validating lifecycle invariants.

    Use this for final state saves where invariants must hold.
    Raises LifecycleViolation if validation fails.
    """
    # Import here to avoid circular dependency
    from engine.lifecycle_guard import validate_before_save

    validate_before_save(state)
    _save_state_raw(state)


# ─────────────────────────────────────────────
# Action Log Functions
# ─────────────────────────────────────────────

def append_action(action_entry):
    """Append an action entry to state_mutations.action_log."""
    state = load_state()
    state["state_mutations"]["action_log"].append(action_entry)
    save_state_validated(state)


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
    save_state_validated(state)


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
    save_state_validated(state)
    return state["focus"]


# ─────────────────────────────────────────────
# Advisory Functions
# ─────────────────────────────────────────────

def get_advisories():
    """Get all advisories in structured format."""
    state = load_state()
    advisories = state.get("advisories", {"open": [], "resolved": [], "dismissed": []})
    if isinstance(advisories, list):
        return {"open": advisories, "resolved": [], "dismissed": []}
    return advisories


def append_open_advisories(new_advisories: list):
    """Append new advisories to open list."""
    state = load_state()
    if "advisories" not in state:
        state["advisories"] = {"open": [], "resolved": [], "dismissed": []}
    if isinstance(state["advisories"], list):
        state["advisories"] = {"open": state["advisories"], "resolved": [], "dismissed": []}
    state["advisories"]["open"].extend(new_advisories)
    save_state_validated(state)
    return state["advisories"]


def update_advisory_status(advisory_id: str, new_status: str):
    """Move advisory between open/resolved/dismissed."""
    state = load_state()
    advisories = state.get("advisories", {"open": [], "resolved": [], "dismissed": []})
    if isinstance(advisories, list):
        advisories = {"open": advisories, "resolved": [], "dismissed": []}

    target_advisory = None
    source_list = None

    for list_name in ["open", "resolved", "dismissed"]:
        for advisory in advisories.get(list_name, []):
            if advisory.get("id") == advisory_id:
                target_advisory = advisory
                source_list = list_name
                break
        if target_advisory:
            break

    if not target_advisory:
        return None

    advisories[source_list].remove(target_advisory)
    target_advisory["status"] = new_status
    advisories[new_status].append(target_advisory)

    state["advisories"] = advisories
    save_state_validated(state)
    return target_advisory


# ─────────────────────────────────────────────
# KB Candidate Functions
# ─────────────────────────────────────────────

def update_kb_candidate_status(candidate_id: str, new_status: str) -> dict | None:
    """Update KB candidate status (pending, queued, dismissed, drafted)."""
    state = load_state()
    candidates = state.get("proposals", {}).get("kb_candidates", [])

    for candidate in candidates:
        if candidate.get("id") == candidate_id:
            candidate["status"] = new_status
            save_state_validated(state)
            return candidate

    return None


def get_kb_candidates() -> list:
    """Get all KB candidates."""
    state = load_state()
    return state.get("proposals", {}).get("kb_candidates", [])


# ─────────────────────────────────────────────
# User Project Functions
# ─────────────────────────────────────────────

def create_user_project(project_data: dict) -> dict:
    """Create a new user-defined project."""
    import uuid
    from datetime import datetime, timezone

    state = load_state()
    now = datetime.now(timezone.utc).isoformat()

    project = {
        "id": str(uuid.uuid4()),
        "title": project_data.get("title", "Untitled Project"),
        "summary": project_data.get("summary", ""),
        "status": project_data.get("status", "active"),
        "priority": project_data.get("priority", "medium"),
        "created_at": now,
        "updated_at": now,
        "source": "user",
        "timestamp": now,
        "freshness": "current",
        "confidence": 1.0,
        "user_defined": True,
    }

    state["state_mutations"]["projects"].append(project)
    save_state_validated(state)
    return project


def update_user_project(project_id: str, updates: dict) -> dict | None:
    """Update an existing project."""
    from datetime import datetime, timezone

    state = load_state()
    projects = state.get("state_mutations", {}).get("projects", [])

    for project in projects:
        if project.get("id") == project_id:
            # Only update allowed fields
            for key in ["title", "summary", "status", "priority"]:
                if key in updates:
                    project[key] = updates[key]
            project["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_state_validated(state)
            return project

    return None


def delete_user_project(project_id: str) -> bool:
    """Delete a user-defined project."""
    state = load_state()
    projects = state.get("state_mutations", {}).get("projects", [])

    for i, project in enumerate(projects):
        if project.get("id") == project_id:
            # Only allow deletion of user-defined projects
            if project.get("user_defined"):
                projects.pop(i)
                save_state_validated(state)
                return True
            return False

    return False


# ─────────────────────────────────────────────
# Advisory Investigate Function
# ─────────────────────────────────────────────

def set_advisory_investigating(advisory_id: str) -> dict | None:
    """Mark an advisory as being investigated."""
    from datetime import datetime, timezone

    state = load_state()
    advisories = state.get("advisories", {"open": [], "resolved": [], "dismissed": []})
    if isinstance(advisories, list):
        advisories = {"open": advisories, "resolved": [], "dismissed": []}

    for advisory in advisories.get("open", []):
        if advisory.get("id") == advisory_id:
            advisory["investigating"] = True
            advisory["investigation_started_at"] = datetime.now(timezone.utc).isoformat()
            state["advisories"] = advisories
            save_state_validated(state)
            return advisory

    return None


# ─────────────────────────────────────────────
# Work Log Functions
# ─────────────────────────────────────────────

def get_work_log() -> list:
    """
    Get work log entries filtered by actionable work types.
    Auto-populated from: KB drafts, recommendations, advisories.
    Returns normalized entries: {type, timestamp, reference_id, details}
    """
    state = load_state()
    action_log = state.get("state_mutations", {}).get("action_log", [])

    work_type_map = {
        "kb_draft_created": "kb_created",
        "kb_draft_saved": "kb_created",
        "recommendation_applied": "recommendation_applied",
        "advisory_resolved": "advisory_resolved",
        "advisory_dismissed": "advisory_resolved",
        "advisory_investigating": "advisory_resolved",
    }

    entries = []
    for entry in action_log:
        action_type = entry.get("action_type")
        if action_type not in work_type_map:
            continue
        metadata = entry.get("metadata", {})
        reference_id = (
            metadata.get("candidate_id")
            or metadata.get("advisory_id")
            or entry.get("id", "unknown")
        )
        entries.append({
            "type": work_type_map[action_type],
            "timestamp": entry.get("timestamp", "unknown"),
            "reference_id": reference_id,
            "details": entry.get("rationale", ""),
        })
    return entries


# ─────────────────────────────────────────────
# Freshness Validation
# ─────────────────────────────────────────────

def compute_freshness(timestamp: str | None) -> str:
    """
    Compute freshness status based on timestamp and threshold.
    Returns: 'current', 'stale', or 'unknown'
    """
    if not timestamp:
        return "unknown"

    try:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_hours = (now - ts).total_seconds() / 3600

        if age_hours > FRESHNESS_THRESHOLD_HOURS:
            return "stale"
        return "current"
    except (ValueError, TypeError):
        return "unknown"


def validate_freshness(items: list, timestamp_field: str = "timestamp") -> list:
    """
    Validate and update freshness for a list of items.
    Mutates items in place, setting freshness='stale' if over threshold.
    """
    for item in items:
        ts = item.get(timestamp_field) or item.get("created_at")
        item["freshness"] = compute_freshness(ts)
    return items


# ─────────────────────────────────────────────
# Project Cleanup (User-Only Projects)
# ─────────────────────────────────────────────

def get_user_projects_only() -> list:
    """
    Get only user-created projects. Filters out any analysis/legacy projects.
    Single source of truth: user_defined=True projects only.
    """
    state = load_state()
    projects = state.get("state_mutations", {}).get("projects", [])
    return [p for p in projects if p.get("user_defined") is True]


def cleanup_legacy_projects() -> int:
    """
    Remove all non-user-defined projects from state.
    Returns count of removed projects.
    """
    state = load_state()
    projects = state.get("state_mutations", {}).get("projects", [])
    user_projects = [p for p in projects if p.get("user_defined") is True]
    removed = len(projects) - len(user_projects)

    if removed > 0:
        state["state_mutations"]["projects"] = user_projects
        save_state_validated(state)

    return removed
