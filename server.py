from flask import Flask, request, jsonify
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter
from engine.draft_work_log import create_draft, DRAFT_WORK_LOG

import uuid


from engine.coach.run import run_coach_mode

app = Flask(__name__, static_folder="ui", static_url_path="/ui")
@app.route("/")
def root():
    return app.send_static_file("index.html")





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

    result = run_coach_mode(
        draft_id=data["draft_id"],
        draft_text=data["draft_text"],
    )

    return jsonify(result)

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
    message = payload["message"]

    routing_decision = {
    "intent": "draft_request" if "draft" in message.lower() else "general"
}


    llm_response = call_llm(message)

    response_payload = {
        "response": llm_response
    }

    # 👇 THIS GOES HERE
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


if __name__ == "__main__":
    app.run(debug=True)
