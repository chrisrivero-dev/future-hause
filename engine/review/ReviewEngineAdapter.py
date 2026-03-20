"""
Future Hause — Review Engine Adapter (Interface)

Review engines critique and improve outputs produced by agents.
They NEVER execute actions and NEVER mutate state.
"""

from typing import Dict, List


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
    Review engine adapter that delegates to providers.
    """

    def review(self, payload: Dict) -> ReviewResult:
        """
        Review a draft or agent output.

        HARD RULES:
        - No execution
        - No delegation
        - No agent spawning
        - No state mutation
        """
        from engine.review.providers.ollama import OllamaReviewProvider

        provider = OllamaReviewProvider()
        return provider.review(
            draft_text=payload.get("draft_text", ""),
            draft_id=payload.get("draft_id", ""),
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
            Review result dict
        """
        from engine.review.providers.ollama import OllamaReviewProvider

        # Currently only Ollama is supported
        provider = OllamaReviewProvider()
        result = provider.review(draft_text=draft_text, draft_id=draft_id)
        result["human_triggered"] = human_triggered

        return result
