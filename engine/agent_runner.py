"""
Future Hause — Agent Runner (Skeleton)

This file is a safe agent gatekeeper.
It accepts events and determines routing, but does NOT execute agents.

No side effects. No agent imports. Blocking by default.
"""

from typing import Dict


def dispatch(event: Dict):
    """
    Central agent gatekeeper.

    Responsibilities:
    - Receive system or human events
    - Validate event structure
    - Determine which agent *could* run
    - Block execution by default

    This file must remain side-effect free.
    """

    event_type = event.get("event")

    if not event_type:
        raise ValueError("Missing event type")

    ROUTES = {
        "EVT_INTEL_INGESTED": "DraftAgent",
        "EVT_DRAFT_REQUESTED": "DraftAgent",
        "EVT_DOC_REVIEW_REQUESTED": "DocAgent",
        "EVT_CODE_REVIEW_REQUESTED": "RefactorAgent",
        "EVT_DEPLOY_COMPLETE": "LogReviewAgent",
        "EVT_LOG_WINDOW_READY": "LogReviewAgent",
        "EVT_ACTION_COMPLETED": "OpsLedgerAgent",
        "EVT_PROJECT_SELECTED": "ProjectFocusAgent",
    }

    agent = ROUTES.get(event_type)

    if not agent:
        return {
            "status": "ignored",
            "reason": "No agent registered for event",
        }

    return {
        "status": "blocked",
        "agent": agent,
        "reason": "Agent execution not yet enabled",
    }
