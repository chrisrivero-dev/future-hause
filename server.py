from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, send_file
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter
from engine.coach.run import run_coach_mode
from engine.state_manager import (
    load_state,
    save_state_validated,
    get_intel_signals,
    append_signal,
    append_action,
    get_action_log,
    get_focus,
    set_active_project,
    get_advisories,
    append_open_advisories,
    update_advisory_status,
    update_kb_candidate_status,
    get_kb_candidates,
    create_user_project,
    update_user_project,
    delete_user_project,
    set_advisory_investigating,
    get_work_log,
)
from engine.signal_extraction import run_signal_extraction
from engine.ingest import run_live_ingest, get_ingestion_status
from engine.proposal_generator import run_proposal_generation
from engine.promotion_engine import record_approval, run_promotion
from engine.advisory_generator import generate_advisories
from engine.kb_draft_generator import scaffold_from_signal
from engine.signal_analyzer import analyze_signals
import requests

app = Flask(__name__)

# ─────────────────────────────────────────────
# Chat Context Assembly Helper
# ─────────────────────────────────────────────
def _assemble_chat_context() -> dict:
    """
    Assemble context for chat endpoint.
    Returns last 5 signals, KB opportunities, open advisories, and active project focus.
    """
    state = load_state()

    # Last 5 signals
    signals = state.get("perception", {}).get("signals", [])
    recent_signals = signals[-5:] if signals else []

    # KB opportunities (candidates)
    kb = state.get("proposals", {}).get("kb_candidates", [])

    # Open advisories
    advisories_data = state.get("advisories", {})
    if isinstance(advisories_data, list):
        advisories_data = {"open": advisories_data, "resolved": [], "dismissed": []}
    open_advisories = advisories_data.get("open", [])

    # Active project focus
    focus = state.get("focus", {})
    active_project_id = focus.get("active_project_id")
    active_project = None
    if active_project_id:
        projects = state.get("state_mutations", {}).get("projects", [])
        for p in projects:
            if p.get("id") == active_project_id:
                active_project = p
                break

    return {
        "signals": recent_signals,
        "kb": kb,
        "advisories": open_advisories,
        "active_project": active_project,
    }

# UI directory path
UI_DIR = Path(__file__).parent / "ui"


# ─────────────────────────────────────────────
# UI Static File Serving
# ─────────────────────────────────────────────
@app.route("/")
def serve_index():
    """Serve the main dashboard page."""
    return send_file(UI_DIR / "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    """Serve static files from ui/ directory."""
    return send_from_directory(UI_DIR, filename)


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
    engine = ReviewEngineAdapter()
    result = engine.run(
        draft_id=data.get("draft_id"),
        draft_text=data.get("draft_text", ""),
        human_triggered=data.get("human_triggered", False),
        provider_name=data.get("provider", "ollama"),
        persist=data.get("persist", True),
        allow_claude=data.get("allow_claude", False),
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
# Chat API
# ─────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Conversational endpoint for querying FutureHause context.

    Input: {"message": string}
    Output: {"success": true, "response": string, "confidence": number}
    """
    data = request.get_json(force=True)
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "success": False,
            "error": "message field is required",
            "response": None,
            "confidence": 0.0,
        }), 400

    # Assemble context
    ctx = _assemble_chat_context()

    # Format context for prompt
    signals_text = "\n".join(
        f"- [{s.get('id', 'unknown')}] {s.get('title', s.get('text', '')[:100])}"
        for s in ctx["signals"]
    ) or "No recent signals."

    kb_text = "\n".join(
        f"- [{k.get('id', 'unknown')}] {k.get('title', 'Untitled')}"
        for k in ctx["kb"][:10]
    ) or "No KB opportunities."

    advisories_text = "\n".join(
        f"- [{a.get('id', 'unknown')}] {a.get('title', 'Untitled')} (priority: {a.get('priority', 'unknown')})"
        for a in ctx["advisories"]
    ) or "No open advisories."

    project_text = "None"
    if ctx["active_project"]:
        p = ctx["active_project"]
        project_text = f"{p.get('title', 'Untitled')} (status: {p.get('status', 'unknown')})"

    prompt = f"""User question:
{message}

Context:
Signals:
{signals_text}

KB:
{kb_text}

Advisories:
{advisories_text}

Active Project Focus:
{project_text}

Instructions:
- Answer the question
- Suggest relevant KB articles if applicable
- Suggest actions or projects if relevant
- Keep response concise and actionable"""

    # Call Ollama
    OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
    MODEL = "llama3.2:3b-instruct-q4_1"

    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Ollama HTTP {r.status_code}")

        response_text = r.json().get("response", "").strip()
        confidence = 0.7 if response_text else 0.0

        return jsonify({
            "success": True,
            "response": response_text,
            "confidence": confidence,
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "response": None,
            "confidence": 0.0,
        }), 500


