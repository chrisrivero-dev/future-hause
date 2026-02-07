# engine/review/providers/claude.py
"""
Claude (Anthropic) review provider — SAFETY LINT ONLY.

Role (FINALIZED):
- Safety lint only
- Human-triggered only
- Last resort
- Advisory only
- No reasoning, no drafting, no iteration

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
    Claude provider — SAFETY LINT ONLY.

    Claude is NOT a peer provider. It serves as:
    - Binary safety check
    - Last resort escalation
    - Human-triggered only

    Output: Short list of issues OR "No issues detected."
    No reasoning. No rewrites. No alternatives.
    """

    API_BASE = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"
    MAX_TOKENS = 150  # Hard limit for lint output

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
        Perform safety lint on draft.

        Binary output: list of issues OR empty.
        No reasoning. No rewrites. No alternatives.
        """
        if not self.api_key:
            return self._build_payload(
                draft_id=draft_id,
                review_text="[Anthropic API key not configured]",
                confidence=0.0,
                risk_flags=["api_key_missing", "stub_review"]
            )

        prompt = self._build_lint_prompt(draft_text)

        try:
            response = self._call_api(prompt)
            review_text, confidence, risk_flags = self._parse_lint_response(response)
        except Exception as e:
            return self._build_payload(
                draft_id=draft_id,
                review_text=f"[Claude API error: {e}]",
                confidence=0.0,
                risk_flags=["api_error", "stub_review"]
            )

        return self._build_payload(
            draft_id=draft_id,
            review_text=review_text,
            confidence=confidence,
            risk_flags=risk_flags
        )

    def _build_lint_prompt(self, draft_text: str) -> str:
        """
        Build binary lint prompt.

        Instruction-only. One-pass. No reasoning.
        """
        return f"""Analyze the following text for risks, ambiguities, or misleading elements.

TEXT:
{draft_text}

RULES:
- List issues as bullet points (max 5)
- Do NOT explain reasoning
- Do NOT rewrite content
- Do NOT suggest alternatives
- If no issues exist, respond only: "No issues detected."

OUTPUT:"""

    def _call_api(self, prompt: str) -> str:
        """Make a single request to the Anthropic API."""
        url = f"{self.API_BASE}/messages"
        data = json.dumps({
            "model": self.model,
            "max_tokens": self.MAX_TOKENS,
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

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            content_blocks = result.get("content", [])
            text_content = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text_content += block.get("text", "")
            return text_content

    def _parse_lint_response(self, response: str) -> tuple[str, float, list]:
        """
        Parse binary lint response.

        Returns:
            tuple: (review_text, confidence, risk_flags)
        """
        review_text = response.strip()
        lower = review_text.lower()

        # Check for clean result
        if "no issues detected" in lower or review_text == "":
            return "No issues detected.", 1.0, []

        # Count issues (bullet points)
        lines = [l.strip() for l in review_text.split('\n') if l.strip()]
        issue_count = sum(1 for l in lines if l.startswith(('-', '•', '*')))

        # Confidence inversely proportional to issues
        if issue_count == 0:
            confidence = 0.8
        elif issue_count <= 2:
            confidence = 0.5
        else:
            confidence = 0.3

        # Extract risk flags from content
        risk_flags = []
        if "risk" in lower:
            risk_flags.append("risk_identified")
        if "ambig" in lower:
            risk_flags.append("ambiguity_detected")
        if "mislead" in lower:
            risk_flags.append("misleading_content")
        if "unclear" in lower:
            risk_flags.append("clarity_issue")
        if "error" in lower or "incorrect" in lower:
            risk_flags.append("potential_error")

        return review_text, confidence, list(set(risk_flags))
