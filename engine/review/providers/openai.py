# engine/review/providers/openai.py
"""
OpenAI/ChatGPT review provider — API-based review generation.

Uses OpenAI API for GPT model inference.
Requires OPENAI_API_KEY environment variable.
"""

import json
import os
import urllib.request
import urllib.error
from .base import ReviewProvider


class OpenAIReviewProvider(ReviewProvider):
    """
    Review provider using OpenAI API.

    Configuration:
    - api_key: OpenAI API key (from env or parameter)
    - model: Model to use (default: gpt-4o-mini)
    """

    API_BASE = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini"
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    @property
    def model_name(self) -> str:
        return "openai"

    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Generate a review using OpenAI API.

        Single call, no streaming, no retries.
        Returns stub response if API key missing or call fails.
        """
        if not self.api_key:
            return self._build_payload(
                draft_id=draft_id,
                review_text="[OpenAI API key not configured] Stub review.",
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
                review_text=f"[OpenAI API error: {e}] Stub review.",
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
        return f"""Review the following draft for:
1. Accuracy and correctness
2. Clarity and completeness
3. Potential risks or issues

Draft:
---
{draft_text}
---

Provide a brief review (2-3 paragraphs), a confidence level (low/medium/high),
and list any specific risk flags or concerns."""

    def _call_api(self, prompt: str) -> str:
        """Make a single request to the OpenAI API. No streaming."""
        url = f"{self.API_BASE}/chat/completions"
        data = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a careful, thorough document reviewer. "
                               "Provide concise but complete reviews."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
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
        if "high confidence" in lower:
            confidence = 0.8
        elif "medium confidence" in lower:
            confidence = 0.5
        elif "low confidence" in lower:
            confidence = 0.3

        # Extract risk flags
        risk_flags = []
        risk_indicators = {
            "accuracy": "accuracy_concern",
            "incorrect": "potential_errors",
            "missing": "incomplete_content",
            "unclear": "clarity_issue",
            "risk": "risk_identified",
            "concern": "concerns_noted"
        }
        for keyword, flag in risk_indicators.items():
            if keyword in lower:
                risk_flags.append(flag)

        return review_text, confidence, list(set(risk_flags))
