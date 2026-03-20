"""
Future Hause — Review Provider Base Class

Base class for review providers (Ollama, Kimi, etc.)
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List


class ReviewProvider(ABC):
    """
    Abstract base class for review providers.
    """

    name: str = "base"

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name used by this provider."""
        pass

    @abstractmethod
    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Review a draft and return structured feedback.

        Args:
            draft_text: The text to review
            draft_id: Identifier for the draft

        Returns:
            dict with review, confidence, risk_flags, model
        """
        pass

    def _build_payload(
        self,
        draft_id: str,
        review_text: str,
        confidence: float,
        risk_flags: List[str],
    ) -> dict:
        """
        Build a standardized review payload.
        """
        return {
            "draft_id": draft_id,
            "review": review_text,
            "confidence": confidence,
            "risk_flags": risk_flags,
            "model": self.model_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "human_triggered": False,
        }
