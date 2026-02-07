# engine/review/providers/kimi.py
"""
Kimi (Moonshot) review provider — API-based review generation.

Uses Moonshot API for Kimi model inference.
Requires MOONSHOT_API_KEY environment variable.
"""

import json
import os
import urllib.request
import urllib.error
from .base import ReviewProvider


class KimiReviewProvider(ReviewProvider):
    """
    Review provider using Moonshot/Kimi API.

    Configuration:
    - api_key: Moonshot API key (from env or parameter)
    - model: Model to use (default: moonshot-v1-8k)
    """

    API_BASE = "https://api.moonshot.cn/v1"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "moonshot-v1-8k"
    ):
        self.api_key = api_key or os.environ.get("MOONSHOT_API_KEY", "")
        self.model = model

    @property
    def model_name(self) -> str:
        return "kimi"

    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Generate a review using Kimi/Moonshot API.

        Returns stub response if API key missing or call fails.
        """
        if not self.api_key:
            return self._build_payload(
                draft_id=draft_id,
                review_text="[Kimi API key not configured] Stub review.",
                confidence=0.0,
                risk_flags=["api_key_missing", "stub_review"]
            )

        prompt = self._build_review_prompt(draft_text)

        try:
            response = self._call_api(prompt)
            review_text, confidence, risk_flags = self._parse_response(response)
        except Exception as e:
            return self._build_payload(
                draft_id=draft_id,
                review_text=f"[Kimi API error: {e}] Stub review.",
                confidence=0.0,
                risk_flags=["api_error", "stub_review"]
            )

        return self._build_payload(
            draft_id=draft_id,
            review_text=review_text,
            confidence=confidence,
            risk_flags=risk_flags
        )

    def _build_review_prompt(self, draft_text: str) -> str:
        """Build the review prompt."""
        return f"""Review the following draft for accuracy, clarity, and potential issues.

Draft:
---
{draft_text}
---

Provide:
1. A brief review (2-3 paragraphs)
2. Confidence level (low/medium/high)
3. Any risk flags or concerns"""

    def _call_api(self, prompt: str) -> str:
        """Make a request to the Moonshot API."""
        url = f"{self.API_BASE}/chat/completions"
        data = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a careful document reviewer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["choices"][0]["message"]["content"]

    def _parse_response(self, response: str) -> tuple[str, float, list]:
        """Parse response to extract review, confidence, and flags."""
        review_text = response.strip()

        # Extract confidence
        confidence = 0.5
        lower = response.lower()
        if "high" in lower and "confidence" in lower:
            confidence = 0.8
        elif "low" in lower and "confidence" in lower:
            confidence = 0.3

        # Extract risk flags
        risk_flags = []
        if "concern" in lower or "issue" in lower:
            risk_flags.append("concerns_noted")
        if "error" in lower or "incorrect" in lower:
            risk_flags.append("potential_errors")
        if "missing" in lower or "incomplete" in lower:
            risk_flags.append("incomplete_content")

        return review_text, confidence, risk_flags
