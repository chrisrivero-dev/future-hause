import uuid
from datetime import datetime

from engine.state_manager import load_state
from engine.draft_work_log import create_draft, DRAFT_WORK_LOG


def run_kb_draft_generation(llm_callable):
    """
    Generates KB drafts from kb_candidates.
    Does NOT approve or promote.
    Pure pre-drafting layer.
    """

    state = load_state()
    candidates = state["proposals"]["kb_candidates"]

    drafts_created = 0
    skipped_existing = 0

    # Prevent duplicate drafts per proposal
    existing_proposal_ids = {
        draft.content.get("source_proposal_id")
        for draft in DRAFT_WORK_LOG.values()
    }

    for proposal in candidates:
        proposal_id = proposal["id"]

        if proposal_id in existing_proposal_ids:
            skipped_existing += 1
            continue

        prompt = f"""
You are writing a structured knowledge base article.

Title: {proposal['title']}
Summary: {proposal['summary']}

Write a clear KB article with:

- Problem
- Cause
- Solution
- Notes (if relevant)

Keep it concise and professional.
"""

        generated_text = llm_callable(prompt)

        draft = create_draft(
            message_id=str(uuid.uuid4()),
            router_intent="kb_draft",
            body=generated_text,
            format="markdown",
            created_by="system",
            tags=["kb_draft"],
        )

        # Attach proposal reference
        draft.content["source_proposal_id"] = proposal_id
        draft.content["generated_at"] = datetime.utcnow().isoformat()

        drafts_created += 1

    return {
        "status": "complete",
        "drafts_created": drafts_created,
        "skipped_existing": skipped_existing,
        "total_candidates": len(candidates),
    }
