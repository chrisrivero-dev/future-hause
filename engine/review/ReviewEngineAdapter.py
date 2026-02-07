"""
Future Hause — Review Engine Adapter (Interface)

Review engines critique and improve outputs produced by agents.
They NEVER execute actions and NEVER mutate state.
"""

from typing import Dict, List
from abc import ABC, abstractmethod


class ReviewResult(Dict):
    """
    Standard review output contract.
    """
    review: str
    confidence: float
    risk_flags: List[str]
    model: str


class ReviewEngineAdapter(ABC):
    """
    All review engines must implement this interface.
    """

    @abstractmethod
    def review(self, payload: Dict) -> ReviewResult:
        """
        Review a draft or agent output.

        HARD RULES:
        - No execution
        - No delegation
        - No agent spawning
        - No state mutation
        """
        pass
