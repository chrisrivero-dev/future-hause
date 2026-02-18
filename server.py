from datetime import datetime, timezone

from flask import Flask, request, jsonify
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter
from engine.coach.run import run_coach_mode
from engine.state_manager import (
    load_state,
    get_intel_signals,
    append_action,
    get_action_log,
    get_focus,
    set_active_project,
    get_advisories,
    append_open_advisories,
    update_advisory_status,
)
from engine.signal_extraction import run_signal_extraction
from engine.proposal_generator import run_proposal_generation
from engine.promotion_engine import record_approval, run_promotion
from engine.advisory_generator import generate_advisories

app = Flask(__name__)


def auto_promote_projects() -> dict:
    """
    Promote all project_candidates through the proper 3-step lifecycle.

    Steps per candidate:
    1. record_approval (creates decision)
    2. run_promotion (creates mutation + action_log entry)

    Returns:
        dict with promoted count and skipped_duplicate count.
    """
    state = load_state()
    candidates = state.get("proposals", {}).get("project_candidates", [])

    approved = 0
    skipped = 0

    for candidate in candidates:
        candidate_id = candidate.get("id")
        if not candidate_id:
            skipped += 1
            continue
        try:
            record_approval(
                proposal_id=candidate_id,
                proposal_type="project_candidate",
                approved_by="system:auto_promote",
                rationale="Auto-promoted during extraction cycle",
            )
            approved += 1
        except ValueError:
            # Already approved or not found — skip
            skipped += 1

    # Run promotion for all newly approved decisions
    promotion_result = run_promotion(triggered_by="system:auto_promote")

    return {
        "promoted": promotion_result.get("project_promoted", 0),
        "skipped_duplicate": skipped,
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

    # Step 4: Generate advisories from promoted projects
    state = load_state()
    new_advisories = generate_advisories(state)
    if new_advisories:
        append_open_advisories(new_advisories)

    # Step 5: Log advisory generation
    now = datetime.now(timezone.utc).isoformat()
    if new_advisories:
        advisory_action = {
            "id": f"advisory-gen-{now}",
            "action": "advisory_generated",
            "action_type": "advisory_generated",
            "timestamp": now,
            "rationale": f"Generated {len(new_advisories)} advisories from promoted projects",
            "metadata": {
                "advisories_created": len(new_advisories),
            },
        }
        append_action(advisory_action)

    # Step 6: Append extraction cycle log entry
    action_entry = {
        "id": f"extraction-{now}",
        "action": "signal_extraction_cycle",
        "action_type": "signal_extraction_cycle",
        "timestamp": now,
        "rationale": f"Extracted {signals_created} signals, generated {proposals_created} proposals, promoted {promotion_result['promoted']} projects, created {len(new_advisories)} advisories",
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
            "advisory_details": {
                "advisories_created": len(new_advisories),
            },
        },
    }
    append_action(action_entry)

    # Step 7: Create snapshot (state after full cycle)
    final_state = load_state()
    advisories = final_state.get("advisories", {"open": [], "resolved": [], "dismissed": []})
    if isinstance(advisories, list):
        advisories = {"open": advisories, "resolved": [], "dismissed": []}
    snapshot = {
        "timestamp": now,
        "signals_count": len(final_state["perception"]["signals"]),
        "kb_candidates_count": len(final_state["proposals"]["kb_candidates"]),
        "project_candidates_count": len(final_state["proposals"]["project_candidates"]),
        "projects_count": len(final_state["state_mutations"]["projects"]),
        "action_log_count": len(final_state["state_mutations"]["action_log"]),
        "advisories_open_count": len(advisories.get("open", [])),
    }

    # Step 8: Return updated authoritative state
    return jsonify({
        "status": "ok",
        "signals_created": signals_created,
        "proposals_created": proposals_created,
        "projects_promoted": promotion_result["promoted"],
        "advisories_created": len(new_advisories),
        "state": final_state,
        "snapshot": snapshot,
    })


# ─────────────────────────────────────────────
# Focus API
# ─────────────────────────────────────────────
@app.route("/api/focus", methods=["GET"])
def get_focus_endpoint():
    """Get current project focus state."""
    focus = get_focus()
    return jsonify({
        "schema_version": "1.0",
        "focus": focus
    })


@app.route("/api/set-active-project", methods=["POST"])
def set_active_project_endpoint():
    """Set the active project for focus mode."""
    data = request.get_json(force=True)
    project_id = data.get("project_id")

    # Validate project_id exists if provided
    if project_id:
        state = load_state()
        projects = state.get("state_mutations", {}).get("projects", [])
        project_exists = any(p.get("id") == project_id for p in projects)
        if not project_exists:
            return jsonify({
                "status": "error",
                "message": f"Project with id '{project_id}' not found"
            }), 404

    # Set active project
    focus = set_active_project(project_id)

    # Log the action
    now = datetime.now(timezone.utc).isoformat()
    action_entry = {
        "id": f"focus-{now}",
        "action": "set_active_project",
        "action_type": "focus_change",
        "timestamp": now,
        "rationale": f"Set active project to: {project_id or 'None'}",
        "metadata": {
            "project_id": project_id,
        },
    }
    append_action(action_entry)

    return jsonify({
        "status": "ok",
        "focus": focus
    })


# ─────────────────────────────────────────────
# Advisories API
# ─────────────────────────────────────────────
@app.route("/api/advisories", methods=["GET"])
def get_advisories_endpoint():
    """Get all advisory suggestions in structured format."""
    advisories = get_advisories()
    return jsonify({
        "open": advisories.get("open", []),
        "resolved": advisories.get("resolved", []),
        "dismissed": advisories.get("dismissed", [])
    })


@app.route("/api/advisory-update", methods=["POST"])
def update_advisory_endpoint():
    """Update advisory status (resolve or dismiss)."""
    data = request.get_json(force=True)
    advisory_id = data.get("advisory_id")
    new_status = data.get("new_status")

    if not advisory_id:
        return jsonify({
            "status": "error",
            "message": "advisory_id is required"
        }), 400

    if new_status not in ["resolved", "dismissed"]:
        return jsonify({
            "status": "error",
            "message": "new_status must be 'resolved' or 'dismissed'"
        }), 400

    result = update_advisory_status(advisory_id, new_status)

    if result is None:
        return jsonify({
            "status": "error",
            "message": f"Advisory with id '{advisory_id}' not found"
        }), 404

    # Log the action
    now = datetime.now(timezone.utc).isoformat()
    action_entry = {
        "id": f"advisory-{new_status}-{now}",
        "action": f"advisory_{new_status}",
        "action_type": "advisory_action",
        "timestamp": now,
        "rationale": f"Advisory {advisory_id} marked as {new_status}",
        "metadata": {
            "advisory_id": advisory_id,
            "new_status": new_status,
        },
    }
    append_action(action_entry)

    # Return updated advisories
    advisories = get_advisories()
    return jsonify({
        "status": "ok",
        "open": advisories.get("open", []),
        "resolved": advisories.get("resolved", []),
        "dismissed": advisories.get("dismissed", [])
    })


if __name__ == "__main__":
    app.run(debug=True)
