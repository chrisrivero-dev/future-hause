# ──────────────────────────────────────────────
# Signal Analyzer
# Analyzes signals using local LLM (Ollama) to generate
# structured intelligence outputs.
# ──────────────────────────────────────────────

import json
import requests
from datetime import datetime, timezone
from typing import TypedDict

from engine.system_identity import SYSTEM_IDENTITY
from engine.state_manager import get_intel_signals, append_action

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2:3b-instruct-q4_1"
TIMEOUT = 120


class KBOpportunity(TypedDict):
    title: str
    reason: str


class Project(TypedDict):
    title: str
    goal: str


class Recommendation(TypedDict):
    title: str
    summary: str


class AnalysisResult(TypedDict):
    kb_opportunities: list[KBOpportunity]
    projects: list[Project]
    recommendations: list[Recommendation]
    analyzed_at: str
    signal_count: int


def build_analysis_prompt(signals: list[dict]) -> str:
    """
    Build a prompt for the LLM to analyze signals and generate
    structured intelligence outputs.
    """
    signals_json = json.dumps(signals, indent=2)

    prompt = f"""{SYSTEM_IDENTITY}

You are analyzing intelligence signals for FutureBit, a Bitcoin mining hardware company.

TASK: Analyze the following signals and generate actionable intelligence outputs.

SIGNALS:
{signals_json}

Based on these signals, generate a JSON response with exactly this structure:
{{
  "kb_opportunities": [
    {{"title": "Short title for KB article", "reason": "Why this is needed based on the signal"}}
  ],
  "projects": [
    {{"title": "Project name", "goal": "What this project should accomplish"}}
  ],
  "recommendations": [
    {{"title": "Action title", "summary": "Brief summary of recommended action"}}
  ]
}}

RULES:
1. Generate 1-3 items per category based on signal relevance
2. KB opportunities should address documentation gaps or user education needs
3. Projects should be concrete initiatives that could help FutureBit
4. Recommendations should be immediate actionable suggestions
5. Be specific and tie outputs to the actual signal content
6. If a signal is not actionable, you may generate fewer items
7. Output ONLY valid JSON, no markdown, no explanation

JSON RESPONSE:"""

    return prompt


def parse_llm_response(response_text: str) -> dict:
    """
    Parse the LLM response, handling potential formatting issues.
    """
    # Clean up the response - strip whitespace and find JSON
    text = response_text.strip()

    # Try to find JSON block if wrapped in markdown
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()

    # Find the JSON object boundaries
    start_idx = text.find("{")
    end_idx = text.rfind("}") + 1

    if start_idx >= 0 and end_idx > start_idx:
        text = text[start_idx:end_idx]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Return empty structure on parse failure
        return {
            "kb_opportunities": [],
            "projects": [],
            "recommendations": [],
        }


def analyze_signals(signals: list[dict] | None = None) -> AnalysisResult:
    """
    Analyze signals using local Ollama LLM and generate structured outputs.

    Args:
        signals: Optional list of signals. If None, fetches from state.

    Returns:
        AnalysisResult with kb_opportunities, projects, and recommendations.
    """
    # Get signals if not provided
    if signals is None:
        signals = get_intel_signals()

    now = datetime.now(timezone.utc).isoformat()

    # Handle empty signals case
    if not signals:
        return {
            "kb_opportunities": [],
            "projects": [],
            "recommendations": [],
            "analyzed_at": now,
            "signal_count": 0,
        }

    # Build prompt
    prompt = build_analysis_prompt(signals)

    # Call Ollama
    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()

        response_text = response.json().get("response", "")
        parsed = parse_llm_response(response_text)

        # Validate and normalize the response structure with trust layer fields
        kb_opps = []
        for opp in parsed.get("kb_opportunities", [])[:5]:
            kb_opps.append({
                **opp,
                "source": "llm_analysis",
                "timestamp": now,
                "freshness": "current",
                "confidence": 0.75,
            })

        projects = []
        for proj in parsed.get("projects", [])[:5]:
            projects.append({
                **proj,
                "source": "llm_analysis",
                "timestamp": now,
                "freshness": "current",
                "confidence": 0.75,
            })

        recommendations = []
        for rec in parsed.get("recommendations", [])[:5]:
            recommendations.append({
                **rec,
                "source": "llm_analysis",
                "timestamp": now,
                "freshness": "current",
                "confidence": 0.75,
            })

        result: AnalysisResult = {
            "kb_opportunities": kb_opps,
            "projects": projects,
            "recommendations": recommendations,
            "analyzed_at": now,
            "signal_count": len(signals),
        }

        # Log the analysis action
        action_entry = {
            "id": f"signal-analysis-{now}",
            "action": "signal_analysis",
            "action_type": "llm_analysis",
            "timestamp": now,
            "rationale": f"Analyzed {len(signals)} signals, generated {len(result['kb_opportunities'])} KB opportunities, {len(result['projects'])} projects, {len(result['recommendations'])} recommendations",
            "metadata": {
                "signal_count": len(signals),
                "kb_opportunities_count": len(result["kb_opportunities"]),
                "projects_count": len(result["projects"]),
                "recommendations_count": len(result["recommendations"]),
            },
        }
        append_action(action_entry)

        return result

    except requests.exceptions.ConnectionError:
        # Ollama not running - return empty result
        return {
            "kb_opportunities": [],
            "projects": [],
            "recommendations": [],
            "analyzed_at": now,
            "signal_count": len(signals),
            "error": "Ollama not available - ensure Ollama is running locally",
        }
    except requests.exceptions.Timeout:
        return {
            "kb_opportunities": [],
            "projects": [],
            "recommendations": [],
            "analyzed_at": now,
            "signal_count": len(signals),
            "error": "Analysis timed out",
        }
    except Exception as e:
        return {
            "kb_opportunities": [],
            "projects": [],
            "recommendations": [],
            "analyzed_at": now,
            "signal_count": len(signals),
            "error": str(e),
        }
