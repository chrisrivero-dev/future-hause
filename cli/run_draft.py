"""
Future Hause — Draft CLI

Runs DraftAgent, writes a review payload to disk,
and optionally triggers manual review (human-confirmed).
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on path (same fix as review CLI)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.agents.draft_agent import run as run_draft_agent  # noqa: E402
from engine.review.manual_review import request_review  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Run DraftAgent and optionally request review"
    )

    parser.add_argument(
        "--event",
        required=True,
        help="Event type to send to DraftAgent (e.g. EVT_DRAFT_REQUESTED)",
    )

    parser.add_argument(
        "--content",
        required=True,
        help="Draft content or prompt",
    )

    parser.add_argument(
        "--out",
        default="payloads/draft_review_payload.json",
        help="Where to write the review payload JSON",
    )

    parser.add_argument(
        "--review",
        action="store_true",
        help="Prompt to request review after draft is generated",
    )

    args = parser.parse_args()

    event = {
        "event": args.event,
        "content": args.content,
    }

    # Run DraftAgent
    result = run_draft_agent(event)

    if not result.get("review_available"):
        print("[error] DraftAgent did not produce a reviewable payload")
        sys.exit(1)

    payload = result["review_payload"]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[ok] Draft completed")
    print(f"[ok] Review payload written to: {out_path}")

    # Human-in-the-loop decision
    if args.review:
        answer = input("Request review now? (y/N): ").strip().lower()
        if answer == "y":
            review_result = request_review(payload)
            print(json.dumps(review_result, indent=2))
        else:
            print("[skipped] Review not requested")


if __name__ == "__main__":
    main()
