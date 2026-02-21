from flask import Flask, request, jsonify
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter
from engine.draft_work_log import create_draft, DRAFT_WORK_LOG
from engine.state_manager import load_state, append_action, get_action_log, get_intel_signals
from engine.signal_extractor import run_signal_extraction
from engine.kb_draft_generator import run_kb_draft_generation
from engine.proposal_generator import run_proposal_generation
from engine.state_manager import get_kb_candidates, get_projects


import uuid
from flask import request
app = Flask(__name__, static_folder="ui", static_url_path="")

@app.route("/")
def root():
    return app.send_static_file("index.html")

@app.route("/api/ingest-reddit", methods=["POST"])
def ingest_reddit():
    from engine.state_manager import load_state, save_state
    import uuid
    from datetime import datetime

    data = request.json or {}

    state = load_state()

    state.setdefault("perception", {})
    state["perception"].setdefault("inputs", [])

    state["perception"]["inputs"].append({
        "id": str(uuid.uuid4()),
        "source": data.get("source", "reddit"),
        "content": data.get("content", ""),
        "created_at": datetime.utcnow().isoformat()
    })

    save_state(state)

    return {"status": "ok"}

from engine.coach.run import run_coach_mode
from engine.state_manager import get_intel_signals, append_action, get_action_log







# ─────────────────────────────────────────────
# Signal Extraction API
# ─────────────────────────────────────────────
@app.route("/api/run-signal-extraction", methods=["POST"])
def run_extraction():
    try:
        from engine.signal_extractor import run_signal_extraction
        from engine.proposal_generator import run_proposal_generation
        from engine.snapshot_manager import create_snapshot
        from engine.state_manager import load_state, save_state, append_action
        from engine.advisory_generator import generate_advisories
        from engine.llm_adapter import call_llm

        # 1️⃣ Run signal extraction
        new_signals = run_signal_extraction()

        # 2️⃣ Run proposal generation
        run_proposal_generation(call_llm)

        # 3️⃣ Load updated state
        state = load_state()

        project_candidates = state.get("proposals", {}).get("project_candidates", [])
        kb_candidates = state.get("proposals", {}).get("kb_candidates", [])

        state.setdefault("state_mutations", {}).setdefault("projects", [])
        state.setdefault("state_mutations", {}).setdefault("kb", [])

        # Prevent duplicate promotions
        existing_source_ids = {
            p.get("source_signal_id")
            for p in state["state_mutations"]["projects"]
        }

        promoted_projects = []
        promoted_kb = []

        for project in project_candidates:
            if project.get("source_signal_id") not in existing_source_ids:
                state["state_mutations"]["projects"].append(project)
                promoted_projects.append(project)

        for kb in kb_candidates:
            state["state_mutations"]["kb"].append(kb)
            promoted_kb.append(kb)

        # Clear proposals
        state["proposals"]["project_candidates"] = []
        state["proposals"]["kb_candidates"] = []

        # 4️⃣ Generate advisories
        new_advisories = generate_advisories(state)

        # 5️⃣ Append lifecycle log
        append_action({
            "action_type": "signal_extraction_cycle",
            "metadata": {
                "signals_created": len(new_signals),
                "projects_promoted": len(promoted_projects),
                "kb_promoted": len(promoted_kb),
                "advisories_created": len(new_advisories)
            }
        })

        # 6️⃣ Save state
        save_state(state)

        # 7️⃣ Snapshot
        snapshot = create_snapshot(
            trigger="signal_extraction_cycle",
            extra={
                "signals_created": len(new_signals),
                "projects_promoted": len(promoted_projects),
                "kb_promoted": len(promoted_kb),
                "advisories_created": len(new_advisories)
            }
        )

        return jsonify({
            "status": "ok",
            "signals_created": len(new_signals),
            "projects_promoted": len(promoted_projects),
            "kb_promoted": len(promoted_kb),
            "advisories_created": len(new_advisories),
            "snapshot": snapshot
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/kb-drafts", methods=["GET"])
def get_kb_drafts_api():
    from engine.state_manager import get_kb_drafts
    return jsonify(get_kb_drafts())


@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(load_state())

@app.route("/api/action", methods=["POST"])
def add_action():
    data = request.json
    append_action(data)
    return jsonify({"status": "ok"})

@app.route("/api/action-log", methods=["GET"])
def action_log():
    return jsonify({
        "schema_version": "1.0",
        "actions": get_action_log()
    })

@app.route("/api/kb", methods=["GET"])
def get_kb():
    return jsonify({
        "schema_version": "1.0",
        "kb_opportunities": get_kb_candidates()
    })

@app.route("/api/projects", methods=["GET"])
def get_projects_api():
    return jsonify({
        "schema_version": "1.0",
        "projects": get_projects()
    })
def get_kb_candidates():
    state = load_state()
    return state["proposals"]["kb_candidates"]

def get_projects():
    state = load_state()
    return state["state_mutations"]["projects"]

# ─────────────────────────────────────────────
# Proposal Generation API
# ─────────────────────────────────────────────
@app.route("/api/run-proposal-generation", methods=["POST"])
def run_proposals():
    try:
        from engine.proposal_generator import run_proposal_generation
        from engine.llm_adapter import generate_text  # adjust if needed

        from engine.llm_adapter import call_llm

        result = run_proposal_generation(call_llm)


        from engine.snapshot_manager import create_snapshot
        snapshot = create_snapshot("proposal_generation")

        result["snapshot"] = snapshot
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



# ─────────────────────────────────────────────
# KB Draft Generation API
# ─────────────────────────────────────────────
@app.route("/api/run-kb-draft-generation", methods=["POST"])
def run_kb_generation():
    try:
        result = run_kb_draft_generation(call_llm)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


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
@app.route("/api/draft/<draft_id>", methods=["GET"])
def get_draft(draft_id):
    draft = DRAFT_WORK_LOG.get(draft_id)
    if not draft:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "draft_id": draft.draft_id,
        "body": draft.content["body"],
        "format": draft.content["format"],
        "status": draft.status,
        "tags": draft.tags,
    })



