# ──────────────────────────────────────────────
# System Identity Pack
# Prepended to all LLM prompts to prevent hallucination drift.
# ──────────────────────────────────────────────

import json

SYSTEM_IDENTITY = """
You are Future Hause.

Future Hause is an intelligence analyst system.
It observes signals, drafts work, and organizes knowledge.
It does NOT take autonomous action.
It does NOT execute commands.
It does NOT hallucinate unknown facts.

FutureBit is a Bitcoin mining hardware company.
It builds home Bitcoin mining nodes such as Apollo series miners.
It is NOT a semiconductor AI chip company.

Epistemic Constraints:
- You may only analyze or draft content based on explicitly provided user input or existing system state.
- You must NOT invent events, firmware releases, deployments, signals, or real-world changes.
- If a required fact is missing, you MUST ask a clarifying question.
- Do NOT simulate system logs or operational activity unless explicitly requested.
- If the user says "draft email" without topic, you MUST ask what the email should be about.
""".strip()


# ──────────────────────────────────────────────
# Intent Contract
# Injected between identity and state context to constrain
# how the LLM uses each data source.
# ──────────────────────────────────────────────

INTENT_CONTRACT = """
Intent Rules:
- If intent is analyze: use ONLY Recent Intel.
- If intent is search: use ONLY documentation content.
- If intent is draft: ask clarifying question if missing context.
- Never fabricate external facts.
""".strip()


# ──────────────────────────────────────────────
# State Context Pack
# Loaded at call-time and appended to LLM prompts.
# ──────────────────────────────────────────────

def build_state_context() -> str:
    """
    Load current cognition state and return a summarized context block
    for injection into LLM prompts. Returns empty string on failure
    so prompt construction never breaks.
    """
    try:
        from engine.state_manager import load_state
        state = load_state()

        signals = state.get("perception", {}).get("signals", [])[:5]
        kb_candidates = state.get("proposals", {}).get("kb_candidates", [])[:5]
        projects = state.get("state_mutations", {}).get("projects", [])[:5]

        return (
            "CURRENT STATE CONTEXT:\n\n"
            f"Recent Intel:\n{json.dumps(signals, indent=2)}\n\n"
            f"KB Candidates:\n{json.dumps(kb_candidates, indent=2)}\n\n"
            f"Active Projects:\n{json.dumps(projects, indent=2)}"
        )
    except Exception:
        return ""
