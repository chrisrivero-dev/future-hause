"""
Proposal Generator for Future Hause

Converts perception signals into proposal candidates:
- discussion signals → kb_candidates
- announcement signals → project_candidates

LLM-assisted synthesis for higher quality titles, summaries,
and impact scoring.

Uses state_manager for persistence.
"""

import uuid
import json
from datetime import datetime, timezone

from engine.state_manager import load_state, save_state


# ---------------------------------------------------------
# PROMPT TEMPLATE
# ---------------------------------------------------------

PROPOSAL_PROMPT = """
You are an intelligence synthesis engine.

Based on the following signal, generate a structured proposal.

Signal:
Category: {category}
Summary: {summary}
Confidence: {confidence}

Respond ONLY in valid JSON:

{
  "title": "...",
  "summary": "...",
  "impact_score": 0-100
}
"""


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------

def _get_existing_proposal_source_ids(state: dict) -> set:
    source_ids = set()

    for candidate in state["proposals"]["kb_candidates"]:
        if "source_signal_id" in candidate:
            source_ids.add(candidate["source_signal_id"])

    for candidate in state["proposals"]["project_candidates"]:
        if "source_signal_id" in candidate:
            source_ids.add(candidate["source_signal_id"])

    return source_ids


def _generate_with_llm(signal: dict, llm_callable):
    prompt = PROPOSAL_PROMPT.format(
        category=signal.get("category"),
        summary=signal.get("summary"),
        confidence=signal.get("confidence"),
    )

    try:
        raw = llm_callable(prompt)
        parsed = json.loads(raw)

        return {
            "title": parsed.get("title", signal.get("summary", "")[:80]),
            "summary": parsed.get("summary", signal.get("summary", "")),
            "impact_score": parsed.get("impact_score", 50),
        }

    except Exception:
        # Safe fallback
        return {
            "title": signal.get("summary", "")[:80],
            "summary": signal.get("summary", ""),
            "impact_score": int(signal.get("confidence", 0.5) * 100),
        }


def _create_candidate(signal: dict, proposal_data: dict) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "source_signal_id": signal.get("id"),
        "title": proposal_data["title"],
        "summary": proposal_data["summary"],
        "impact_score": proposal_data["impact_score"],
        "confidence": signal.get("confidence", 0.5),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------------

def run_proposal_generation(llm_callable) -> dict:
    """
    Generate proposals from perception signals.

    LLM synthesizes title, summary, and impact_score.
    Duplicate-safe.
    """

    state = load_state()

    signals = state["perception"]["signals"]
    existing_source_ids = _get_existing_proposal_source_ids(state)

    kb_generated = 0
    project_generated = 0
    skipped_duplicate = 0
    skipped_unknown_category = 0

    for signal in signals:
        signal_id = signal.get("id")

        if signal_id in existing_source_ids:
            skipped_duplicate += 1
            continue

        category = signal.get("category", "").lower()

        if category not in ["discussion", "announcement"]:
            skipped_unknown_category += 1
            continue

        proposal_data = _generate_with_llm(signal, llm_callable)
        candidate = _create_candidate(signal, proposal_data)

        if category == "discussion":
            state["proposals"]["kb_candidates"].append(candidate)
            kb_generated += 1
        else:
            state["proposals"]["project_candidates"].append(candidate)
            project_generated += 1

    save_state(state)

    return {
        "status": "complete",
        "kb_candidates_generated": kb_generated,
        "project_candidates_generated": project_generated,
        "skipped_duplicate": skipped_duplicate,
        "skipped_unknown_category": skipped_unknown_category,
        "total_signals_processed": len(signals),
    }
