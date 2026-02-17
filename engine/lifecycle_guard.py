"""
Lifecycle Guard for Future Hause

Enforces invariants for the deterministic lifecycle system:
1. Three-Step Promotion Invariant: Every promoted project must have
   proposal_id, decision_id, and triggered_by in action_log
2. No state mutation without action_log entry
3. No advisory generated without source_signal_id

This module provides enforcement only. No new features.
"""


class LifecycleViolation(Exception):
    """Raised when a lifecycle invariant is violated."""
    pass


class ThreeStepPromotionViolation(LifecycleViolation):
    """Raised when a promoted project lacks required audit trail."""
    pass


class MutationWithoutActionLogViolation(LifecycleViolation):
    """Raised when a state mutation has no corresponding action_log entry."""
    pass


class AdvisoryWithoutSourceViolation(LifecycleViolation):
    """Raised when an advisory lacks source_signal_id."""
    pass


def validate_state_integrity(state: dict) -> None:
    """
    Validate all lifecycle invariants on the given state.

    Raises:
        ThreeStepPromotionViolation: If a promoted project lacks required fields
        MutationWithoutActionLogViolation: If mutation has no action_log entry
        AdvisoryWithoutSourceViolation: If advisory lacks source_signal_id

    Args:
        state: The cognition state dict to validate
    """
    _validate_three_step_promotion(state)
    _validate_mutations_have_action_log(state)
    _validate_advisories_have_source(state)


def _validate_three_step_promotion(state: dict) -> None:
    """
    Validate Three-Step Promotion Invariant.

    Every project in state_mutations.projects must have:
    - proposal_id: Reference to original proposal
    - decision_id: Reference to approval decision
    - triggered_by: Found in corresponding action_log entry
    """
    projects = state.get("state_mutations", {}).get("projects", [])
    action_log = state.get("state_mutations", {}).get("action_log", [])

    # Build index of action_log entries by mutation_id
    action_log_by_mutation = {}
    for entry in action_log:
        mutation_id = entry.get("mutation_id")
        if mutation_id:
            action_log_by_mutation[mutation_id] = entry

    for project in projects:
        project_id = project.get("id", "<unknown>")

        # Check proposal_id
        if not project.get("proposal_id"):
            raise ThreeStepPromotionViolation(
                f"Project '{project_id}' missing proposal_id. "
                "Every promoted project must reference its originating proposal."
            )

        # Check decision_id
        if not project.get("decision_id"):
            raise ThreeStepPromotionViolation(
                f"Project '{project_id}' missing decision_id. "
                "Every promoted project must reference its approval decision."
            )

        # Check triggered_by via action_log
        action_entry = action_log_by_mutation.get(project_id)
        if action_entry is None:
            raise ThreeStepPromotionViolation(
                f"Project '{project_id}' has no action_log entry. "
                "Every promoted project must have a recorded promotion action."
            )

        if not action_entry.get("triggered_by"):
            raise ThreeStepPromotionViolation(
                f"Project '{project_id}' action_log entry missing triggered_by. "
                "Every promotion must record who triggered it."
            )


def _validate_mutations_have_action_log(state: dict) -> None:
    """
    Validate that every state mutation has a corresponding action_log entry.

    Checks both kb and projects mutations.
    """
    kb_mutations = state.get("state_mutations", {}).get("kb", [])
    project_mutations = state.get("state_mutations", {}).get("projects", [])
    action_log = state.get("state_mutations", {}).get("action_log", [])

    # Build set of mutation_ids in action_log
    logged_mutation_ids = set()
    for entry in action_log:
        mutation_id = entry.get("mutation_id")
        if mutation_id:
            logged_mutation_ids.add(mutation_id)

    # Check kb mutations
    for mutation in kb_mutations:
        mutation_id = mutation.get("id")
        if mutation_id and mutation_id not in logged_mutation_ids:
            raise MutationWithoutActionLogViolation(
                f"KB mutation '{mutation_id}' has no action_log entry. "
                "Every state mutation must be recorded in action_log."
            )

    # Check project mutations
    for mutation in project_mutations:
        mutation_id = mutation.get("id")
        if mutation_id and mutation_id not in logged_mutation_ids:
            raise MutationWithoutActionLogViolation(
                f"Project mutation '{mutation_id}' has no action_log entry. "
                "Every state mutation must be recorded in action_log."
            )


def _validate_advisories_have_source(state: dict) -> None:
    """
    Validate that every advisory has a source_signal_id.

    Checks all advisory lists: open, resolved, dismissed.
    """
    advisories = state.get("advisories", {})

    # Handle legacy list format
    if isinstance(advisories, list):
        advisories = {"open": advisories, "resolved": [], "dismissed": []}

    for list_name in ["open", "resolved", "dismissed"]:
        for advisory in advisories.get(list_name, []):
            advisory_id = advisory.get("id", "<unknown>")

            if not advisory.get("source_signal_id"):
                raise AdvisoryWithoutSourceViolation(
                    f"Advisory '{advisory_id}' in '{list_name}' list missing source_signal_id. "
                    "Every advisory must reference its source signal."
                )


def validate_after_promotion(state: dict) -> None:
    """
    Run validation after promotion execution.

    This is the integration point called after run_promotion() or promote_single().

    Raises:
        LifecycleViolation subclass if any invariant is violated
    """
    validate_state_integrity(state)


def validate_before_save(state: dict) -> None:
    """
    Run validation before saving state.

    This is the integration point called before save_state().

    Raises:
        LifecycleViolation subclass if any invariant is violated
    """
    validate_state_integrity(state)
