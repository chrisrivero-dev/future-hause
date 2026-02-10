# Review Checks — Deterministic vs Agent-Assisted Mapping

*(Governance-aligned, no new behavior)*

---

## Purpose

This document classifies **review checks** used in Future Hause into:

- Deterministic (non-LLM)
- Agent-assisted (LLM-supported, non-authoritative)
- Human-only

The goal is to ensure reviews are:
- Cheap by default
- Predictable
- Constitutionally safe
- Free of accidental autonomy

This document does **not** introduce implementation details or automation.

---

## Classification Principles

1. Deterministic checks are always preferred.
2. Agent-assisted checks may **flag**, never decide.
3. Human judgment is required for approval, rejection, or execution.
4. No check may mutate drafts or system state.

---

## Review Check Matrix

### Contract / Constitution Compliance

Deterministic Checks:
- Presence of prohibited phrases (execution, approval, autonomy)
- Reference to disallowed actions
- Missing required disclaimers
- Violations of response-type separation

Agent-Assisted Checks:
- Identify ambiguous language
- Highlight potential constitutional conflicts
- Suggest which contract sections may apply

Human-Only:
- Final determination of violation severity
- Decision to approve, flag, or reject

---

### System / Architecture Scope

Deterministic Checks:
- Mentions of automation or background execution
- References to undefined system components
- Scope keywords exceeding current system boundaries

Agent-Assisted Checks:
- Flag likely scope creep
- Identify responsibility leakage
- Detect implied future features

Human-Only:
- Decide whether scope expansion is acceptable
- Authorize architectural changes

---

### Clarity / User Impact

Deterministic Checks:
- Empty or malformed content
- Structural issues (missing sections, headings)
- Excessive length thresholds

Agent-Assisted Checks:
- Flag unclear instructions
- Identify over- or under-specification
- Highlight confusing terminology

Human-Only:
- Decide whether clarity issues warrant revision
- Accept tradeoffs between clarity and brevity

---

## What Is Explicitly Forbidden

- Agent-only approval
- Agent-only rejection
- Review-triggered execution
- Review-triggered draft mutation
- Cross-check side effects

---

## Mapping to Review Passes

| Review Pass | Deterministic | Agent-Assisted | Human-Only |
|------------|---------------|----------------|------------|
| Contract | Yes | Yes | Yes |
| Architecture | Yes | Yes | Yes |
| Clarity | Yes | Yes | Yes |

Deterministic checks run first, followed by agent-assisted flagging.
Human decision always terminates the review chain.

---

## Alignment Notes

Aligned with:
- docs/fh-constitution.md
- docs/review_pass_mechanics.md
- docs/conversation_contract.md
- docs/llm-routing.md
- docs/agent_architecture_and_invocation_v1.md

No conflicts detected.

---

## Notes

- This mapping enables future automation without authority leakage
- Local scripts or rules engines may implement deterministic checks
- LLMs remain advisory only
