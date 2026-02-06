"""
Future Hause — Review CLI

Manually trigger a review for a DraftAgent output.
This command must be invoked explicitly by a human.
"""

import argparse
import json
import sys
from pathlib import Path

# ✅ FIX: add project root to PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.review.manual_review import request_review  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Trigger a manual review for a DraftAgent output"
    )

    parser.add_argument(
        "--payload",
        required=True,
        help="Path to JSON file containing review_payload"
    )

    args = parser.parse_args()

    try:
        with open(args.payload, "r") as f:
            review_payload = json.load(f)
    except Exception as e:
        print(f"[error] Failed to load payload: {e}", file=sys.stderr)
        sys.exit(1)

    result = request_review(review_payload)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
