import requests
from datetime import datetime, timezone

from engine.system_identity import SYSTEM_IDENTITY, INTENT_CONTRACT, build_state_context
from .base import ReviewProvider


# =============================================================================
# Coach Mode Entrypoint (delegates — NOT a provider)
# =============================================================================

def run_coach_mode(draft_id: str, draft_text: str) -> dict:
    """
    Run Coach Mode using Ollama.
    Coach Mode is advisory and NOT part of the review engine.
    """
    return run_coach(draft_id=draft_id, draft_text=draft_text)


# =============================================================================
# Ollama Review Provider (STRICT safety review only)
# =============================================================================

class OllamaReviewProvider(ReviewProvider):
    """
    Local Ollama review provider.

    PURPOSE:
    - Safety / accuracy linting ONLY
    - Binary output when no issues exist
    - NO coaching, suggestions, or questions
    """

    name = "ollama"

    OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
    MODEL = "llama3.2:3b-instruct-q4_1"
    TIMEOUT = 60

    # -------------------------------------------------------------------------
    # Required abstract property
    # -------------------------------------------------------------------------

    @property
    def model_name(self) -> str:
        return self.MODEL

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def review(self, draft_text: str, draft_id: str) -> dict:
        """
        Generate a safety review using local Ollama.

        Falls back to stub payload if Ollama is unavailable.
        """
        prompt = self._build_review_prompt(draft_text)

        try:
            response = self._call_ollama(prompt)
            review_text, confidence, risk_flags = self._parse_response(response)
        except Exception as e:
            return self._build_stub_payload(draft_id, str(e))

        payload = self._build_payload(
            draft_id=draft_id,
            review_text=review_text,
            confidence=confidence,
            risk_flags=risk_flags,
        )

        # Enforce provider identity for schema compliance
        payload["model"] = self.name  # must be "ollama"

        return payload

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _call_ollama(self, prompt: str) -> dict:
        """
        Call local Ollama server.
        """
        payload = {
            "model": self.MODEL,
            "prompt": prompt,
            "stream": False,
        }

        r = requests.post(
            self.OLLAMA_URL,
            json=payload,
            timeout=self.TIMEOUT,
        )

        if r.status_code != 200:
            raise RuntimeError(f"Ollama HTTP {r.status_code}: {r.text}")

        return r.json()

    def _parse_response(self, response: dict):
        """
        Parse Ollama response into review components.
        """
        text = response.get("response", "").strip()

        if not text:
            raise ValueError("Empty response from Ollama")

        confidence = 0.6
        risk_flags = []

        lowered = text.lower()
        if "risk" in lowered or "misleading" in lowered:
            risk_flags.append("potential_risk")

        return text, confidence, risk_flags

    def _build_review_prompt(self, draft_text: str) -> str:
        """
        STRICT safety lint contract.
        """
        state_context = build_state_context()

        return (
            SYSTEM_IDENTITY + "\n\n"
            + INTENT_CONTRACT + "\n\n"
            + state_context + "\n\n"
            "You are a safety and accuracy reviewer.\n"
            "TASK:\n"
            "- Identify risks, ambiguities, or misleading elements.\n"
            "- If none exist, respond with EXACTLY: 'No issues detected.'\n"
            "- Do NOT provide suggestions, questions, examples, or explanations.\n"
            "- Do NOT rewrite the draft.\n\n"
            f"DRAFT:\n{draft_text}"
        )

    def _build_stub_payload(self, draft_id: str, error: str) -> dict:
        """
        Build a stub payload when Ollama is unavailable.
        """
        payload = self._build_payload(
            draft_id=draft_id,
            review_text=f"[Ollama unavailable: {error}] Stub review generated.",
            confidence=0.0,
            risk_flags=["ollama_unavailable", "stub_review"],
        )

        payload["model"] = self.name  # must be "ollama"
        return payload
