from datetime import datetime, timezone

from flask import Flask, request, jsonify
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter
from engine.coach.run import run_coach_mode
from engine.state_manager import load_state, get_intel_signals, append_action, get_action_log
from engine.signal_extraction import run_signal_extraction
from engine.proposal_generator import run_proposal_generation

app = Flask(__name__)



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
    state = load_state()
    projects = state.get("state_mutations", {}).get("projects", [])
    # Also include project candidates from proposals
    project_candidates = state.get("proposals", {}).get("project_candidates", [])
    return jsonify({
        "schema_version": "1.0",
        "projects": projects + project_candidates
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

    # Step 3: Append action log entry
    now = datetime.now(timezone.utc).isoformat()
    action_entry = {
        "id": f"extraction-{now}",
        "action": "signal_extraction_cycle",
        "action_type": "signal_extraction_cycle",
        "timestamp": now,
        "rationale": f"Extracted {signals_created} signals, generated {proposals_created} proposals",
        "metadata": {
            "signals_created": signals_created,
            "proposals_created": proposals_created,
            "proposal_details": {
                "kb_candidates_generated": proposal_result["kb_candidates_generated"],
                "project_candidates_generated": proposal_result["project_candidates_generated"],
                "skipped_duplicate": proposal_result["skipped_duplicate"],
            },
        },
    }
    append_action(action_entry)

    # Step 4: Create snapshot (state after full cycle)
    final_state = load_state()
    snapshot = {
        "timestamp": now,
        "signals_count": len(final_state["perception"]["signals"]),
        "kb_candidates_count": len(final_state["proposals"]["kb_candidates"]),
        "project_candidates_count": len(final_state["proposals"]["project_candidates"]),
        "action_log_count": len(final_state["state_mutations"]["action_log"]),
    }

    # Step 5: Return updated authoritative state
    return jsonify({
        "status": "ok",
        "signals_created": signals_created,
        "proposals_created": proposals_created,
        "state": final_state,
        "snapshot": snapshot,
    })


if __name__ == "__main__":
    app.run(debug=True)
