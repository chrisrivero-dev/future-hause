# Model Usage Mapping — Work vs Review Zones

*(Cost-aware, governance-aligned, no new behavior)*

---

## Purpose

This document defines how **LLMs may be swapped or selected** across environments
(home vs work) while preserving Future Hause’s governance model.

It explicitly allows:
- Free/local models at home
- Paid API models at work (e.g. ChatGPT)
- Seamless substitution without changing system rules

This document defines **policy**, not implementation.

---

## Key Principle: Models Are Replaceable, Rules Are Not

Future Hause governance is enforced by:
- Routing rules
- Review mechanics
- Draft lifecycle
- Human decision points

**Models are interchangeable execution engines** beneath these rules.

Switching models must never:
- Change authority
- Enable execution
- Bypass review
- Alter response type

---

## Zone-Based Model Usage

### Work Zone (Drafting & Exploration)

Characteristics:
- Creative
- Low risk
- Advisory only
- High tolerance for verbosity

Allowed Model Types:
- Local open-source LLMs
- Paid API LLMs
- Mixed usage depending on environment

Recommended (Home / Free):
- Mistral
- Qwen
- LLaMA-family models
- Any local Ollama-compatible model

Recommended (Work / API):
- ChatGPT (any reasoning-capable tier)
- Claude (if available)
- Gemini (optional)

Constraints:
- Draft output only
- No execution language
- No implied actions

---

### Review Zone (Flagging & Evaluation)

Characteristics:
- Constrained
- Non-creative
- Read-only
- High precision preferred

Allowed Model Types:
- Smaller local models
- Paid API models if needed

Recommended (Home / Free):
- Phi
- Gemma
- Smaller Mistral variants
- Rule-based scripts for deterministic checks

Recommended (Work / API):
- ChatGPT (small/cheap tier preferred)
- Any model capable of structured analysis

Constraints:
- Flag only
- No edits
- No approvals
- No execution

---

### Execution Zone

Characteristics:
- System mutation
- Permanent effects

Allowed Model Types:
- None

Execution is **human-only**.

Models may not:
- Trigger execution
- Simulate execution
- Imply execution

---

## Environment Swapping Policy

Environment differences (home vs work) may affect:
- Model choice
- Cost profile
- Latency

Environment differences may **not** affect:
- Review order
- Authority boundaries
- Draft lifecycle
- Human decision requirements

This ensures:
- Safe work-time usage with API keys
- Cost-free home experimentation
- Identical behavior guarantees

---

## What This Enables

- Seamless switching between local and API models
- Work-time productivity without refactoring
- Cost control without governance risk
- Future multi-model experimentation

---

## What Is Explicitly Blocked

- API model granting extra authority
- “Premium model = execution” assumptions
- Review shortcutting due to cost or convenience

---

## Alignment Notes

Aligned with:
- docs/fh-constitution.md
- docs/llm-routing.md
- docs/review_pass_mechanics.md
- docs/review_checks_mapping.md

No conflicts detected.

---

## Notes

- Model selection should remain configurable
- Governance documents remain authoritative
- Implementation details belong elsewhere
