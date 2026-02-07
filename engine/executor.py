"""
Future Hause — Execution Layer

Consumes routing decisions from agent_runner.
Does NOT auto-execute agents unless explicitly enabled.

This is the only file allowed to cross from "policy"
into "capability".
"""

from typing import Dict
from engine.agent_runner import dispatch


# Feature flag — execution is OFF by default
EXECUTION_ENABLED = False


def execute(event: Dict) -> Dict:
    """
    Consume a routing decision and determine next steps.

    This function:
    - Calls the agent runner (policy)
    - Interprets the decision
    - Blocks or allows execution explicitly

    No agent execution occurs unless EXECUTION_ENABLED = True.
    """

    decision = dispatch(event)

    status = decision.get("status")

    # Pass-through ignored events
    if status == "ignored":
        return {
            "status": "ignored",
            "reason": decision.get("reason"),
        }

    # Explicitly blocked by policy
    if status == "blocked":
        return {
            "status": "blocked",
            "agent": decision.get("agent"),
            "reason": decision.get("reason"),
        }

    # Future-proofing: allowed but execution disabled
    if status == "allowed" and not EXECUTION_ENABLED:
        return {
            "status": "blocked",
            "agent": decision.get("agent"),
            "reason": "Execution layer disabled",
        }

    # Hard safety net — should never happen
    return {
        "status": "error",
        "reason": "Unhandled execution state",
        "decision": decision,
    }
