# engine/review/providers/ollama.py
"""
Ollama review provider — Local LLM review generation.

Uses Ollama API at localhost:11434 for local inference.
Falls back to stub if model unavailable.
"""

import json
import urllib.request
import urllib.error
from .base import ReviewProvider


class OllamaReviewProvider(ReviewProvider):
    """
    Review provider using local Ollama instance.

    Configuration:
    - host: Ollama API host (default: localhost)
    - port: Ollama API port (default: 11434)
    - model: Model to use (default: mistral:latest)
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 11434,
        model: str = "mistral:latest"
    ):
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"

    @property
    def model_name(self) -> str:
        return "ollama"

    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Generate a review using local Ollama instance.

        Falls back to stub response if Ollama unavailable.
        """
        prompt = self._build_review_prompt(draft_text)

        try:
            response = self._call_ollama(prompt)
            review_text, confidence, risk_flags = self._parse_response(response)
        except Exception as e:
            # Fallback to stub if Ollama unavailable
            return self._build_stub_payload(draft_id, str(e))

        return self._build_payload(
            draft_id=draft_id,
            review_text=review_text,
            confidence=confidence,
            risk_flags=risk_flags
        )

    def _build_review_prompt(self, draft_text: str) -> str:
        """Build the review prompt for the model."""
        return f"""You are a careful reviewer. Review the following draft for:
1. Accuracy and correctness
2. Clarity and completeness
3. Potential risks or issues

Draft to review:
---
{draft_text}
---

Provide a brief review (2-3 paragraphs). Be specific about any concerns.
End with a confidence level (low/medium/high) and list any risk flags."""

    def _call_ollama(self, prompt: str) -> str:
        """Make a request to the Ollama API."""
        url = f"{self.base_url}/api/generate"
        data = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "")

    def _parse_response(self, response: str) -> tuple[str, float, list]:
        """
        Parse the model response to extract review, confidence, and flags.

        Returns:
            tuple: (review_text, confidence, risk_flags)
        """
        review_text = response.strip()

        # Extract confidence from response text
        confidence = 0.5  # default to medium
        lower_response = response.lower()
        if "high confidence" in lower_response or "confidence: high" in lower_response:
            confidence = 0.8
        elif "low confidence" in lower_response or "confidence: low" in lower_response:
            confidence = 0.3

        # Extract risk flags (simple heuristic)
        risk_flags = []
        risk_keywords = [
            "risk", "concern", "issue", "problem", "error",
            "incorrect", "missing", "unclear", "incomplete"
        ]
        for keyword in risk_keywords:
            if keyword in lower_response:
                risk_flags.append(f"detected_{keyword}")

        # Deduplicate flags
        risk_flags = list(set(risk_flags))[:5]  # limit to 5 flags

        return review_text, confidence, risk_flags

    def _build_stub_payload(self, draft_id: str, error: str) -> dict:
        """Build a stub payload when Ollama is unavailable."""
        return self._build_payload(
            draft_id=draft_id,
            review_text=f"[Ollama unavailable: {error}] Stub review generated.",
            confidence=0.0,
            risk_flags=["ollama_unavailable", "stub_review"]
        )
