"""
Advisory Engine for Project Focus Layer

Deterministically matches signals against active project metadata
and generates advisory suggestions. No LLM calls, no auto-execution.

Advisory types:
- signal_match: A signal matches project keywords or domain
- kb_opportunity: A KB candidate relates to the active project
- action_suggested: A recommended action based on signal patterns
"""

from datetime import datetime, timezone
import uuid

from engine.state_manager import (
    load_state,
    get_focus,
    set_advisories,
    get_advisories,
)


def _extract_project_keywords(project: dict) -> set[str]:
    """
    Extract searchable keywords from project metadata.
    Deterministic extraction from title, summary, and status.
    """
    keywords = set()

    title = project.get("title", "") or project.get("name", "")
    summary = project.get("summary", "") or project.get("description", "")

    for text in [title, summary]:
        if text:
            words = text.lower().split()
            keywords.update(w.strip(".,!?:;") for w in words if len(w) > 3)

    return keywords


def _signal_matches_project(signal: dict, project_keywords: set[str]) -> bool:
    """
    Deterministic match: does signal content overlap with project keywords?
    Returns True if there's keyword overlap.
    """
    signal_text = f"{signal.get('title', '')} {signal.get('content', '')}".lower()
    signal_words = set(signal_text.split())

    overlap = project_keywords & signal_words
    return len(overlap) >= 1


def _generate_advisory_from_signal(signal: dict, project: dict) -> dict:
    """
    Generate an advisory suggestion from a matching signal.
    """
    return {
        "id": f"adv-{uuid.uuid4().hex[:8]}",
        "type": "signal_match",
        "source_signal_id": signal.get("id"),
        "project_id": project.get("id"),
        "title": f"Signal relates to: {project.get('title') or project.get('name', 'Project')}",
        "summary": f"Signal '{signal.get('title', 'Untitled')}' may be relevant to your active project.",
        "suggested_action": "Review signal and determine if action is needed.",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _generate_advisory_from_kb(kb_candidate: dict, project: dict) -> dict:
    """
    Generate an advisory suggestion from a KB opportunity.
    """
    return {
        "id": f"adv-{uuid.uuid4().hex[:8]}",
        "type": "kb_opportunity",
        "source_kb_id": kb_candidate.get("id"),
        "project_id": project.get("id"),
        "title": f"KB opportunity for: {project.get('title') or project.get('name', 'Project')}",
        "summary": f"KB candidate '{kb_candidate.get('title', 'Untitled')}' may support your project.",
        "suggested_action": "Consider drafting KB content to address this gap.",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run_advisory_engine() -> dict:
    """
    Run the advisory engine to generate suggestions.

    Process:
    1. Check if an active project exists
    2. Load signals and KB candidates
    3. Match against project metadata (deterministic keyword matching)
    4. Generate advisory suggestions
    5. Store in state.advisories

    Returns:
        dict with advisory generation results
    """
    state = load_state()
    focus = state.get("focus", {})
    active_project_id = focus.get("active_project_id")

    # No active project = no advisories generated
    if not active_project_id:
        return {
            "status": "skipped",
            "reason": "no_active_project",
            "advisories_generated": 0,
        }

    # Find the active project
    projects = state.get("state_mutations", {}).get("projects", [])
    active_project = None
    for project in projects:
        if project.get("id") == active_project_id:
            active_project = project
            break

    if not active_project:
        return {
            "status": "skipped",
            "reason": "active_project_not_found",
            "advisories_generated": 0,
        }

    # Extract project keywords for matching
    project_keywords = _extract_project_keywords(active_project)

    if not project_keywords:
        return {
            "status": "skipped",
            "reason": "no_project_keywords",
            "advisories_generated": 0,
        }

    # Get existing advisories to prevent duplicates
    existing_advisories = state.get("advisories", [])
    existing_signal_ids = {
        a.get("source_signal_id")
        for a in existing_advisories
        if a.get("source_signal_id")
    }
    existing_kb_ids = {
        a.get("source_kb_id")
        for a in existing_advisories
        if a.get("source_kb_id")
    }

    new_advisories = []

    # Match signals against project
    signals = state.get("perception", {}).get("signals", [])
    for signal in signals:
        signal_id = signal.get("id")
        if signal_id in existing_signal_ids:
            continue

        if _signal_matches_project(signal, project_keywords):
            advisory = _generate_advisory_from_signal(signal, active_project)
            new_advisories.append(advisory)
            existing_signal_ids.add(signal_id)

    # Match KB candidates against project
    kb_candidates = state.get("proposals", {}).get("kb_candidates", [])
    for kb_candidate in kb_candidates:
        kb_id = kb_candidate.get("id")
        if kb_id in existing_kb_ids:
            continue

        kb_text = f"{kb_candidate.get('title', '')} {kb_candidate.get('summary', '')}".lower()
        kb_words = set(kb_text.split())

        if project_keywords & kb_words:
            advisory = _generate_advisory_from_kb(kb_candidate, active_project)
            new_advisories.append(advisory)
            existing_kb_ids.add(kb_id)

    # Append new advisories to existing (preserve old ones)
    all_advisories = existing_advisories + new_advisories
    set_advisories(all_advisories)

    return {
        "status": "completed",
        "advisories_generated": len(new_advisories),
        "total_advisories": len(all_advisories),
        "active_project_id": active_project_id,
    }
