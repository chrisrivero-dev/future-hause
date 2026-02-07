Future Hause Constitution (v0)

1. Truth vs Interpretation
   Facts come only from registries and the Action Log.
   LLM output is advisory unless explicitly promoted by a human.
   Presence states describe loop state, not completed work.

2. Candidate Objects
   Future Hause may generate:

- Candidate Intel
- Candidate KB Opportunities
- Candidate Recommendations
- Draft Artifacts
  All must be labeled and non-persistent until human promotion.

## Core System Architecture

Future Hause is composed of four strict tiers:

Router → Draft Engine → Review Engine → Human State Mutation

Each tier has a single responsibility and explicit limits.
No tier may bypass another.

Autonomy is permitted only where outputs are reversible.
Execution and state mutation are always human-governed.

---

## 1. Router (Heuristics Layer)

**Role**

- Entry point for all events (system or human)
- Determines _which agent could run_
- Enforces runtime mode restrictions

**Characteristics**

- Rule-based (no LLM calls)
- Deterministic
- Side-effect free
- Blocks execution by default

**Key Principle**

> The Router may _suggest_ agents, but never executes them.

---

## 2. Draft Engine (Scoped Autonomy)

**Role**

- Generates drafts, summaries, or structured outputs
- Operates autonomously **only within strict bounds**

**Allowed Autonomy**

- DraftAgent is the **only** agent permitted to run without human approval
- Outputs are treated as _proposals_, never actions

**Explicit Constraints**

- No state mutation
- No external side effects
- No irreversible operations
- No direct execution of system actions

**Rationale**
Drafting is reversible. Execution is not.

---

## 3. Review Engine (Advisory Intelligence)

**Role**

- Critiques, evaluates, and flags draft outputs
- Provides risk signals and confidence estimates

**Characteristics**

- Never runs automatically
- Always human-triggered
- May use premium or external models (e.g. Kimi, GPT, Claude)
- Outputs are advisory only

**Important**

> A review does not imply approval.

---

## 4. Human State Mutation (Final Authority)

**Role**

- Approves, rejects, or modifies outcomes
- Owns all irreversible decisions
- Controls whether anything moves forward

**Examples**

- Approving a draft
- Rejecting a recommendation
- Manually triggering a follow-up action

**Non-Negotiable Rule**

> No agent may mutate system state without an explicit human action.

---

## Execution Model

- Agents do **not** execute each other
- Execution is mediated by a dedicated executor layer
- Executor respects:
  - Router decisions
  - Runtime mode
  - Human approvals

Blocked-by-default is intentional.

---

## Logging & Auditability

Future Hause maintains an **Action Log** that records:

- Timestamp
- Event ID
- Actor (human or agent)
- Action taken
- Rationale / reason

This provides:

- Full traceability
- Post-hoc analysis
- Review comparison potential

No separate “payload history” is required unless a future use case demands it.

---

## Runtime Modes

The system supports multiple runtime modes (e.g. LOCAL, WORK, DEMO).

Runtime mode controls:

- Which events are permitted
- Which agents may run
- Whether external services are accessible

This enables:

- Safe operation on work machines
- Richer behavior at home
- Deterministic demos

---

## Work vs Home Environments

**Work Environment**

- System Python (no PATH changes)
- User-scoped dependencies only
- No local LLMs
- No automatic execution
- Static UI + modular engine

**Home Environment**

- Optional virtual environments
- Local or remote LLMs
- Expanded experimentation
- Same architectural constraints

The architecture does not change — only capabilities do.

---

## Explicit Non-Goals

Future Hause is **not**:

- A fully autonomous agent system
- A self-governing AI
- A background process that acts without oversight

If a feature proposal violates these constraints, it should be rejected.

---

## Design Philosophy (Summary)

- Autonomy is earned, not assumed
- Drafting is safe; execution is dangerous
- Humans stay in control
- Architecture > cleverness
- Constraints enable speed

This document is the contract.

3. Action Log Authority
   The Action Log is the sole system of record.
   No action may be implied unless it exists in the Action Log.
   Drafts, summaries, and recommendations are not actions.

4. Drafting Rules
   Drafting is opt-in.
   Drafts must be clearly labeled.
   Drafts must never be auto-submitted or written externally.

5. Uncertainty Handling (Critical)
   If Future Hause is uncertain, it must:

- State the uncertainty explicitly
- Avoid guessing
- Record the uncertainty for later resolution
  Uncertainty is a first-class object.
  Resolved uncertainties may be promoted to truth only by a human.

6. Learning Boundary
   Future Hause does not learn implicitly.
   Knowledge updates only occur when a human resolves:

- an uncertainty
- or promotes a draft or recommendation

7. LLM Guardrails
   Routing is intent-first and cost-minimizing.
   Deterministic logic is preferred over model calls.
   No model may imply system actions.
