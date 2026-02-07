from typing import Dict
from config import config


def dispatch(event: Dict):
    """
    Central agent gatekeeper.

    Responsibilities:
    - Receive system or human events
    - Validate event structure
    - Determine which agent *could* run
    - Enforce runtime mode policy
    - Signal whether an agent is allowed or blocked

    No side effects. No execution. Policy only.
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

    ALLOWED_MODES = {
        "EVT_DRAFT_REQUESTED": {"LOCAL", "WORK_REMOTE", "DEMO"},
        "EVT_DOC_REVIEW_REQUESTED": {"WORK_REMOTE", "DEMO"},
        "EVT_CODE_REVIEW_REQUESTED": {"LOCAL", "WORK_REMOTE"},
    }

    agent = ROUTES.get(event_type)

    if not agent:
        return {
            "status": "ignored",
            "reason": "No agent registered for event",
        }

    allowed_modes = ALLOWED_MODES.get(event_type)
    current_mode = config.runtimeMode

    # Enforce runtime mode restrictions first
    if allowed_modes is not None and current_mode not in allowed_modes:
        return {
            "status": "blocked",
            "agent": agent,
            "reason": f"Event not permitted in runtime mode {current_mode}",
        }

    # DraftAgent is explicitly allowed for autonomous execution (draft-only)
    if agent == "DraftAgent":
        return {
            "status": "allowed",
            "agent": agent,
            "reason": "DraftAgent allowed for autonomous draft execution",
        }

    return {
        "status": "blocked",
        "agent": agent,
        "reason": "Agent execution not yet enabled",
    }
