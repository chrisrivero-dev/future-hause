"""
Promotion Engine for Future Hause

Controlled Promotion System that:
1. Promotes approved KB candidates → state_mutations.kb
2. Promotes approved project candidates → state_mutations.projects
3. Prevents double promotion
4. Records every promotion in action_log
5. Maintains audit trace: proposal_id → decision_id → mutation_id
6. Never auto-approves anything
7. Requires explicit human-triggered decision call

Deterministic. No LLM calls. No external dependencies.
"""

import uuid
from datetime import datetime, timezone
from typing import Literal
from engine.state_manager import load_state, save_state, save_state_validated
from engine.lifecycle_guard import validate_after_promotion


# ─────────────────────────────────────────────────────────────────────────────
# Type Definitions
# ─────────────────────────────────────────────────────────────────────────────

ProposalType = Literal["kb_candidate", "project_candidate"]
PromotionResult = dict  # Contains status, counts, and any errors


# ─────────────────────────────────────────────────────────────────────────────
# Decision Recording (Human-Triggered)
# ─────────────────────────────────────────────────────────────────────────────

def record_approval(
    proposal_id: str,
    proposal_type: ProposalType,
    approved_by: str,
    rationale: str | None = None,
) -> dict:
    """
    Record a human approval decision for a proposal.

    This function ONLY records the decision. It does NOT promote.
    Promotion requires a separate explicit call to run_promotion().

    Args:
        proposal_id: The ID of the proposal being approved
        proposal_type: Either "kb_candidate" or "project_candidate"
        approved_by: Human identifier who approved (required for audit)
        rationale: Optional reason for approval

    Returns:
        dict with decision_id and status

    Raises:
        ValueError: If proposal_id not found or already approved
    """
    state = load_state()

    # Validate proposal_type
    if proposal_type not in ("kb_candidate", "project_candidate"):
        raise ValueError(f"Invalid proposal_type: {proposal_type}. Must be 'kb_candidate' or 'project_candidate'")

    # Validate approved_by is provided
    if not approved_by or not approved_by.strip():
        raise ValueError("approved_by is required for audit trail")

    # Find the proposal
    proposal = _find_proposal(state, proposal_id, proposal_type)
    if proposal is None:
        raise ValueError(f"Proposal not found: {proposal_id} (type: {proposal_type})")

    # Check if already approved
    if _is_proposal_already_approved(state, proposal_id):
        raise ValueError(f"Proposal already approved: {proposal_id}")

    # Create decision record
    decision_id = str(uuid.uuid4())
    decision = {
        "id": decision_id,
        "proposal_id": proposal_id,
        "proposal_type": proposal_type,
        "approved_by": approved_by.strip(),
        "rationale": rationale.strip() if rationale else None,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "promoted": False,  # Tracks whether promotion has occurred
    }

    state["decisions"]["approved"].append(decision)
    save_state(state)

    return {
        "status": "recorded",
        "decision_id": decision_id,
        "proposal_id": proposal_id,
        "proposal_type": proposal_type,
    }


