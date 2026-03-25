"""
Future Hause — Review Engine Adapter (Concrete Class)

Review engines critique and improve outputs produced by agents.
They NEVER execute actions and NEVER mutate state.

This is a CONCRETE class — no abstract base inheritance.
"""

from typing import Dict, List, Any


class ReviewResult(Dict):
    """
    Standard review output contract.
    """
    review: str
    confidence: float
    risk_flags: List[str]
    model: str


class ReviewEngineAdapter:
    """
    Concrete review engine adapter that delegates to providers.
    No abstract base class — fully instantiable.
    """

    def __init__(self):
        """Initialize the adapter. No abstract methods to implement."""
        pass

    def _normalize_response(
        self,
        success: bool,
        error: str | None,
        result: Any,
        confidence: float
    ) -> Dict:
        """
        Normalize all adapter responses to standard shape.

        Returns:
            {"success": bool, "error": str | None, "result": any, "confidence": number}
        """
        return {
            "success": success,
            "error": error,
            "result": result,
            "confidence": confidence,
        }

    def review(self, payload: Dict) -> Dict:
        """
        Review a draft or agent output.

        HARD RULES:
        - No execution
        - No delegation
        - No agent spawning
        - No state mutation

        Returns:
            Normalized response: {"success", "error", "result", "confidence"}
        """
        try:
            from engine.review.providers.ollama import OllamaReviewProvider
            provider = OllamaReviewProvider()
            provider_result = provider.review(
                draft_text=payload.get("draft_text", ""),
                draft_id=payload.get("draft_id", ""),
            )
            return self._normalize_response(
                success=True,
                error=None,
                result=provider_result,
                confidence=provider_result.get("confidence", 0.0),
            )
        except Exception as e:
            return self._normalize_response(
                success=False,
                error=str(e),
                result=None,
                confidence=0.0,
            )

    def run(
        self,
        draft_id: str,
        draft_text: str,
        human_triggered: bool = False,
        provider_name: str = "ollama",
        persist: bool = True,
        allow_claude: bool = False,
    ) -> Dict:
        """
        Run a review using the specified provider.

        Args:
            draft_id: Identifier for the draft
            draft_text: The text to review
            human_triggered: Whether review was triggered by human
            provider_name: Provider to use (default: ollama)
            persist: Whether to persist the result
            allow_claude: Whether to allow Claude provider

        Returns:
            Normalized response: {"success", "error", "result", "confidence"}
        """
        try:
            from engine.review.providers.ollama import OllamaReviewProvider

            # Currently only Ollama is supported
            provider = OllamaReviewProvider()
            provider_result = provider.review(draft_text=draft_text, draft_id=draft_id)
            provider_result["human_triggered"] = human_triggered

            return self._normalize_response(
                success=True,
                error=None,
                result=provider_result,
                confidence=provider_result.get("confidence", 0.0),
            )
        except Exception as e:
            return self._normalize_response(
                success=False,
                error=str(e),
                result=None,
                confidence=0.0,
            )