# ─────────────────────────────────────────────
# Coach API
# http://localhost:8080/ui/index.html

@app.route("/api/coach", methods=["POST"])
def coach():
    data = request.get_json(force=True)

    draft_id = data.get("draft_id")
    draft_text = data.get("draft_text")

    # If draft exists → use review engine
    if draft_id and draft_id in DRAFT_WORK_LOG:
        engine = ReviewEngineAdapter(provider_name="ollama")
        result = engine.run(
            draft_id=draft_id,
            draft_text=draft_text,
            human_triggered=True,
        )
        return jsonify(result)

    # Otherwise → run direct coach LLM call
    coach_prompt = f"""
You are a professional writing coach.
Improve clarity, tone, and structure.
Do not invent new facts.

Text:
{draft_text}
"""

    response = call_llm(coach_prompt)

    return jsonify({
        "mode": "coach",
        "content": response
    })


import requests

def call_llm(message: str) -> str:
    """
    Simple Ollama call.
    Can later swap to Claude, OpenAI, etc.
    """
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "llama3.1:latest",
                "prompt": message,
                "stream": False
            },
            timeout=60,
        )

        data = response.json()
        return data.get("response", "")

    except Exception as e:
        return f"[LLM ERROR] {str(e)}"



@app.route("/api/send", methods=["POST"])
def send():
    payload = request.get_json(force=True)
    message = payload["message"].strip()
    mode = payload.get("mode")

    if mode == "coach":
        coach_prompt = f"""
You are a professional writing coach.
Improve clarity, tone, and structure.
Do not invent new facts.

Text:
{message}
""".strip()

        response = call_llm(coach_prompt)
        return jsonify({"response": response})

    routing_decision = {
        "intent": "draft_request" if "draft" in message.lower() else "general"
    }


    SYSTEM_IDENTITY = """
You are Future Hause.

Role:
- You are an intelligence analyst + drafting assistant.
- You observe signals, draft work entries, and organize knowledge.
- You do NOT take autonomous action or execute commands.

Reality / Safety:
- Bitcoin mining is legal activity in many jurisdictions, including the U.S.
- Do NOT claim bitcoin mining is illegal.
- Only refuse if the user asks for explicitly illegal wrongdoing (fraud, hacking, violence, etc.).
- Writing normal business emails is allowed.

Company grounding:
- FutureBit is a Bitcoin mining hardware company.
- It builds home Bitcoin mining nodes (Apollo series).
- It is NOT an AI semiconductor company.

Epistemic constraints:
- Use only the user’s message + existing system state.
- Do NOT invent deployments, firmware releases, outages, or system logs.
- If the user provides a clear topic, draft the email using reasonable professional defaults.
- Only ask clarifying questions if the request is ambiguous or unsafe.

""".strip()

    final_prompt = f"""
{SYSTEM_IDENTITY}

User Message:
{message}
""".strip()

    llm_response = call_llm(final_prompt)

    response_payload = {
        "response": llm_response
    }

    if routing_decision["intent"] == "draft_request":
        draft = create_draft(
            message_id=str(uuid.uuid4()),
            router_intent="draft_request",
            body=llm_response,
            format="text",
            created_by="agent",
            tags=[],
        )

        response_payload["draft_id"] = draft.draft_id

    return jsonify(response_payload)



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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True, use_reloader=False)
