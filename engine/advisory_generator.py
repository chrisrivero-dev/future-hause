"""
Advisory Generator for Project Promotion

Generates advisories from newly promoted projects.
No scoring, no confidence - deterministic pass/fail only.
"""

from datetime import datetime, timezone
import uuid


def generate_advisories(state: dict) -> list:
    """
    Generate advisories from promoted projects.

    For each project in state_mutations.projects:
    - Create an advisory suggesting KB review
    - Deduplicate by source_signal_id

    Args:
        state: Current cognition state

    Returns:
        List of newly created advisory objects
    """
    projects = state.get("state_mutations", {}).get("projects", [])
    advisories = state.get("advisories", {"open": [], "resolved": [], "dismissed": []})

    if isinstance(advisories, list):
        advisories = {"open": advisories, "resolved": [], "dismissed": []}

    existing_source_ids = set()
    for list_name in ["open", "resolved", "dismissed"]:
        for adv in advisories.get(list_name, []):
            source_id = adv.get("source_signal_id")
            if source_id:
                existing_source_ids.add(source_id)

    new_advisories = []

    for project in projects:
        source_signal_id = project.get("source_signal_id")

        if source_signal_id in existing_source_ids:
            continue

        advisory = {
            "id": str(uuid.uuid4()),
            "project_id": project.get("id"),
            "source_signal_id": source_signal_id,
            "type": "intel_alert",
            "title": project.get("summary") or project.get("title") or "New Project",
            "recommendation": "Review and determine if KB update is required.",
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        new_advisories.append(advisory)
        existing_source_ids.add(source_signal_id)

    return new_advisories
