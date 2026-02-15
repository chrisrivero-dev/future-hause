from datetime import datetime, timezone
import uuid

from flask import Flask, request, jsonify
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter
from engine.coach.run import run_coach_mode
from engine.state_manager import load_state, save_state, get_intel_signals, append_action, get_action_log
from engine.signal_extraction import run_signal_extraction
from engine.proposal_generator import run_proposal_generation

app = Flask(__name__)


def auto_promote_projects() -> dict:
    """
    Automatically promote all project_candidates to state_mutations.projects.

    Rules:
    - Pass/fail promotion (no confidence thresholds)
    - Duplicates prevented by source_signal_id
    - Proposals cleared after promotion

    Returns:
        dict with promoted count and skipped_duplicate count.
    """
    state = load_state()

    candidates = state.get("proposals", {}).get("project_candidates", [])
    existing_projects = state.get("state_mutations", {}).get("projects", [])

    # Build set of existing source_signal_ids to prevent duplicates
    existing_source_ids = {
        p.get("source_signal_id") for p in existing_projects if p.get("source_signal_id")
    }

    promoted = 0
    skipped_duplicate = 0

    for candidate in candidates:
        source_signal_id = candidate.get("source_signal_id")

        # Skip if already promoted (duplicate prevention)
        if source_signal_id and source_signal_id in existing_source_ids:
            skipped_duplicate += 1
            continue

        # Create promoted project from candidate
        promoted_project = {
            "id": str(uuid.uuid4()),
            "source_signal_id": source_signal_id,
            "title": candidate.get("title"),
            "summary": candidate.get("summary"),
            "status": "active",
            "created_at": candidate.get("created_at"),
            "promoted_at": datetime.now(timezone.utc).isoformat(),
        }

        state["state_mutations"]["projects"].append(promoted_project)
        existing_source_ids.add(source_signal_id)
        promoted += 1

    # Clear proposals after promotion
    state["proposals"]["project_candidates"] = []

    save_state(state)

    return {
        "promoted": promoted,
        "skipped_duplicate": skipped_duplicate,
    }



# ─────────────────────────────────────────────
# Review API
# ─────────────────────────────────────────────
@app.route("/api/review", methods=["POST"])
def review():
    data = request.get_json(force=True)

    engine = ReviewEngineAdapter(
        provider_name=data.get("provider", "ollama"),
        persist=data.get("persist", True),
        allow_claude=data.get("allow_claude", False),
    )

    result = engine.run(
        draft_id=data["draft_id"],
        draft_text=data["draft_text"],
        human_triggered=data.get("human_triggered", False),
    )

    return jsonify(result)



# ─────────────────────────────────────────────
# Coach API
# ─────────────────────────────────────────────http://localhost:8080/ui/index.html

@app.route("/api/coach", methods=["POST"])
def coach():
    data = request.get_json(force=True)

    result = run_coach_mode(
        draft_id=data["draft_id"],
        draft_text=data["draft_text"],
    )

    return jsonify(result)


# ─────────────────────────────────────────────
# Intel API
# ─────────────────────────────────────────────
@app.route("/api/intel", methods=["GET"])
def get_intel():
    return jsonify({
        "schema_version": "1.0",
        "intel_events": get_intel_signals()
    })


# ─────────────────────────────────────────────
# Action Log API
# ─────────────────────────────────────────────
@app.route("/api/action", methods=["POST"])
def post_action():
    data = request.get_json(force=True)
    append_action(data)
    return jsonify({"status": "ok"})


@app.route("/api/action-log", methods=["GET"])
def get_action_log_endpoint():
    return jsonify({
        "schema_version": "1.0",
        "actions": get_action_log()
    })


# ─────────────────────────────────────────────
# KB Opportunities API
# ─────────────────────────────────────────────
@app.route("/api/kb", methods=["GET"])
def get_kb():
    state = load_state()
    candidates = state.get("proposals", {}).get("kb_candidates", [])
    return jsonify({
        "schema_version": "1.0",
        "opportunities": candidates
    })


# ─────────────────────────────────────────────
# Projects API
# ─────────────────────────────────────────────
@app.route("/api/projects", methods=["GET"])
def get_projects():
    """Return only promoted projects from state_mutations.projects."""
    state = load_state()
    projects = state.get("state_mutations", {}).get("projects", [])
    return jsonify({
        "schema_version": "1.0",
        "projects": projects
    })


# ─────────────────────────────────────────────
# Signal Extraction Lifecycle API
# ─────────────────────────────────────────────
@app.route("/api/run-signal-extraction", methods=["POST"])
def run_signal_extraction_endpoint():
    # Step 1: Run signal extraction
    extraction_result = run_signal_extraction()
    signals_created = extraction_result["signals_created"]

    # Step 2: Run proposal generation
    proposal_result = run_proposal_generation()
    proposals_created = (
        proposal_result["kb_candidates_generated"]
        + proposal_result["project_candidates_generated"]
    )

    # Step 3: Auto-promote project candidates (deterministic, pass/fail)
    promotion_result = auto_promote_projects()

    # Step 4: Append action log entry
    now = datetime.now(timezone.utc).isoformat()
    action_entry = {
        "id": f"extraction-{now}",
        "action": "signal_extraction_cycle",
        "action_type": "signal_extraction_cycle",
        "timestamp": now,
        "rationale": f"Extracted {signals_created} signals, generated {proposals_created} proposals, promoted {promotion_result['promoted']} projects",
        "metadata": {
            "signals_created": signals_created,
            "proposals_created": proposals_created,
            "proposal_details": {
                "kb_candidates_generated": proposal_result["kb_candidates_generated"],
                "project_candidates_generated": proposal_result["project_candidates_generated"],
                "skipped_duplicate": proposal_result["skipped_duplicate"],
            },
            "promotion_details": {
                "projects_promoted": promotion_result["promoted"],
                "skipped_duplicate": promotion_result["skipped_duplicate"],
            },
        },
    }
    append_action(action_entry)

    # Step 5: Create snapshot (state after full cycle)
    final_state = load_state()
    snapshot = {
        "timestamp": now,
        "signals_count": len(final_state["perception"]["signals"]),
        "kb_candidates_count": len(final_state["proposals"]["kb_candidates"]),
        "project_candidates_count": len(final_state["proposals"]["project_candidates"]),
        "projects_count": len(final_state["state_mutations"]["projects"]),
        "action_log_count": len(final_state["state_mutations"]["action_log"]),
    }

    # Step 6: Return updated authoritative state
    return jsonify({
        "status": "ok",
        "signals_created": signals_created,
        "proposals_created": proposals_created,
        "projects_promoted": promotion_result["promoted"],
        "state": final_state,
        "snapshot": snapshot,
    })


if __name__ == "__main__":
    app.run(debug=True)
