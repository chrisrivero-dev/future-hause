"""
Advisory Generator
Creates deterministic advisories from promoted projects.
"""

import uuid
from datetime import datetime


def generate_advisories(state):
    """
    Generates advisories from newly promoted projects.
    Deduplicates by source_signal_id.
    """

    advisories = state.setdefault("advisories", {
        "open": [],
        "resolved": [],
        "dismissed": []
    })

    existing_source_ids = {
        a["source_signal_id"]
        for bucket in advisories.values()
        for a in bucket
    }

    new_advisories = []

    for project in state.get("state_mutations", {}).get("projects", []):

        source_id = project.get("source_signal_id")

        if not source_id:
            continue

        if source_id in existing_source_ids:
            continue

        advisory = {
            "id": str(uuid.uuid4()),
            "project_id": project.get("id"),
            "source_signal_id": source_id,
            "type": "intel_alert",
            "title": project.get("summary", "New Intel Detected"),
            "recommendation": "Review and determine if KB update is required.",
            "status": "open",
            "priority": "normal",
            "created_at": datetime.utcnow().isoformat()
        }

        advisories["open"].append(advisory)
        new_advisories.append(advisory)

    return new_advisories
