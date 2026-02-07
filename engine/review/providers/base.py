# engine/review/providers/base.py
"""
Base interface for all review providers.

All providers MUST implement this interface and return
schema-compliant review payloads.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import uuid


class ReviewProvider(ABC):
    """
    Abstract base class for review providers.

    Contract:
    - review() MUST return a dict matching the review payload schema
    - Providers MUST NOT call other providers
    - Providers MUST NOT mutate external state
    - Providers are advisory only
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier (e.g., 'ollama', 'kimi', 'openai')."""
        pass

    @abstractmethod
    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Generate a review for the given draft.

        Args:
            draft_text: The text content to review
            draft_id: Unique identifier for the draft

        Returns:
            dict: Review payload matching the schema:
                {
                    "review_id": str,
                    "draft_id": str,
                    "model": str,
                    "confidence": float,
                    "risk_flags": list,
                    "review": str,
                    "created_at": str (ISO-8601)
                }
        """
        pass

    def _generate_review_id(self) -> str:
        """Generate a unique review ID."""
        return f"rev-{uuid.uuid4().hex[:12]}"

    def _get_timestamp(self) -> str:
        """Get current ISO-8601 timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def _build_payload(
        self,
        draft_id: str,
        review_text: str,
        confidence: float = 0.0,
        risk_flags: list | None = None
    ) -> dict:
        """
        Build a schema-compliant review payload.

        Args:
            draft_id: The draft being reviewed
            review_text: The review content
            confidence: Confidence score (0.0 to 1.0)
            risk_flags: List of identified risks

        Returns:
            dict: Complete review payload
        """
        return {
            "review_id": self._generate_review_id(),
            "draft_id": draft_id,
            "model": self.model_name,
            "confidence": max(0.0, min(1.0, confidence)),
            "risk_flags": risk_flags or [],
            "review": review_text,
            "created_at": self._get_timestamp()
        }
