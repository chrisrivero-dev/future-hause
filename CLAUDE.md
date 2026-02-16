# CLAUDE.md — AI Execution Contract for Future Hause

This document defines the execution constraints for AI assistants working on Future Hause.

It is not marketing copy.  
It is an architectural discipline contract.

---

## System Identity

Future Hause is a **bounded intelligence system**.

It:
- Collects signals
- Classifies them
- Generates proposals
- Promotes structured artifacts
- Generates advisories
- Scaffolds drafts (conditionally)

It does **not**:
- Act autonomously
- Publish content
- Contact customers
- Modify external systems
- Make final decisions

**Core principle:**  
Future Hause suggests. Humans decide.

---

## Architectural Model

Future Hause operates as a deterministic lifecycle:

```
Inputs
  ↓
Signal Extraction
  ↓
Proposal Generation
  ↓
Promotion (state_mutations)
  ↓
Advisory Generation
  ↓
(Optional) Draft Scaffolding
```

Each layer is explicit.  
No hidden background loops.  
No silent mutations.

---

## Autonomy Model (Bounded)

Future Hause supports bounded autonomy with gates.

### Allowed
- Deterministic lifecycle execution
- Automatic promotion (rule-based)
- Advisory generation (detinistic)
- Conditional draft scaffolding (focus-matched only)

### Forbidden
- Auto-publishing
- Auto-execution of KB updates
- Auto-contact with external systems
- Background polling without explicit trigger
- Hidden retries or silent failure recovery

All autonomy must be:
- Traceable
- Logged
- Human-visible
- Reversible

---

## State Is the Source of Truth

All system behavior must read and write through:

```
state/cognition_state.json
```

No in-memory shadow state.  
No hidden global variables.  
No UI-derived state mutations.

Every mutation must:
- Be written to state
- Append an `action_log` entry
- Be auditable

---

## Lifecycle Rules

1. Extraction writes **signals only**.
2. Proposal generation writes **proposals only**.
3. Promotion writes to **state_mutations only**.
4. Advisory generation writes to **state.advisories only**.
5. Draft scaffolding writes to **state.kb_drafts only**.
6. No layer skips another.

No cross-layer mutation shortcuts are allowed.

---

## Deterministic First

When implementing features:

- Prefer rule-based logic over LLM calls.
- LLMs may classify or summarize.
- LLMs must not control state transitions.
- Confidence scores must not gate execution.
- Pass/fail logic only.

---

## File Modification Discipline

When modifying code:

- Do not refactor architecture unless instructed.
- Do not rename files casually.
- Do not create new modules unless necessary.
- Prefer inline changes for small tasks (<5 edits).
- Use `grep` before reading large files.
- Never re-read the same file unnecessarily.

Do not narrate tool calls.  
Do not echo file contents back.

---

## UI Contract

The UI is a reflection layer only.

The UI:
- Reads API endpoints.
- Does not mutate state directly.
- Does not infer state.
- Does not implement business logic.

All business logic belongs in the `engine/` layer.

---

## Logging Requirements

Every lifecycle cycle must append:

- `signal_extraction_cycle`
- `advisory_generated` (if applicable)
- `focus_changed` (if applicable)
- `draft_scaffolded` (if applicable)

No silent state changes are allowed.

---

## Focus System

Focus is a first-class concept.

```
state.focus.active_project_id
```

Rules:
- Only one active project at a time.
- Advisory priority may depend on focus.
- Draft scaffolding only occurs for focus-matched advisories.
- Focus does not auto-create projects.

---

## Draft Scaffolding Rules

Draft scaffolds:
- Are structured.
- Are not published.
- Are marked as `scaffolded`.
- Must be manually reviewed before promotion.

No auto-KB publication ever.

---

## Safety Boundaries

Never implement:

- Background daemons
- Autonomous loops
- Self-triggered re-execution
- External API write calls
- Credential storage
- Customer communication logic

If a feature makes Future Hause resemble an AI employee,  
it violates the system identity.

---

## Error Handling

On error:

- Stop execution.
- Log error.
- Do not retry automatically.
- Do not guess.
- Do not fabricate fallback state.

Graceful failure > clever recovery.

---

## Execution Summary

Future Hause is:

- Structured
- Deterministic
- Logged
- Bounded
- Human-governed

It is not:

- An agentic employee
- A self-directing bot
- A production automation engine

If a change increases autonomy,  
it must introduce an explicit gate.
