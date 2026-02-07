# engine/review/providers/claude.py
"""
Claude (Anthropic) review provider — API-based review generation.

Uses Anthropic API for Claude model inference.
Requires ANTHROPIC_API_KEY environment variable.
"""

import json
import os
import urllib.request
import urllib.error
from .base import ReviewProvider


class ClaudeReviewProvider(ReviewProvider):
    """
    Review provider using Anthropic Claude API.

    Configuration:
    - api_key: Anthropic API key (from env or parameter)
    - model: Model to use (default: claude-3-haiku-20240307)
    """

    API_BASE = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-haiku-20240307"
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model

    @property
    def model_name(self) -> str:
        return "claude"

    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Generate a review using Claude API.

        Minimal config, single call, no streaming.
        Returns stub response if API key missing or call fails.
        """
        if not self.api_key:
            return self._build_payload(
                draft_id=draft_id,
                review_text="[Anthropic API key not configured] Stub review.",
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
                review_text=f"[Claude API error: {e}] Stub review.",
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
        return f"""Please review the following draft for:
1. Accuracy and correctness
2. Clarity and completeness
3. Potential risks or issues

Draft:
---
{draft_text}
---

Provide:
- A brief review (2-3 paragraphs)
- Your confidence level (low/medium/high)
- Any specific risk flags or concerns"""

    def _call_api(self, prompt: str) -> str:
        """Make a single request to the Anthropic API."""
        url = f"{self.API_BASE}/messages"
        data = json.dumps({
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            # Claude returns content as list of blocks
            content_blocks = result.get("content", [])
            text_content = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text_content += block.get("text", "")
            return text_content

    def _parse_response(self, response: str) -> tuple[str, float, list]:
        """Parse response to extract review, confidence, and flags."""
        review_text = response.strip()

        # Extract confidence
        confidence = 0.5
        lower = response.lower()
        if "high confidence" in lower or "confidence: high" in lower:
            confidence = 0.8
        elif "medium confidence" in lower or "confidence: medium" in lower:
            confidence = 0.5
        elif "low confidence" in lower or "confidence: low" in lower:
            confidence = 0.3

        # Extract risk flags
        risk_flags = []
        risk_keywords = [
            ("inaccurate", "accuracy_issue"),
            ("incorrect", "potential_errors"),
            ("missing", "incomplete_content"),
            ("unclear", "clarity_issue"),
            ("risk", "risk_identified"),
            ("concern", "concerns_noted"),
            ("error", "error_detected"),
        ]
        for keyword, flag in risk_keywords:
            if keyword in lower:
                risk_flags.append(flag)

        return review_text, confidence, list(set(risk_flags))
