# engine/review/schema.py
"""
Review payload schema validation.

The review payload schema is LOCKED:
{
    "review_id": str,
    "draft_id": str,
    "model": str (one of: kimi, openai, claude, ollama, gemini),
    "confidence": float (0.0 to 1.0),
    "risk_flags": list of str,
    "review": str,
    "created_at": str (ISO-8601)
}

No extra fields. No missing fields.
"""

from datetime import datetime

VALID_MODELS = {'kimi', 'openai', 'claude', 'ollama', 'gemini'}

REQUIRED_FIELDS = {
    'review_id': str,
    'draft_id': str,
    'model': str,
    'confidence': (int, float),
    'risk_flags': list,
    'review': str,
    'created_at': str,
}


class SchemaValidationError(Exception):
    """Raised when a review payload fails schema validation."""
    pass


def validate_review_payload(payload: dict) -> dict:
    """
    Validate a review payload against the locked schema.

    Args:
        payload: The review payload to validate

    Returns:
        dict: The validated payload (unchanged if valid)

    Raises:
        SchemaValidationError: If validation fails
    """
    if not isinstance(payload, dict):
        raise SchemaValidationError("Payload must be a dict")

    # Check for required fields
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in payload:
            raise SchemaValidationError(f"Missing required field: {field}")

        value = payload[field]
        if not isinstance(value, expected_type):
            raise SchemaValidationError(
                f"Field '{field}' must be {expected_type}, got {type(value)}"
            )

    # Check for extra fields
    extra_fields = set(payload.keys()) - set(REQUIRED_FIELDS.keys())
    if extra_fields:
        raise SchemaValidationError(f"Extra fields not allowed: {extra_fields}")

    # Validate model is one of the allowed values
    if payload['model'] not in VALID_MODELS:
        raise SchemaValidationError(
            f"Invalid model: {payload['model']}. Must be one of: {VALID_MODELS}"
        )

    # Validate confidence is in range
    confidence = payload['confidence']
    if not (0.0 <= confidence <= 1.0):
        raise SchemaValidationError(
            f"Confidence must be between 0.0 and 1.0, got {confidence}"
        )

    # Validate risk_flags contains only strings
    for flag in payload['risk_flags']:
        if not isinstance(flag, str):
            raise SchemaValidationError(
                f"risk_flags must contain only strings, got {type(flag)}"
            )

    # Validate created_at is ISO-8601
    try:
        datetime.fromisoformat(payload['created_at'].replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        raise SchemaValidationError(
            f"created_at must be ISO-8601 format: {e}"
        )

    return payload


def create_empty_payload(draft_id: str, model: str) -> dict:
    """
    Create an empty/placeholder review payload.

    Useful for error cases where we need a valid schema
    but no actual review was generated.
    """
    from datetime import timezone
    return {
        "review_id": f"rev-empty-{draft_id[:8]}",
        "draft_id": draft_id,
        "model": model,
        "confidence": 0.0,
        "risk_flags": ["generation_failed"],
        "review": "[Review generation failed]",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
