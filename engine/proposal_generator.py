"""
Proposal Generator for Future Hause

Converts perception signals into proposal candidates:
- discussion, support_issue, firmware_issue, kb_candidate signals → kb_candidates
- announcement, product_news signals → project_candidates

Product announcements matching patterns like "Apollo III", "is here", "launch"
generate project candidates with titles like "Apollo III support preparation".

Deterministic. No LLM calls. Uses state_manager for persistence.
"""

import re

import uuid
from datetime import datetime, timezone
from engine.state_manager import load_state, save_state_validated


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
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "source_signal_id": signal.get("id"),
        "title": signal.get("title", "Untitled Discussion"),
        "summary": signal.get("content", signal.get("summary", "")),
        "created_at": now.isoformat(),
        # DATA TRUST LAYER FIELDS
        "source": signal.get("source", "unknown"),
        "timestamp": now.isoformat(),
        "freshness": "current",
        "confidence": 0.7,
        "status": "pending",
    }


def _extract_product_name(title: str, content: str) -> str | None:
    """Extract product name from announcement text if present."""
    text = f"{title} {content}"

    # Look for Apollo product mentions
    # Order alternatives from longest to shortest to match "III" before "II"
    apollo_match = re.search(r"Apollo\s*(BTC|III|II|IV|[2-4]|\d+)?", text, re.IGNORECASE)
    if apollo_match:
        version = apollo_match.group(1) or ""
        if version:
            return f"Apollo {version.upper()}"
        return "Apollo"

    # Look for FutureBit product mentions
    futurebit_match = re.search(r"FutureBit\s+(\w+)", text, re.IGNORECASE)
    if futurebit_match:
        return f"FutureBit {futurebit_match.group(1)}"

    return None


def _create_project_candidate(signal: dict) -> dict:
    """
    Create a Project candidate proposal from an announcement signal.

    For product announcements, generates project name like:
    "Apollo III support preparation"
    """
    title = signal.get("title", "Untitled Announcement")
    content = signal.get("content", signal.get("summary", ""))

    # Try to extract product name for better project title
    product_name = _extract_product_name(title, content)
    if product_name:
        project_title = f"{product_name} support preparation"
    else:
        project_title = title

    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "source_signal_id": signal.get("id"),
        "title": project_title,
        "summary": content,
        "priority": "medium",
        "status": "candidate",
        "created_at": now.isoformat(),
        # DATA TRUST LAYER FIELDS
        "source": signal.get("source", "unknown"),
        "timestamp": now.isoformat(),
        "freshness": "current",
        "confidence": 0.7,
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
        elif category in ("announcement", "product_news"):
            # Product announcements and news generate project candidates
            candidate = _create_project_candidate(signal)
            state["proposals"]["project_candidates"].append(candidate)
            project_generated += 1
        elif category in ("support_issue", "firmware_issue", "kb_candidate"):
            # Support-related signals generate KB candidates
            candidate = _create_kb_candidate(signal)
            state["proposals"]["kb_candidates"].append(candidate)
            kb_generated += 1
        else:
            skipped_unknown_category += 1

    # Persist updated state
    save_state_validated(state)

    return {
        "status": "complete",
        "kb_candidates_generated": kb_generated,
        "project_candidates_generated": project_generated,
        "skipped_duplicate": skipped_duplicate,
        "skipped_unknown_category": skipped_unknown_category,
        "total_signals_processed": len(signals),
    }
