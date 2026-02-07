# engine/review/run.py
"""
Review Engine Orchestration.

Entry point for generating reviews. This module:
1. Accepts draft_id, draft_text, and provider_name
2. Selects the appropriate provider
3. Calls provider.review()
4. Validates the payload
5. Persists via persist.py
6. Returns the payload

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


class ReviewEngineError(Exception):
    """Base exception for review engine errors."""
    pass


class UnknownProviderError(ReviewEngineError):
    """Raised when an unknown provider is requested."""
    pass


def list_providers() -> list[str]:
    """Return list of available provider names."""
    return list(PROVIDERS.keys())


def run_review(
    draft_id: str,
    draft_text: str,
    provider_name: str,
    persist: bool = True
) -> dict:
    """
    Run a review on the given draft using the specified provider.

    This function is the main entry point for the review engine.
    It MUST be human-triggered — no automated calls.

    Args:
        draft_id: Unique identifier for the draft being reviewed
        draft_text: The text content of the draft
        provider_name: Name of the provider to use (ollama, kimi, openai, claude, gemini)
        persist: Whether to persist the review payload (default: True)

    Returns:
        dict: The validated review payload

    Raises:
        UnknownProviderError: If provider_name is not recognized
        SchemaValidationError: If the provider returns an invalid payload
    """
    # Validate provider name
    if provider_name not in PROVIDERS:
        raise UnknownProviderError(
            f"Unknown provider: {provider_name}. "
            f"Available: {list_providers()}"
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


def run_multi_review(
    draft_id: str,
    draft_text: str,
    provider_names: list[str],
    persist: bool = True
) -> list[dict]:
    """
    Run reviews using multiple providers.

    Each provider is called independently — no provider calls another.

    Args:
        draft_id: Unique identifier for the draft
        draft_text: The text content of the draft
        provider_names: List of provider names to use
        persist: Whether to persist review payloads

    Returns:
        list[dict]: List of validated review payloads
    """
    results = []
    for provider_name in provider_names:
        try:
            payload = run_review(
                draft_id=draft_id,
                draft_text=draft_text,
                provider_name=provider_name,
                persist=persist
            )
            results.append(payload)
        except ReviewEngineError as e:
            # Log error but continue with other providers
            print(f"[Review Engine] Error with {provider_name}: {e}")
            continue

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
        choices=list_providers(),
        help="Provider to use"
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Don't persist the review"
    )

    args = parser.parse_args()

    try:
        result = run_review(
            draft_id=args.draft_id,
            draft_text=args.draft_text,
            provider_name=args.provider,
            persist=not args.no_persist
        )
        print(json.dumps(result, indent=2))
    except ReviewEngineError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
