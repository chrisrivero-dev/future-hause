from flask import Flask, request, jsonify
from engine.review.ReviewEngineAdapter import ReviewEngineAdapter
from engine.coach.run import run_coach_mode

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


if __name__ == "__main__":
    app.run(debug=True)
