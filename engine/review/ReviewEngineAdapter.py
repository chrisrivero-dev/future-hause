from engine.draft_work_log import (
    DRAFT_WORK_LOG,
    DraftReview,
    attach_review,
)


from datetime import datetime
import uuid


class ReviewEngineAdapter:
    def __init__(
        self,
        provider_name: str = "local",
        persist: bool = True,
        allow_claude: bool = False,
    ):
        self.provider_name = provider_name
        self.persist = persist
        self.allow_claude = allow_claude

    def run(
        self,
        *,
        draft_id: str,
        draft_text: str,
        human_triggered: bool = False,
    ):
        if draft_id not in DRAFT_WORK_LOG:
            raise ValueError("Draft does not exist")

        draft = DRAFT_WORK_LOG[draft_id]

        # ─────────────────────────────────────────────
        # Move to reviewing state
        # ─────────────────────────────────────────────
        if draft.status == "drafted":
            draft.status = "reviewing"

        # ─────────────────────────────────────────────
        # Minimal deterministic review logic
        # ─────────────────────────────────────────────
        severity = "low"
        notes = "No major issues detected."

        if len(draft_text.strip()) < 40:
            severity = "medium"
            notes = "Draft is very short. Consider expanding."

        review_id = str(uuid.uuid4())

        review = DraftReview(
            draft_id=draft_id,
            reviewer="agent",
            review_type="clarity",
            severity=severity,
            notes=notes,
            references=[],
        )

        # ─────────────────────────────────────────────
        # Finalize state
        # ─────────────────────────────────────────────
        draft.status = "reviewed"
        draft.review = {
            "review_id": review_id,
            "notes": notes,
            "severity": severity,
            "status": "flagged" if severity != "low" else "approved",
            "reviewed_at": datetime.utcnow().isoformat(),
        }

        if self.persist:
            attach_review(review)

        return {
            "review_id": review_id,
            "draft_id": draft_id,
            "status": draft.status,
            "severity": severity,
            "notes": notes,
        }