# ─────────────────────────────────────────────
# Intel API
# ─────────────────────────────────────────────
@app.route("/api/intel", methods=["GET"])
def get_intel():
    return jsonify({
        "schema_version": "1.0",
        "intel_events": get_intel_signals()
    })


@app.route("/api/signals", methods=["GET"])
def get_signals():
    """Return signals in format expected by dashboard."""
    return jsonify({
        "schema_version": "1.0",
        "signals": get_intel_signals()
    })


@app.route("/api/signals", methods=["POST"])
def post_signal():
    """
    Create a new signal and trigger downstream processing.

    Input: {"text": string}
    Output: {"success": true, "signal_id": string}
    """
    data = request.get_json(force=True)

    if not data or not data.get("text"):
        return jsonify({
            "success": False,
            "error": "text field is required"
        }), 400

    # Create and persist signal
    signal = append_signal(data)
    signal_id = signal["id"]

    # Trigger downstream processing pipeline
    now = datetime.now(timezone.utc).isoformat()

    # Step 1: Run proposal generation (creates kb_candidates/project_candidates)
    proposal_result = run_proposal_generation()

    # Step 2: Auto-promote project candidates
    promotion_result = auto_promote_projects()

    # Step 3: Generate advisories from promoted projects
    state = load_state()
    new_advisories = generate_advisories(state)
    if new_advisories:
        append_open_advisories(new_advisories)

    # Step 4: Log the signal creation action
    action_entry = {
        "id": f"signal-created-{now}",
        "action": "signal_created",
        "action_type": "signal_created",
        "timestamp": now,
        "rationale": f"Signal created via API: {signal.get('title', '')[:50]}",
        "metadata": {
            "signal_id": signal_id,
            "proposals_generated": proposal_result.get("kb_candidates_generated", 0)
                + proposal_result.get("project_candidates_generated", 0),
            "projects_promoted": promotion_result.get("promoted", 0),
            "advisories_created": len(new_advisories),
        },
    }
    append_action(action_entry)

    return jsonify({
        "success": True,
        "signal_id": signal_id
    })


# ─────────────────────────────────────────────
# Signal Analysis API
# ─────────────────────────────────────────────
@app.route("/api/analyze-signals", methods=["POST"])
def analyze_signals_endpoint():
    """
    Analyze current signals using local LLM (Ollama) and generate
    structured intelligence outputs.

    Returns:
        JSON with kb_opportunities, projects, and recommendations.
    """
    try:
        result = analyze_signals()
        return jsonify({
            "status": "ok",
            **result,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "kb_opportunities": [],
            "projects": [],
            "recommendations": [],
        }), 500


# ─────────────────────────────────────────────
# Ingestion API
# ─────────────────────────────────────────────
@app.route("/api/ingest/status", methods=["GET"])
def ingest_status():
    """Get ingestion status and source availability."""
    status = get_ingestion_status()
    return jsonify(status)


@app.route("/api/ingest", methods=["POST"])
def run_ingest():
    """
    Run live ingestion from all available sources.

    This endpoint fetches data from Reddit, Twitter, and News feeds,
    normalizes it into the intel schema, and persists to state.
    """
    try:
        result = run_live_ingest()
        return jsonify({
            "status": "ok",
            "result": result,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


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
        "kb_opportunities": candidates
    })


