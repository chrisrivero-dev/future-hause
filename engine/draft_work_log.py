from datetime import datetime
from typing import Dict, List, Literal
import uuid


# ─────────────────────────────────────────────
# Draft Status Enum
# ─────────────────────────────────────────────

DraftStatus = Literal[
    "drafted",
    "under_review",
    "flagged",
    "approved",
    "rejected",
]


# ─────────────────────────────────────────────
# DraftWork Entity
# ─────────────────────────────────────────────

class DraftWork:
    def __init__(
        self,
        *,
        message_id: str,
        router_intent: str,
        body: str,
        format: Literal["text", "md", "json", "code"],
        created_by: Literal["human", "agent"],
        tags: List[str] = None,
    ):
        self.draft_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat()
        self.created_by = created_by

        self.source = {
            "message_id": message_id,
            "router_intent": router_intent,
        }

        self.zone = "work"

        self.content = {
            "body": body,
            "format": format,
        }

        self.status: DraftStatus = "drafted"
        self.tags = tags or []


# ─────────────────────────────────────────────
# DraftReview Entity (read-only attachment)
# ─────────────────────────────────────────────

class DraftReview:
    def __init__(
        self,
        *,
        draft_id: str,
        reviewer: Literal["agent", "human"],
        review_type: Literal["contract", "architecture", "clarity"],
        severity: Literal["low", "medium", "high"],
        notes: str,
        references: List[str] = None,
    ):
        self.review_id = str(uuid.uuid4())
        self.draft_id = draft_id
        self.reviewer = reviewer
        self.review_type = review_type

        self.findings = {
            "severity": severity,
            "notes": notes,
            "references": references or [],
        }

        self.created_at = datetime.utcnow().isoformat()


# ─────────────────────────────────────────────
# In-Memory Authoritative Store
# ─────────────────────────────────────────────

DRAFT_WORK_LOG: Dict[str, DraftWork] = {}
DRAFT_REVIEWS: Dict[str, List[DraftReview]] = {}


# ─────────────────────────────────────────────
# Lifecycle Functions (HUMAN-ONLY transitions)
# ─────────────────────────────────────────────

def create_draft(
    *,
    message_id: str,
    router_intent: str,
    body: str,
    format: Literal["text", "md", "json", "code"],
    created_by: Literal["human", "agent"],
    tags: List[str] = None,
) -> DraftWork:

    draft = DraftWork(
        message_id=message_id,
        router_intent=router_intent,
        body=body,
        format=format,
        created_by=created_by,
        tags=tags,
    )

    DRAFT_WORK_LOG[draft.draft_id] = draft
    return draft




def attach_review(review: DraftReview):
    if review.draft_id not in DRAFT_WORK_LOG:
        raise ValueError("Draft does not exist")

    DRAFT_REVIEWS.setdefault(review.draft_id, []).append(review)

    draft = DRAFT_WORK_LOG[review.draft_id]

    if review.findings["severity"] in ("medium", "high"):
        draft.status = "flagged"


def decide_draft(draft_id: str, decision: Literal["approved", "rejected"]):
    draft = DRAFT_WORK_LOG[draft_id]

    if draft.status not in ("under_review", "flagged"):
        raise ValueError("Draft must be reviewed before decision")

    draft.status = decision
