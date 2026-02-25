"""
KB Draft Generator for Future Hause

Generates structured KB article drafts from kb_candidates using an LLM.
Each draft follows a fixed JSON schema for downstream consumption.

Deterministic fallback if LLM response is unparseable.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Callable

from engine.state_manager import load_state, save_state_validated


KB_DRAFT_PROMPT = """\
You are a technical knowledge base writer.
Given the following support topic, produce a structured KB article as valid JSON.

Topic title: {title}
Topic summary: {summary}

Return ONLY a single JSON object matching this exact schema. No markdown. No commentary. No explanation. No code fences.

{{
  "title": "string — concise article title",
  "problem": "string — clear problem statement",
  "affected_versions": ["list of affected product versions, or empty"],
  "symptoms": ["list of observable symptoms"],
  "root_cause": "string — underlying cause",
  "solution_steps": ["ordered list of resolution steps"],
  "preventative_notes": "string — how to prevent recurrence",
  "related_articles": ["list of related article titles, or empty"],
  "source_signal_ids": {source_signal_ids},
  "confidence": 0.8
}}

Return valid JSON only."""


def _build_prompt(candidate: dict) -> str:
    """Build the LLM prompt for a given KB candidate."""
    source_ids = []
    source_signal_id = candidate.get("source_signal_id")
    if source_signal_id:
        source_ids.append(source_signal_id)

    return KB_DRAFT_PROMPT.format(
        title=candidate.get("title", "Untitled"),
        summary=candidate.get("summary", ""),
        source_signal_ids=json.dumps(source_ids),
    )


def _parse_llm_response(raw: str, candidate: dict) -> dict:
    """Parse LLM response as JSON. Return structured fallback on failure."""
    # Strip common wrapper artifacts
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        parsed = json.loads(text)
        # Validate required keys exist
        required = ("title", "problem", "solution_steps")
        if all(k in parsed for k in required):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: minimal structured template
    return _build_fallback(candidate)


def _build_fallback(candidate: dict) -> dict:
    """Build a minimal structured draft from candidate metadata."""
    source_ids = []
    source_signal_id = candidate.get("source_signal_id")
    if source_signal_id:
        source_ids.append(source_signal_id)

    return {
        "title": candidate.get("title", "Untitled"),
        "problem": candidate.get("summary", ""),
        "affected_versions": [],
        "symptoms": [],
        "root_cause": "",
        "solution_steps": [],
        "preventative_notes": "",
        "related_articles": [],
        "source_signal_ids": source_ids,
        "confidence": 0.5,
    }


def run_kb_draft_generation(call_llm: Callable[[str], str]) -> dict:
    """
    Generate structured KB drafts for all undrafted kb_candidates.

    Args:
        call_llm: Callable that takes a prompt string and returns a response string.

    Returns:
        dict with counts of drafts generated and skipped.
    """
    state = load_state()

    candidates = state.get("proposals", {}).get("kb_candidates", [])

    # Debug logging
    print(f"[kb_draft_generator] kb_candidates found: {len(candidates)}")

    # Build set of already-drafted candidate IDs to prevent duplicates
    existing_draft_ids = set()
    for candidate in candidates:
        if candidate.get("draft"):
            existing_draft_ids.add(candidate.get("id"))

    generated = 0
    skipped_duplicate = 0
    skipped_error = 0

    for candidate in candidates:
        candidate_id = candidate.get("id")

        # Skip if already drafted
        if candidate_id in existing_draft_ids:
            skipped_duplicate += 1
            continue

        prompt = _build_prompt(candidate)

        try:
            raw_response = call_llm(prompt)
            draft = _parse_llm_response(raw_response, candidate)
        except Exception:
            draft = _build_fallback(candidate)
            skipped_error += 1

        # Attach draft to the candidate
        candidate["draft"] = draft
        candidate["draft_id"] = str(uuid.uuid4())
        candidate["drafted_at"] = datetime.now(timezone.utc).isoformat()
        generated += 1

    # Debug logging
    print(f"[kb_draft_generator] drafts generated: {generated}")

    # Persist updated state
    save_state_validated(state)

    return {
        "status": "complete",
        "drafts_generated": generated,
        "skipped_duplicate": skipped_duplicate,
        "skipped_error": skipped_error,
        "total_candidates": len(candidates),
    }
