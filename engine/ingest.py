"""
Future Hause — Ingestion Layer (Skeleton)

This file defines the ingestion interface for raw intel sources.
It validates input structure but does NOT process or store data.

No side effects. No persistence. Blocking by default.
"""

from typing import Dict, List, Optional
from datetime import datetime


# Supported source types (authoritative)
VALID_SOURCE_TYPES = {
    "reddit",
    "notes",
    "external",
    "freshdesk",
    "manual",
}

# Supported projects (authoritative)
VALID_PROJECTS = {
    "futurehub",
    "freshdesk-ai",
    "help-nearby",
    "other",
}


def validate_intel(payload: Dict) -> Dict:
    """
    Validate raw intel payload structure.

    Does NOT ingest, store, or process data.
    Returns validation result only.

    Required fields:
    - source_type: One of VALID_SOURCE_TYPES
    - project: One of VALID_PROJECTS
    - content: Non-empty string
    - timestamp: ISO-8601 string (optional, defaults to now)
    """

    errors = []

    # Check source_type
    source_type = payload.get("source_type")
    if not source_type:
        errors.append("Missing required field: source_type")
    elif source_type not in VALID_SOURCE_TYPES:
        errors.append(f"Invalid source_type: {source_type}")

    # Check project
    project = payload.get("project")
    if not project:
        errors.append("Missing required field: project")
    elif project not in VALID_PROJECTS:
        errors.append(f"Invalid project: {project}")

    # Check content
    content = payload.get("content")
    if not content:
        errors.append("Missing required field: content")
    elif not isinstance(content, str) or len(content.strip()) == 0:
        errors.append("Content must be a non-empty string")

    # Check timestamp (optional)
    timestamp = payload.get("timestamp")
    if timestamp:
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            errors.append(f"Invalid timestamp format: {timestamp}")

    if errors:
        return {
            "status": "invalid",
            "errors": errors,
        }

    return {
        "status": "valid",
        "errors": [],
    }


def ingest(payload: Dict) -> Dict:
    """
    Ingestion entry point.

    Responsibilities:
    - Validate payload structure
    - Return validation status
    - Block actual ingestion (not yet enabled)

    This function does NOT:
    - Write to disk
    - Emit events
    - Call agents
    - Modify state

    Ingestion is blocked by default.
    """

    validation = validate_intel(payload)

    if validation["status"] != "valid":
        return {
            "status": "rejected",
            "reason": "Validation failed",
            "errors": validation["errors"],
        }

    # Ingestion is blocked until explicitly enabled
    return {
        "status": "blocked",
        "reason": "Ingestion not yet enabled",
        "validated_payload": {
            "source_type": payload.get("source_type"),
            "project": payload.get("project"),
            "content_length": len(payload.get("content", "")),
            "has_timestamp": "timestamp" in payload,
        },
    }


def list_sources() -> List[str]:
    """Return list of valid source types."""
    return sorted(VALID_SOURCE_TYPES)


def list_projects() -> List[str]:
    """Return list of valid projects."""
    return sorted(VALID_PROJECTS)
