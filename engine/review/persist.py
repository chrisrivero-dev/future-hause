# engine/review/persist.py
"""
Review persistence layer.

Persists review payloads to the filesystem.
Location: payloads/reviews/{draft_id}/{review_id}.json

Rules:
- Do NOT update Action Log here
- Do NOT write anywhere else
- Reviews are grouped by draft_id
"""

import json
from pathlib import Path

# Base directory for review payloads
PAYLOADS_DIR = Path(__file__).parent.parent.parent / "payloads" / "reviews"


def get_reviews_dir() -> Path:
    """Get the base reviews directory, creating if needed."""
    PAYLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return PAYLOADS_DIR


def get_draft_reviews_dir(draft_id: str) -> Path:
    """Get the directory for a specific draft's reviews."""
    draft_dir = get_reviews_dir() / draft_id
    draft_dir.mkdir(parents=True, exist_ok=True)
    return draft_dir


def persist_review(payload: dict) -> Path:
    """
    Persist a review payload to disk.

    Args:
        payload: Validated review payload

    Returns:
        Path: Path to the saved file
    """
    draft_id = payload["draft_id"]
    review_id = payload["review_id"]

    # Get directory for this draft
    draft_dir = get_draft_reviews_dir(draft_id)

    # Write review file
    review_path = draft_dir / f"{review_id}.json"
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return review_path


def load_review(draft_id: str, review_id: str) -> dict | None:
    """
    Load a specific review by IDs.

    Args:
        draft_id: The draft ID
        review_id: The review ID

    Returns:
        dict or None: The review payload, or None if not found
    """
    review_path = get_reviews_dir() / draft_id / f"{review_id}.json"

    if not review_path.exists():
        return None

    with open(review_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_reviews_for_draft(draft_id: str) -> list[dict]:
    """
    Load all reviews for a specific draft.

    Args:
        draft_id: The draft ID

    Returns:
        list[dict]: List of review payloads, sorted by created_at
    """
    draft_dir = get_reviews_dir() / draft_id

    if not draft_dir.exists():
        return []

    reviews = []
    for review_file in draft_dir.glob("*.json"):
        try:
            with open(review_file, "r", encoding="utf-8") as f:
                reviews.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue

    # Sort by created_at
    reviews.sort(key=lambda r: r.get("created_at", ""))

    return reviews


def list_reviewed_drafts() -> list[str]:
    """
    List all draft IDs that have reviews.

    Returns:
        list[str]: List of draft IDs
    """
    reviews_dir = get_reviews_dir()

    if not reviews_dir.exists():
        return []

    return [
        d.name for d in reviews_dir.iterdir()
        if d.is_dir() and any(d.glob("*.json"))
    ]


def count_reviews(draft_id: str) -> int:
    """
    Count reviews for a specific draft.

    Args:
        draft_id: The draft ID

    Returns:
        int: Number of reviews
    """
    draft_dir = get_reviews_dir() / draft_id

    if not draft_dir.exists():
        return 0

    return len(list(draft_dir.glob("*.json")))
