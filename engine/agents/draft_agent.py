"""
Future Hause — DraftAgent (Stub)

This agent performs draft-only work.
No state mutation. No memory writes. No side effects.

This is a placeholder implementation.
"""
from typing import Dict


def run(event: Dict) -> Dict:
    """
    Execute a draft task.

    This agent produces a draft and exposes a payload
    that MAY be reviewed if explicitly requested.
    """

    draft_output = {
        "text": "DraftAgent stub output — replace with real draft later"
    }

    return {
        "status": "draft_completed",
        "agent": "DraftAgent",
        "draft": draft_output,
        "review_available": True,
        "review_payload": {
            "agent_name": "DraftAgent",
            "original_event": event,
            "draft_output": draft_output["text"],
        },
    }
