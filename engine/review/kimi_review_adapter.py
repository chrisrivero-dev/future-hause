"""
Future Hause — KimiReviewAdapter

Kimi K2.5 is used STRICTLY as a review engine.
Agent swarm / delegation / tool use is explicitly forbidden.
"""

from typing import Dict, List
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter, ReviewResult


class KimiReviewAdapter(ReviewEngineAdapter):
    def __init__(self, api_key: str, model: str = "kimi-k2.5"):
        if not api_key:
            raise ValueError("KimiReviewAdapter requires an API key")

        self.api_key = api_key
        self.model = model

    def review(self, payload: Dict) -> ReviewResult:
        """
        Review a draft or agent output.

        Payload is expected to include:
        - original_input
        - draft_output
        - agent_name
        """

        # ⚠️ This is a stub — no real API call yet
        # The important thing is the CONSTRAINTS

        review_text = (
            "Kimi Review (stub):\n"
            "- Identified reasoning gaps\n"
            "- Suggested clearer structure\n"
            "- No execution recommended"
        )

        risk_flags: List[str] = []

        if len(payload.get("draft_output", "")) < 200:
            risk_flags.append("thin_draft")

        return {
            "review": review_text,
            "confidence": 0.75,
            "risk_flags": risk_flags,
            "model": self.model,
        }
