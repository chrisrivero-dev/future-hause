# Future Hause

Future Hause is a **local support intelligence assistant**.

It runs quietly in the background to collect support signals, track recurring issues, and produce **human-reviewed documentation drafts** that reduce repeat support tickets.

Future Hause does **not** talk to customers, make decisions, or publish content automatically.

---
## LLM Routing Contract

LLM routing rules are defined in `docs/llm-routing.md`.  
All code must conform to that contract. No implicit actions.

## Core Philosophy

- Human-in-the-loop by design
- Transparency over autonomy
- Evidence before conclusions
- Boring, reliable automation over “AI magic”

Future Hause is an **analyst**, not an actor.

---

## What Future Hause Does

At a high level, Future Hause:

1. Collects support signals (e.g. Reddit, tickets)
2. Records what it did (state + logs)
3. Produces structured artifacts for review
4. Waits for human approval

Nothing is sent, published, or decided automatically.

---

## What Future Hause Does NOT Do

- ❌ No customer-facing chat
- ❌ No auto-publishing
- ❌ No task assignment
- ❌ No emotional or human-like behavior
- ❌ No decision-making authority

If it looks like a “bot employee,” it’s out of scope.

---

## Project Status

**Current version:** v0.1 (in progress)

### v0.1 Scope (Locked)

Future Hause v0.1 does **only** the following:

- Collect Reddit posts (read-only)
- Save raw data locally
- Record job state:
  - `idle → collecting → done`
- Log what happened during a run

No analysis.  
No AI.  
No UI.

If it’s not required for the above, it is intentionally excluded.

---

## Planned Future Versions (High-Level)

- **v0.2**
  - Batch builder
  - Structured datasets for analysis

- **v0.3**
  - Claude-assisted analysis
  - Draft KB articles and canned responses

- **v0.4+**
  - Read-only dashboard
  - State visualization
  - Review & approval interface

These are ideas, not commitments.

---

## Intent Routing & Ollama Usage

Future Hause classifies user messages by **intent** before responding.

### Intent Types

| Intent | Behavior | Ollama Called? |
|--------|----------|----------------|
| `draft_request` | Generate draft → render in Draft Work | ✅ Yes |
| `question` | Explanatory response only | ❌ No |
| `meta` | Static explanation of FutureHause | ❌ No |
| `action` | Refusal + explanation of boundaries | ❌ No |
| `observation` | Acknowledgement only | ❌ No |

### Key Rules

- **Ollama is draft-only**: Only called when `allow_draft === true`
- **No background calls**: All LLM calls are explicit and user-triggered
- **No auto-routing**: Intent classification is deterministic (heuristics, no LLM)

See `docs/llm-routing.md` for the full routing contract.

---

## Draft Work vs KB Opportunities

| Section | Purpose | Source | Persistence |
|---------|---------|--------|-------------|
| **Draft Work** | Ollama-generated drafts for review | User request + Ollama | None (ephemeral) |
| **KB Opportunities** | Observed gaps in knowledge base | System observation | Candidate only |

### Draft Work Rules
- Generated only when user explicitly requests a draft
- Content is **DRAFT** until human review
- No auto-promotion to KB, Projects, or Action Log
- No persistence — refresh clears drafts

### KB Opportunities Rules
- System-observed suggestions, not user-generated
- Marked as **CANDIDATE** until promoted
- Promotion requires explicit human approval

---

## Action Log Semantics

The Action Log records **approved actions only** — not ideas, not drafts.

### Action Log Schema (Future)

Each entry will include:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier |
| `timestamp` | ISO 8601 timestamp |
| `actor` | Who approved/performed the action |
| `action_type` | Type of action taken |
| `target` | What was affected |
| `rationale` | Why the action was taken |

### Example Entries

- "Updated Freshdesk work spreadsheet"
- "Created KB article from approved recommendation"
- "Promoted recommendation to project"

### Key Rule

> **Ideas do not go into the Action Log — only approved actions do.**

---

## Future: WorkLogAgent (Design Only)

A future WorkLogAgent will help capture daily work hours for export.

### Conceptual Flow

1. User drafts work entries via **Draft Work**
2. User reviews and approves entries
3. Approved entries → **Action Log**
4. Later: Export approved entries to Excel for CEO review

### Guardrails

- No Excel generation yet
- No filesystem writes yet
- No scheduling or background logging
- All exports require explicit human action

This keeps FutureHause safe and reviewable.

---

## Repository Structure (Evolving)

