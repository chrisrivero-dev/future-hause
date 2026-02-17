# SYSTEM_ARCHITECTURE.md — Deterministic Lifecycle & Layer Responsibilities

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       FUTURE HAUSE v0.1                         │
│                                                                 │
│  ┌──────────┐   ┌────────────┐   ┌────────────┐                │
│  │  INPUT    │──>│  SIGNAL    │──>│ PROPOSAL   │                │
│  │Collection │   │ Extraction │   │ Generation │                │
│  └──────────┘   └────────────┘   └─────┬──────┘                │
│   (automated)     (automated)          │                        │
│                                        v                        │
│                               ┌────────────────┐               │
│                               │   DECISION      │ <── HUMAN    │
│                               │   Recording     │              │
│                               └───────┬────────┘               │
│                                       v                         │
│                               ┌────────────────┐               │
│                               │   PROMOTION     │ <── HUMAN    │
│                               │   Execution     │              │
│                               └───────┬────────┘               │
│                                       │                         │
│                          ┌────────────┼────────────┐            │
│                          v            v            v            │
│                   ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│                   │ADVISORY  │ │  DRAFT   │ │ REVIEW   │       │
│                   │Gen.      │ │ Scaffold │ │ Engine   │       │
│                   └──────────┘ └──────────┘ └──────────┘       │
│                    (automated)  (gated/stub)  (read-only)       │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           state/cognition_state.json (single SOT)         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Deterministic Lifecycle

```
Input ──> Signal Extraction ──> Proposal ──> [Human Decision] ──> Promotion ──> Advisory ──> Draft Scaffold
  1             2                  3               4                  5            6              7
```

Each step feeds the next. No step may be skipped. Steps 4 and 5 require explicit human action.

---

## Layer Definitions

### 1. Input Collection — `engine/run.py`

Collects raw signals from configured sources (Reddit stub in v0.1). Human-initiated via `python engine/run.py`. **Mutates:** `data/raw/`, `engine/state.json`, `engine/log.json`. **Reads:** `config/future_hause.yaml`.

### 2. Signal Extraction — `engine/signal_extraction.py`

Converts raw posts into UUID-tagged perception signals. Deterministic, no LLM. Automated after collection. **Mutates:** `perception.signals` (append-only). **Reads:** raw data, existing signals for deduplication. Once created, signals are never modified or deleted.

### 3. Proposal Generation — `engine/proposal_generator.py`

Routes signals to typed proposal buckets by category. Deterministic only. Automated after extraction. **Mutates:** `proposals.kb_candidates` or `proposals.project_candidates` (append-only). **Reads:** signals, existing proposals for deduplication.

Routing: `discussion` → KB candidate | `announcement` → project candidate | unknown → skipped.

### 4. Decision Recording — `engine/promotion_engine.py`

Records human approval or rejection. **Human-triggered only** via `record_approval()` or `record_rejection()`. **Mutates:** `decisions.approved` or `decisions.rejected`. Every decision records `approved_by`, `rationale`, and timestamp. Recording does **not** promote — that is a separate human action.

### 5. Promotion Execution — `engine/promotion_engine.py`

Moves approved proposals into `state_mutations` with full audit trail. **Human-triggered only** via `run_promotion()` or `promote_single()`. **Mutates:** `state_mutations.kb` or `state_mutations.projects`, `state_mutations.action_log`, `decisions.approved[*].promoted`. Creates traceable chain: `signal_id → proposal_id → decision_id → mutation_id`.

### 6. Advisory Generation — `engine/advisory_generator.py`

Generates deterministic intel alerts for promoted projects. Automated. **Mutates nothing directly** — returns advisory objects; caller appends via `state_manager.append_open_advisories()`. Bounded: one per source signal, type `intel_alert` only, no scoring. Status lifecycle: `open → resolved | dismissed` (human-managed).

### 7. Draft Scaffold — `engine/agents/draft_agent.py`

Generates draft content for human review. Gated by router policy + executor flag (`EXECUTION_ENABLED = False`). **Mutates nothing.** Drafts are transient payloads with a `review_payload` for optional critique. Drafts are proposals, not actions.

---

## State & Mutation Authority

All internal state lives in `state/cognition_state.json` via `engine/state_manager.py`.

### What Mutates State

| Layer | Target | Gate |
|---|---|---|
| Collection | Raw data, engine log, engine state | None (deterministic) |
| Signal Extraction | `perception.signals` | None (deterministic) |
| Proposal Generation | `proposals.*` | None (deterministic) |
| Decision Recording | `decisions.*` | **Human required** |
| Promotion Execution | `state_mutations.*`, `decisions.*.promoted` | **Human required** |
| Advisory Append | `advisories.open` | None (caller-driven) |
| Advisory Status Change | `advisories.*` (moves between buckets) | **Human required** |
| Project Focus | `focus.active_project_id` | **Human required** |

### What Is Strictly Read-Only

| Layer | Reason |
|---|---|
| Advisory Generation | Returns objects; does not write |
| Draft Agent | Produces ephemeral payloads only |
| Review Engine | Advisory critique; no state access |
| Agent Router | Policy evaluation only |
| Executor | Decision relay; execution disabled |

All state sections are **append-only** (signals, proposals, decisions, mutations, action_log). Output files under `outputs/` are read-only exported artifacts never written by the engine.

---

## Action Classification

### Human-Triggered Actions

- `record_approval(proposal_id, approved_by, rationale)`
- `record_rejection(proposal_id, rejected_by, rationale)`
- `run_promotion(triggered_by)` / `promote_single(decision_id, triggered_by)`
- `update_advisory_status(advisory_id, new_status)`
- `set_active_project(project_id)`
- Running the engine: `python engine/run.py`

### Deterministic Automated Actions

- Signal extraction: raw post → UUID-tagged signal (no LLM)
- Proposal generation: signal category → typed proposal (no LLM)
- Advisory generation: promoted project → intel alert (no LLM)
- Deduplication filtering at every append boundary

### Forbidden Autonomous Behaviors

- **No auto-approval.** Proposals never self-promote regardless of content.
- **No auto-promotion.** Approved decisions require a separate human trigger.
- **No auto-publish.** Output artifacts are never written by the engine.
- **No agent self-invocation.** Agents never trigger other agents.
- **No synthetic signals.** LLMs cannot generate perception signals.
- **No history deletion.** Signals, proposals, decisions, mutations are append-only.
- **No implicit state inference.** Drafts never become facts. Advisories never become actions.
- **No external execution.** `EXECUTION_ENABLED = False`. No shell, subprocess, or network calls.
- **No confidence-based gating.** No scoring thresholds trigger automated behavior.
- **No bypass of the three-step promotion gate** (propose → approve → promote).

---

## Three-Step Promotion Invariant

No proposal reaches `state_mutations` without three distinct stages, two requiring explicit human action:

```
1. Proposal created       (automated, deterministic)
2. Decision recorded      (human: record_approval with identity + rationale)
3. Promotion executed     (human: run_promotion with triggered_by)
```

Every mutation in `state_mutations.action_log` contains the full chain: `proposal_id → decision_id → mutation_id → triggered_by`. This is the audit trail.
