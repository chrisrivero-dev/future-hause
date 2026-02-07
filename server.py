from flask import Flask, request, jsonify

from engine.review.run import run_review
from engine.coach.run import run_coach_mode

app = Flask(__name__)


# ─────────────────────────────────────────────
# Review API
# ─────────────────────────────────────────────
@app.route("/api/review", methods=["POST"])
def review():
    data = request.get_json(force=True)

    result = run_review(
        draft_id=data["draft_id"],
        draft_text=data["draft_text"],
        provider_name=data.get("provider", "ollama"),
        persist=data.get("persist", True),
        allow_claude=data.get("allow_claude", False),
        human_triggered=data.get("human_triggered", False),
    )

    return jsonify(result)


# ─────────────────────────────────────────────
# Coach API
# ─────────────────────────────────────────────
@app.route("/api/coach", methods=["POST"])
def coach():
    data = request.get_json(force=True)

    result = run_coach_mode(
        draft_id=data["draft_id"],
        draft_text=data["draft_text"],
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
