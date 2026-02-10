# Agent Collaboration Zones — Future Hause

This document defines where agent collaboration is permitted within Future Hause.
It is a conceptual mapping aligned to the Constitution and existing contracts.
No new system behavior is introduced here.

## Zones

### 1. Work Zone
Purpose:
- Drafting, synthesis, exploration

Allowed:
- Agent ↔ Agent collaboration
- Human authoring

Forbidden:
- Execution
- Side effects
- Approval
- State mutation

Mapped Concepts:
- Draft Work
- Draft Work Log
- Observations / Intel

References:
- docs/fh-constitution.md
- docs/intelligence_contract_v0.md
- docs/conversation_contract.md

---

### 2. Review Zone
Purpose:
- Read-only evaluation of drafts

Allowed:
- Agent review
- Flagging issues
- Human review

Forbidden:
- Editing
- Rewriting
- Approval
- Execution

Mapped Concepts:
- Review
- Recommendations

References:
- docs/agent_architecture_and_invocation_v1.md
- docs/conversation_contract.md

---

### 3. Execution Zone
Purpose:
- Apply approved changes

Allowed:
- Human-only actions

Forbidden:
- Agent collaboration
- Autonomous execution
- Implied actions

Mapped Concepts:
- Human State Mutation
- Action Log

References:
- docs/fh-constitution.md
- docs/llm-routing.md

---

## Notes

- Zones are conceptual governance boundaries, not implementation details.
- If ambiguity exists between documents, it must be flagged, not resolved implicitly.
