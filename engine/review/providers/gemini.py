# engine/review/providers/gemini.py
"""
Gemini (Google) review provider — STUB ONLY.

This is a placeholder implementation that returns mock review payloads.
Full implementation pending Google AI API integration.
"""

from .base import ReviewProvider


class GeminiReviewProvider(ReviewProvider):
    """
    Stub review provider for Gemini.

    Returns mock review payloads for testing/development.
    NOT connected to actual Gemini API.
    """

    def __init__(self, api_key: str | None = None):
        # API key stored but not used (stub only)
        self.api_key = api_key

    @property
    def model_name(self) -> str:
        return "gemini"

    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Return a mock review payload.

        This is a STUB implementation. It does not call Gemini API.
        """
        # Generate a simple mock review based on draft length
        draft_length = len(draft_text)

        if draft_length < 50:
            mock_review = "This draft is very short. Consider expanding with more detail."
            confidence = 0.3
            risk_flags = ["too_short", "needs_expansion"]
        elif draft_length < 200:
            mock_review = "This draft covers the basics but could benefit from additional context or examples."
            confidence = 0.5
            risk_flags = ["could_be_expanded"]
        else:
            mock_review = "This draft appears to be reasonably complete. A full review would require Gemini API integration."
            confidence = 0.6
            risk_flags = []

        # Mark as stub review
        mock_review += "\n\n[STUB: Gemini provider not fully implemented]"
        risk_flags.append("stub_review")

        return self._build_payload(
            draft_id=draft_id,
            review_text=mock_review,
            confidence=confidence,
            risk_flags=risk_flags
        )
