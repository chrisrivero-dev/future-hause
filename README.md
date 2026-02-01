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

## Repository Structure (Evolving)

