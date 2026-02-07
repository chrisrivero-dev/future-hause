# engine/review/run.py
"""
Review Engine Orchestration.

Entry point for generating reviews. This module:
1. Accepts draft_id, draft_text, and provider_name
2. Enforces STRICT escalation policy
3. Calls provider.review()
4. Validates the payload
5. Persists via persist.py
6. Returns the payload

ESCALATION LADDER (STRICT):
1. Ollama — always allowed
2. Kimi — allowed when confidence < threshold
3. ChatGPT — allowed ONLY when multiple reviews disagree
4. Claude — allowed ONLY when allow_claude=True AND human_triggered=True

Claude is NOT a peer provider. Claude is:
- Safety lint only
- Human-triggered only
- Last resort
- Advisory only

Architecture constraints:
- Human-triggered ONLY
- Advisory output ONLY
- No execution
- No state mutation
- No automation
- No provider may call another provider
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.review.providers import PROVIDERS
from engine.review.schema import validate_review_payload, SchemaValidationError
from engine.review.persist import persist_review


# Escalation thresholds
CONFIDENCE_THRESHOLD = 0.6  # Below this, Kimi escalation allowed


class ReviewEngineError(Exception):
    """Base exception for review engine errors."""
    pass


class UnknownProviderError(ReviewEngineError):
    """Raised when an unknown provider is requested."""
    pass


class EscalationError(ReviewEngineError):
    """Raised when escalation conditions are not met."""
    pass


def list_providers() -> list[str]:
    """Return list of available provider names (excluding Claude by default)."""
    return [p for p in PROVIDERS.keys() if p != 'claude']


def list_all_providers() -> list[str]:
    """Return ALL provider names including Claude."""
    return list(PROVIDERS.keys())


def run_review(
    draft_id: str,
    draft_text: str,
    provider_name: str,
    persist: bool = True,
    allow_claude: bool = False,
    human_triggered: bool = False
) -> dict:
    """
    Run a review on the given draft using the specified provider.

    This function is the main entry point for the review engine.
    It MUST be human-triggered — no automated calls.

    ESCALATION POLICY:
    - Ollama: always allowed
    - Kimi: always allowed (use check_escalation_kimi for smart escalation)
    - OpenAI: always allowed (use check_escalation_openai for smart escalation)
    - Claude: ONLY when allow_claude=True AND human_triggered=True

    Args:
        draft_id: Unique identifier for the draft being reviewed
        draft_text: The text content of the draft
        provider_name: Name of the provider to use
        persist: Whether to persist the review payload (default: True)
        allow_claude: Explicit gate for Claude (default: False)
        human_triggered: Whether this was human-initiated (required for Claude)

    Returns:
        dict: The validated review payload

    Raises:
        UnknownProviderError: If provider_name is not recognized
        EscalationError: If Claude conditions not met
        SchemaValidationError: If the provider returns an invalid payload
    """
    # Validate provider name
    if provider_name not in PROVIDERS:
        raise UnknownProviderError(
            f"Unknown provider: {provider_name}. "
            f"Available: {list_all_providers()}"
        )

    # STRICT: Claude gating
    if provider_name == 'claude':
        if not allow_claude:
            raise EscalationError(
                "Claude is gated. Set allow_claude=True to enable. "
                "Claude is safety lint only, not a peer provider."
            )
        if not human_triggered:
            raise EscalationError(
                "Claude requires human_triggered=True. "
                "Claude must NEVER be called automatically."
            )

    # Instantiate provider
    provider_class = PROVIDERS[provider_name]
    provider = provider_class()

    # Generate review
    payload = provider.review(draft_text, draft_id)

    # Validate payload against schema
    try:
        validate_review_payload(payload)
    except SchemaValidationError as e:
        raise ReviewEngineError(f"Provider returned invalid payload: {e}")

    # Persist if requested
    if persist:
        persist_review(payload)

    return payload


def check_escalation_kimi(prior_reviews: list[dict]) -> bool:
    """
    Check if escalation to Kimi is allowed.

    Kimi is allowed when:
    - Prior review confidence < CONFIDENCE_THRESHOLD

    Args:
        prior_reviews: List of prior review payloads

    Returns:
        bool: True if Kimi escalation is allowed
    """
    if not prior_reviews:
        return True  # No prior reviews, Kimi allowed

    # Check if any prior review has low confidence
    for review in prior_reviews:
        if review.get('confidence', 1.0) < CONFIDENCE_THRESHOLD:
            return True

    return False


def check_escalation_openai(prior_reviews: list[dict]) -> bool:
    """
    Check if escalation to OpenAI/ChatGPT is allowed.

    OpenAI is allowed ONLY when:
    - Multiple reviews exist AND they disagree

    Disagreement = different risk_flags or significantly different confidence.

    Args:
        prior_reviews: List of prior review payloads

    Returns:
        bool: True if OpenAI escalation is allowed
    """
    if len(prior_reviews) < 2:
        return False  # Need at least 2 reviews to disagree

    # Check for disagreement
    confidences = [r.get('confidence', 0.5) for r in prior_reviews]
    confidence_spread = max(confidences) - min(confidences)

    # Significant confidence disagreement
    if confidence_spread > 0.3:
        return True

    # Check for flag disagreement
    all_flags = [set(r.get('risk_flags', [])) for r in prior_reviews]
    if len(all_flags) >= 2:
        # Check if flag sets differ significantly
        for i, flags_a in enumerate(all_flags):
            for flags_b in all_flags[i+1:]:
                symmetric_diff = flags_a.symmetric_difference(flags_b)
                if len(symmetric_diff) >= 2:
                    return True

    return False


def run_multi_review(
    draft_id: str,
    draft_text: str,
    provider_names: list[str],
    persist: bool = True,
    allow_claude: bool = False,
    human_triggered: bool = False
) -> list[dict]:
    """
    Run reviews using multiple providers with escalation enforcement.

    Each provider is called independently — no provider calls another.
    Claude requires explicit allow_claude=True AND human_triggered=True.

    Args:
        draft_id: Unique identifier for the draft
        draft_text: The text content of the draft
        provider_names: List of provider names to use
        persist: Whether to persist review payloads
        allow_claude: Explicit gate for Claude (default: False)
        human_triggered: Whether this was human-initiated (required for Claude)

    Returns:
        list[dict]: List of validated review payloads

    Raises:
        EscalationError: If Claude requested without proper flags
    """
    results = []
    for provider_name in provider_names:
        try:
            payload = run_review(
                draft_id=draft_id,
                draft_text=draft_text,
                provider_name=provider_name,
                persist=persist,
                allow_claude=allow_claude,
                human_triggered=human_triggered
            )
            results.append(payload)
        except EscalationError:
            # Do NOT silently fallback — re-raise escalation errors
            raise
        except ReviewEngineError as e:
            # Log other errors but continue with other providers
            print(f"[Review Engine] Error with {provider_name}: {e}")
            continue

    return results


def run_escalated_review(
    draft_id: str,
    draft_text: str,
    persist: bool = True,
    allow_claude: bool = False,
    human_triggered: bool = False
) -> list[dict]:
    """
    Run reviews with automatic escalation based on prior results.

    Escalation ladder:
    1. Ollama (always)
    2. Kimi (if Ollama confidence < threshold)
    3. OpenAI (if reviews disagree)
    4. Claude (ONLY if allow_claude=True AND human_triggered=True)

    Args:
        draft_id: Unique identifier for the draft
        draft_text: The text content of the draft
        persist: Whether to persist review payloads
        allow_claude: Explicit gate for Claude (default: False)
        human_triggered: Whether this was human-initiated

    Returns:
        list[dict]: List of review payloads from all escalation levels
    """
    results = []

    # Level 1: Ollama (always)
    try:
        ollama_result = run_review(
            draft_id=draft_id,
            draft_text=draft_text,
            provider_name='ollama',
            persist=persist
        )
        results.append(ollama_result)
    except ReviewEngineError as e:
        print(f"[Review Engine] Ollama failed: {e}")

    # Level 2: Kimi (if confidence low)
    if check_escalation_kimi(results):
        try:
            kimi_result = run_review(
                draft_id=draft_id,
                draft_text=draft_text,
                provider_name='kimi',
                persist=persist
            )
            results.append(kimi_result)
        except ReviewEngineError as e:
            print(f"[Review Engine] Kimi failed: {e}")

    # Level 3: OpenAI (if reviews disagree)
    if check_escalation_openai(results):
        try:
            openai_result = run_review(
                draft_id=draft_id,
                draft_text=draft_text,
                provider_name='openai',
                persist=persist
            )
            results.append(openai_result)
        except ReviewEngineError as e:
            print(f"[Review Engine] OpenAI failed: {e}")

    # Level 4: Claude (ONLY with explicit permission)
    # Claude is NOT automatic — must be explicitly requested
    if allow_claude and human_triggered:
        try:
            claude_result = run_review(
                draft_id=draft_id,
                draft_text=draft_text,
                provider_name='claude',
                persist=persist,
                allow_claude=True,
                human_triggered=True
            )
            results.append(claude_result)
        except ReviewEngineError as e:
            print(f"[Review Engine] Claude failed: {e}")

    return results


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run a review on a draft")
    parser.add_argument("--draft-id", required=True, help="Draft ID")
    parser.add_argument("--draft-text", required=True, help="Draft text to review")
    parser.add_argument(
        "--provider",
        required=True,
        choices=list_all_providers(),
        help="Provider to use"
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Don't persist the review"
    )
    parser.add_argument(
        "--allow-claude",
        action="store_true",
        help="Explicitly allow Claude (required for claude provider)"
    )
    parser.add_argument(
        "--human-triggered",
        action="store_true",
        help="Mark as human-triggered (required for claude provider)"
    )

    args = parser.parse_args()

    try:
        result = run_review(
            draft_id=args.draft_id,
            draft_text=args.draft_text,
            provider_name=args.provider,
            persist=not args.no_persist,
            allow_claude=args.allow_claude,
            human_triggered=args.human_triggered
        )
        print(json.dumps(result, indent=2))
    except ReviewEngineError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
