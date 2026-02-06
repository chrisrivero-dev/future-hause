"""
Future Hause — Manual Review Trigger

Reviews are NEVER automatic.
This module is called explicitly by a human or UI action.
"""

from typing import Dict
from engine.review.kimi_review_adapter import KimiReviewAdapter


def request_review(review_payload: Dict) -> Dict:
    """
    Manually trigger a review for a draft or agent output.
    """

    # In real usage, API keys will come from secure config
    kimi = KimiReviewAdapter(api_key="KIMI_API_KEY_PLACEHOLDER")

    review_result = kimi.review(review_payload)

    return {
        "status": "review_completed",
        "review_engine": "Kimi",
        "review": review_result,
    }