@app.route("/api/kb-drafts", methods=["GET"])
def get_kb_drafts():
    """Return KB candidates that have drafts, organized by status."""
    state = load_state()
    candidates = state.get("proposals", {}).get("kb_candidates", [])

    # Filter to only candidates with drafts, organize by status
    active = []
    archived = []
    scaffolded = []

    for candidate in candidates:
        if not candidate.get("draft"):
            continue

        status = candidate.get("status", "active")
        if status == "archived":
            archived.append(candidate)
        elif status == "scaffolded":
            scaffolded.append(candidate)
        else:
            active.append(candidate)

    return jsonify({
        "schema_version": "1.0",
        "active": active,
        "archived": archived,
        "scaffolded": scaffolded,
    })


@app.route("/api/kb-drafts/new", methods=["POST"])
def create_kb_draft():
    """Create a scaffolded KB proposal from a signal."""
    data = request.get_json(force=True)

    # Validate signal data
    if not data:
        return jsonify({"status": "error", "message": "Request body required"}), 400

    signal_id = data.get("id")
    if not signal_id:
        return jsonify({"status": "error", "message": "Signal id required"}), 400

    # Check for duplicate (signal already scaffolded)
    state = load_state()
    existing_ids = {
        c.get("source_signal_id")
        for c in state.get("proposals", {}).get("kb_candidates", [])
    }
    if signal_id in existing_ids:
        return jsonify({
            "status": "error",
            "message": f"Signal {signal_id} already has a KB proposal"
        }), 409

    # Create scaffolded proposal
    proposal = scaffold_from_signal(data)

    # Append to kb_candidates
    state["proposals"]["kb_candidates"].append(proposal)
    save_state_validated(state)

    # Return enforced KB draft structure
    return jsonify({
        "status": "ok",
        "proposal": proposal,
        "title": proposal.get("title", ""),
        "summary": proposal.get("summary", ""),
        "steps": [s.get("content", "") for s in proposal.get("sections", []) if s.get("heading") == "Solution / Fix"] or [""],
        "source_reference": proposal.get("source_signal_id", ""),
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


@app.route("/api/set-focus", methods=["POST"])
def set_focus_endpoint():
    """Set focus state (alias for set-active-project)."""
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

    focus = set_active_project(project_id)

    now = datetime.now(timezone.utc).isoformat()
    append_action({
        "id": f"focus-{now}",
        "action": "set_focus",
        "action_type": "focus_change",
        "timestamp": now,
        "rationale": f"Focus set to: {project_id or 'None'}",
        "metadata": {"project_id": project_id},
    })

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


# ─────────────────────────────────────────────
# KB Actions API
# ─────────────────────────────────────────────
@app.route("/api/kb/queue", methods=["POST"])
def save_kb_to_queue():
    """Save KB candidate to queue for later processing."""
    data = request.get_json(force=True)
    candidate_id = data.get("candidate_id")

    if not candidate_id:
        return jsonify({"status": "error", "message": "candidate_id required"}), 400

    result = update_kb_candidate_status(candidate_id, "queued")
    if not result:
        return jsonify({"status": "error", "message": "Candidate not found"}), 404

    # Log the action
    now = datetime.now(timezone.utc).isoformat()
    append_action({
        "id": f"kb-queue-{now}",
        "action": "kb_queued",
        "action_type": "kb_draft_saved",
        "timestamp": now,
        "rationale": f"KB candidate {candidate_id} saved to queue",
        "metadata": {"candidate_id": candidate_id},
    })

    return jsonify({"status": "ok", "candidate": result})


@app.route("/api/kb/dismiss", methods=["POST"])
def dismiss_kb_candidate():
    """Dismiss a KB candidate."""
    data = request.get_json(force=True)
    candidate_id = data.get("candidate_id")

    if not candidate_id:
        return jsonify({"status": "error", "message": "candidate_id required"}), 400

    result = update_kb_candidate_status(candidate_id, "dismissed")
    if not result:
        return jsonify({"status": "error", "message": "Candidate not found"}), 404

    # Log the action
    now = datetime.now(timezone.utc).isoformat()
    append_action({
        "id": f"kb-dismiss-{now}",
        "action": "kb_dismissed",
        "action_type": "kb_dismissed",
        "timestamp": now,
        "rationale": f"KB candidate {candidate_id} dismissed",
        "metadata": {"candidate_id": candidate_id},
    })

    return jsonify({"status": "ok", "candidate": result})


# ─────────────────────────────────────────────
# User Projects API
# ─────────────────────────────────────────────
@app.route("/api/projects/create", methods=["POST"])
def create_project():
    """Create a new user-defined project."""
    data = request.get_json(force=True)

    if not data.get("title"):
        return jsonify({"status": "error", "message": "title required"}), 400

    project = create_user_project(data)

    # Log the action
    now = datetime.now(timezone.utc).isoformat()
    append_action({
        "id": f"project-create-{now}",
        "action": "project_created",
        "action_type": "project_created",
        "timestamp": now,
        "rationale": f"User created project: {project['title']}",
        "metadata": {"project_id": project["id"]},
    })

    return jsonify({"status": "ok", "project": project})


@app.route("/api/projects/update", methods=["POST"])
def update_project():
    """Update an existing project."""
    data = request.get_json(force=True)
    project_id = data.get("project_id")

    if not project_id:
        return jsonify({"status": "error", "message": "project_id required"}), 400

    result = update_user_project(project_id, data)
    if not result:
        return jsonify({"status": "error", "message": "Project not found"}), 404

    return jsonify({"status": "ok", "project": result})


@app.route("/api/projects/delete", methods=["POST"])
def delete_project():
    """Delete a user-defined project."""
    data = request.get_json(force=True)
    project_id = data.get("project_id")

    if not project_id:
        return jsonify({"status": "error", "message": "project_id required"}), 400

    result = delete_user_project(project_id)
    if not result:
        return jsonify({"status": "error", "message": "Project not found or cannot be deleted"}), 404

    # Log the action
    now = datetime.now(timezone.utc).isoformat()
    append_action({
        "id": f"project-delete-{now}",
        "action": "project_deleted",
        "action_type": "project_deleted",
        "timestamp": now,
        "rationale": f"User deleted project: {project_id}",
        "metadata": {"project_id": project_id},
    })

    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────
# Advisory Investigate API
# ─────────────────────────────────────────────
@app.route("/api/advisory-investigate", methods=["POST"])
def investigate_advisory():
    """Mark an advisory as being investigated and attach related signals."""
    data = request.get_json(force=True)
    advisory_id = data.get("advisory_id")

    if not advisory_id:
        return jsonify({"status": "error", "message": "advisory_id required"}), 400

    result = set_advisory_investigating(advisory_id)
    if not result:
        return jsonify({"status": "error", "message": "Advisory not found"}), 404

    # Attach related signals based on project_id or source_signal_id
    state = load_state()
    signals = state.get("perception", {}).get("signals", [])
    related_signals = []
    project_id = result.get("project_id")
    source_signal_id = result.get("source_signal_id")

    for sig in signals:
        if project_id and sig.get("project_id") == project_id:
            related_signals.append(sig)
        elif source_signal_id and sig.get("id") == source_signal_id:
            related_signals.append(sig)

    # Log the action with related signals
    now = datetime.now(timezone.utc).isoformat()
    append_action({
        "id": f"advisory-investigate-{now}",
        "action": "advisory_investigating",
        "action_type": "advisory_investigating",
        "timestamp": now,
        "rationale": f"Started investigation of advisory: {advisory_id}",
        "metadata": {
            "advisory_id": advisory_id,
            "advisory_title": result.get("title", "Unknown"),
            "related_signal_ids": [s.get("id") for s in related_signals],
            "related_signal_count": len(related_signals),
        },
    })

    # Return updated advisories with investigation details
    advisories = get_advisories()
    return jsonify({
        "status": "ok",
        "advisory": result,
        "related_signals": related_signals,
        "investigation_details": {
            "started_at": result.get("investigation_started_at"),
            "related_signal_count": len(related_signals),
        },
        "open": advisories.get("open", []),
        "resolved": advisories.get("resolved", []),
        "dismissed": advisories.get("dismissed", []),
    })


# ─────────────────────────────────────────────
# Work Log API
# ─────────────────────────────────────────────
@app.route("/api/work-log", methods=["GET"])
def get_work_log_endpoint():
    """Get the draft work log (auto-populated from actions)."""
    work_entries = get_work_log()
    return jsonify({
        "schema_version": "1.0",
        "entries": work_entries,
    })


if __name__ == "__main__":
    app.run(debug=True)