def record_rejection(
    proposal_id: str,
    proposal_type: ProposalType,
    rejected_by: str,
    rationale: str,
) -> dict:
    """
    Record a human rejection decision for a proposal.

    Args:
        proposal_id: The ID of the proposal being rejected
        proposal_type: Either "kb_candidate" or "project_candidate"
        rejected_by: Human identifier who rejected (required for audit)
        rationale: Reason for rejection (required)

    Returns:
        dict with decision_id and status

    Raises:
        ValueError: If proposal_id not found or already decided
    """
    state = load_state()

    # Validate proposal_type
    if proposal_type not in ("kb_candidate", "project_candidate"):
        raise ValueError(f"Invalid proposal_type: {proposal_type}")

    # Validate required fields
    if not rejected_by or not rejected_by.strip():
        raise ValueError("rejected_by is required for audit trail")
    if not rationale or not rationale.strip():
        raise ValueError("rationale is required for rejections")

    # Find the proposal
    proposal = _find_proposal(state, proposal_id, proposal_type)
    if proposal is None:
        raise ValueError(f"Proposal not found: {proposal_id} (type: {proposal_type})")

    # Check if already decided
    if _is_proposal_already_decided(state, proposal_id):
        raise ValueError(f"Proposal already has a decision: {proposal_id}")

    # Create rejection record
    decision_id = str(uuid.uuid4())
    decision = {
        "id": decision_id,
        "proposal_id": proposal_id,
        "proposal_type": proposal_type,
        "rejected_by": rejected_by.strip(),
        "rationale": rationale.strip(),
        "rejected_at": datetime.now(timezone.utc).isoformat(),
    }

    state["decisions"]["rejected"].append(decision)
    save_state(state)

    return {
        "status": "rejected",
        "decision_id": decision_id,
        "proposal_id": proposal_id,
        "proposal_type": proposal_type,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Promotion Execution (Human-Triggered)
# ─────────────────────────────────────────────────────────────────────────────

def run_promotion(triggered_by: str) -> PromotionResult:
    """
    Execute promotion of all approved-but-not-promoted proposals.

    This function MUST be explicitly called by a human trigger.
    It does NOT auto-execute on approval.

    Process:
    1. Find all approved decisions where promoted=False
    2. For each, look up the original proposal
    3. Create mutation in state_mutations.kb or state_mutations.projects
    4. Record promotion in action_log with full audit trail
    5. Mark decision as promoted=True

    Args:
        triggered_by: Human identifier who triggered promotion (required)

    Returns:
        dict with promotion counts and any errors

    Raises:
        ValueError: If triggered_by is not provided
    """
    if not triggered_by or not triggered_by.strip():
        raise ValueError("triggered_by is required - promotion must be human-triggered")

    state = load_state()

    kb_promoted = 0
    project_promoted = 0
    errors = []
    promotions = []

    # Process all un-promoted approvals
    for decision in state["decisions"]["approved"]:
        if decision.get("promoted", False):
            continue  # Skip already promoted

        decision_id = decision["id"]
        proposal_id = decision["proposal_id"]
        proposal_type = decision["proposal_type"]

        try:
            # Find the original proposal
            proposal = _find_proposal(state, proposal_id, proposal_type)
            if proposal is None:
                errors.append({
                    "decision_id": decision_id,
                    "proposal_id": proposal_id,
                    "error": "Proposal not found - may have been removed",
                })
                continue

            # Check for double-promotion via action_log
            if _is_already_promoted_in_action_log(state, proposal_id):
                errors.append({
                    "decision_id": decision_id,
                    "proposal_id": proposal_id,
                    "error": "Double-promotion prevented - already in action_log",
                })
                decision["promoted"] = True  # Mark to prevent future attempts
                continue

            # Create mutation
            mutation_id = str(uuid.uuid4())
            mutation = _create_mutation(proposal, decision, mutation_id)

            # Add to appropriate state_mutations bucket
            if proposal_type == "kb_candidate":
                state["state_mutations"]["kb"].append(mutation)
                kb_promoted += 1
            elif proposal_type == "project_candidate":
                state["state_mutations"]["projects"].append(mutation)
                project_promoted += 1

            # Record in action_log
            action_entry = _create_action_log_entry(
                proposal_id=proposal_id,
                decision_id=decision_id,
                mutation_id=mutation_id,
                proposal_type=proposal_type,
                triggered_by=triggered_by.strip(),
            )
            state["state_mutations"]["action_log"].append(action_entry)

            # Mark decision as promoted
            decision["promoted"] = True
            decision["promoted_at"] = datetime.now(timezone.utc).isoformat()
            decision["mutation_id"] = mutation_id

            promotions.append({
                "proposal_id": proposal_id,
                "decision_id": decision_id,
                "mutation_id": mutation_id,
                "type": proposal_type,
            })

        except Exception as e:
            errors.append({
                "decision_id": decision_id,
                "proposal_id": proposal_id,
                "error": str(e),
            })

    # Validate invariants before save, then persist
    save_state_validated(state)

    # Additional validation after promotion execution
    validate_after_promotion(state)

    return {
        "status": "complete",
        "triggered_by": triggered_by.strip(),
        "kb_promoted": kb_promoted,
        "project_promoted": project_promoted,
        "total_promoted": kb_promoted + project_promoted,
        "promotions": promotions,
        "errors": errors if errors else None,
    }


def promote_single(
    decision_id: str,
    triggered_by: str,
) -> dict:
    """
    Promote a single approved decision by its decision_id.

    Use this for fine-grained control over which approvals get promoted.

    Args:
        decision_id: The ID of the approval decision to promote
        triggered_by: Human identifier who triggered promotion (required)

    Returns:
        dict with mutation_id and status

    Raises:
        ValueError: If decision not found, not approved, or already promoted
    """
    if not triggered_by or not triggered_by.strip():
        raise ValueError("triggered_by is required - promotion must be human-triggered")

    state = load_state()

    # Find the decision
    decision = None
    for d in state["decisions"]["approved"]:
        if d["id"] == decision_id:
            decision = d
            break

    if decision is None:
        raise ValueError(f"Approved decision not found: {decision_id}")

    if decision.get("promoted", False):
        raise ValueError(f"Decision already promoted: {decision_id}")

    proposal_id = decision["proposal_id"]
    proposal_type = decision["proposal_type"]

    # Check action_log for double-promotion
    if _is_already_promoted_in_action_log(state, proposal_id):
        raise ValueError(f"Double-promotion prevented - proposal {proposal_id} already in action_log")

    # Find the proposal
    proposal = _find_proposal(state, proposal_id, proposal_type)
    if proposal is None:
        raise ValueError(f"Proposal not found: {proposal_id}")

    # Create mutation
    mutation_id = str(uuid.uuid4())
    mutation = _create_mutation(proposal, decision, mutation_id)

    # Add to appropriate bucket
    if proposal_type == "kb_candidate":
        state["state_mutations"]["kb"].append(mutation)
    elif proposal_type == "project_candidate":
        state["state_mutations"]["projects"].append(mutation)

    # Record in action_log
    action_entry = _create_action_log_entry(
        proposal_id=proposal_id,
        decision_id=decision_id,
        mutation_id=mutation_id,
        proposal_type=proposal_type,
        triggered_by=triggered_by.strip(),
    )
    state["state_mutations"]["action_log"].append(action_entry)

    # Mark decision as promoted
    decision["promoted"] = True
    decision["promoted_at"] = datetime.now(timezone.utc).isoformat()
    decision["mutation_id"] = mutation_id

    # Validate invariants before save, then persist
    save_state_validated(state)

    # Additional validation after promotion execution
    validate_after_promotion(state)

    return {
        "status": "promoted",
        "proposal_id": proposal_id,
        "decision_id": decision_id,
        "mutation_id": mutation_id,
        "proposal_type": proposal_type,
        "triggered_by": triggered_by.strip(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Query Functions (Read-Only)
# ─────────────────────────────────────────────────────────────────────────────

def get_pending_promotions() -> list[dict]:
    """
    Get all approved decisions that have not yet been promoted.

    Returns:
        List of decisions awaiting promotion
    """
    state = load_state()
    pending = []

    for decision in state["decisions"]["approved"]:
        if not decision.get("promoted", False):
            pending.append({
                "decision_id": decision["id"],
                "proposal_id": decision["proposal_id"],
                "proposal_type": decision["proposal_type"],
                "approved_by": decision["approved_by"],
                "approved_at": decision["approved_at"],
                "rationale": decision.get("rationale"),
            })

    return pending


def get_promotion_history() -> list[dict]:
    """
    Get all promotion records from the action_log.

    Returns:
        List of promotion action_log entries
    """
    state = load_state()
    promotions = []

    for action in state["state_mutations"]["action_log"]:
        if action.get("action_type") == "promotion":
            promotions.append(action)

    return promotions


def get_audit_trail(proposal_id: str) -> dict | None:
    """
    Get the full audit trail for a proposal: proposal → decision → mutation.

    Args:
        proposal_id: The ID of the proposal to trace

    Returns:
        dict with proposal, decision, and mutation details, or None if not found
    """
    state = load_state()

    # Find proposal
    proposal = None
    proposal_type = None

    for p in state["proposals"]["kb_candidates"]:
        if p.get("id") == proposal_id:
            proposal = p
            proposal_type = "kb_candidate"
            break

    if proposal is None:
        for p in state["proposals"]["project_candidates"]:
            if p.get("id") == proposal_id:
                proposal = p
                proposal_type = "project_candidate"
                break

    if proposal is None:
        return None

    # Find decision
    decision = None
    for d in state["decisions"]["approved"]:
        if d.get("proposal_id") == proposal_id:
            decision = d
            break

    if decision is None:
        for d in state["decisions"]["rejected"]:
            if d.get("proposal_id") == proposal_id:
                decision = d
                break

    # Find mutation (if promoted)
    mutation = None
    action_log_entry = None

    if decision and decision.get("promoted"):
        mutation_id = decision.get("mutation_id")

        # Search in kb mutations
        for m in state["state_mutations"]["kb"]:
            if m.get("id") == mutation_id:
                mutation = m
                break

        # Search in project mutations
        if mutation is None:
            for m in state["state_mutations"]["projects"]:
                if m.get("id") == mutation_id:
                    mutation = m
                    break

        # Find action_log entry
        for a in state["state_mutations"]["action_log"]:
            if a.get("mutation_id") == mutation_id:
                action_log_entry = a
                break

    return {
        "proposal_id": proposal_id,
        "proposal_type": proposal_type,
        "proposal": proposal,
        "decision": decision,
        "mutation": mutation,
        "action_log_entry": action_log_entry,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _find_proposal(state: dict, proposal_id: str, proposal_type: ProposalType) -> dict | None:
    """Find a proposal by ID and type."""
    if proposal_type == "kb_candidate":
        candidates = state["proposals"]["kb_candidates"]
    elif proposal_type == "project_candidate":
        candidates = state["proposals"]["project_candidates"]
    else:
        return None

    for candidate in candidates:
        if candidate.get("id") == proposal_id:
            return candidate

    return None


def _is_proposal_already_approved(state: dict, proposal_id: str) -> bool:
    """Check if proposal has already been approved."""
    for decision in state["decisions"]["approved"]:
        if decision.get("proposal_id") == proposal_id:
            return True
    return False


def _is_proposal_already_decided(state: dict, proposal_id: str) -> bool:
    """Check if proposal has any decision (approved or rejected)."""
    for decision in state["decisions"]["approved"]:
        if decision.get("proposal_id") == proposal_id:
            return True
    for decision in state["decisions"]["rejected"]:
        if decision.get("proposal_id") == proposal_id:
            return True
    return False


def _is_already_promoted_in_action_log(state: dict, proposal_id: str) -> bool:
    """Check if proposal has already been promoted (via action_log)."""
    for action in state["state_mutations"]["action_log"]:
        if (action.get("action_type") == "promotion" and
            action.get("proposal_id") == proposal_id):
            return True
    return False


def _create_mutation(proposal: dict, decision: dict, mutation_id: str) -> dict:
    """Create a state mutation record from a proposal and decision."""
    return {
        "id": mutation_id,
        "proposal_id": proposal["id"],
        "decision_id": decision["id"],
        "title": proposal.get("title"),
        "summary": proposal.get("summary"),
        "source_signal_id": proposal.get("source_signal_id"),
        "approved_by": decision.get("approved_by"),
        "approval_rationale": decision.get("rationale"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _create_action_log_entry(
    proposal_id: str,
    decision_id: str,
    mutation_id: str,
    proposal_type: ProposalType,
    triggered_by: str,
) -> dict:
    """Create an action_log entry for a promotion."""
    # Determine target type for clarity
    if proposal_type == "kb_candidate":
        target_type = "kb"
    else:
        target_type = "project"

    return {
        "id": str(uuid.uuid4()),
        "action_type": "promotion",
        "proposal_id": proposal_id,
        "decision_id": decision_id,
        "mutation_id": mutation_id,
        "target_type": target_type,
        "triggered_by": triggered_by,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
