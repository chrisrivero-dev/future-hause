"""
Proposal Generator for Future Hause

Converts perception signals into proposal candidates:
- discussion signals → kb_candidates
- announcement signals → project_candidates

Deterministic. No LLM calls. Uses state_manager for persistence.
"""

import uuid
from datetime import datetime, timezone
from engine.state_manager import load_state, save_state


def _get_existing_proposal_source_ids(state: dict) -> set:
    """Extract all source_signal_ids from existing proposals."""
    source_ids = set()

    for candidate in state["proposals"]["kb_candidates"]:
        if "source_signal_id" in candidate:
            source_ids.add(candidate["source_signal_id"])

    for candidate in state["proposals"]["project_candidates"]:
        if "source_signal_id" in candidate:
            source_ids.add(candidate["source_signal_id"])

    return source_ids


def _create_kb_candidate(signal: dict) -> dict:
    """Create a KB candidate proposal from a discussion signal."""
    return {
        "id": str(uuid.uuid4()),
        "source_signal_id": signal.get("id"),
        "title": signal.get("title", "Untitled Discussion"),
        "summary": signal.get("content", signal.get("summary", "")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _create_project_candidate(signal: dict) -> dict:
    """Create a Project candidate proposal from an announcement signal."""
    return {
        "id": str(uuid.uuid4()),
        "source_signal_id": signal.get("id"),
        "title": signal.get("title", "Untitled Announcement"),
        "summary": signal.get("content", signal.get("summary", "")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run_proposal_generation() -> dict:
    """
    Generate proposals from perception signals.

    Reads all signals from perception.signals.
    Skips signals that have already been proposed (duplicate prevention).
    Creates KB candidates for 'discussion' category signals.
    Creates Project candidates for 'announcement' category signals.

    Returns:
        dict with counts of generated proposals and any skipped signals.
    """
    state = load_state()

    signals = state["perception"]["signals"]
    existing_source_ids = _get_existing_proposal_source_ids(state)

    kb_generated = 0
    project_generated = 0
    skipped_duplicate = 0
    skipped_unknown_category = 0

    for signal in signals:
        signal_id = signal.get("id")

        # Skip if already proposed
        if signal_id and signal_id in existing_source_ids:
            skipped_duplicate += 1
            continue

        category = signal.get("category", "").lower()

        if category == "discussion":
            candidate = _create_kb_candidate(signal)
            state["proposals"]["kb_candidates"].append(candidate)
            kb_generated += 1
        elif category == "announcement":
            candidate = _create_project_candidate(signal)
            state["proposals"]["project_candidates"].append(candidate)
            project_generated += 1
        else:
            skipped_unknown_category += 1

    # Persist updated state
    save_state(state)

    return {
        "status": "complete",
        "kb_candidates_generated": kb_generated,
        "project_candidates_generated": project_generated,
        "skipped_duplicate": skipped_duplicate,
        "skipped_unknown_category": skipped_unknown_category,
        "total_signals_processed": len(signals),
    }
