# Review-Pass Mechanics — Definition & Boundaries

*(Governance-aligned, no new behavior)*

---

## Purpose

This document defines the **review-pass mechanics** for Future Hause.

It establishes:
- Which review checks exist
- Which checks may be automated vs human-only
- What review outputs are allowed
- What review outputs are forbidden

This document does **not** introduce execution, approval automation, or agent authority.

---

## Review Pass Ordering

Reviews are **sequential and additive**, never mutating.

A draft may pass through **zero or more** review passes before a human decision is made.

---

## Review Pass 1 — Contract / Constitution Compliance

### Purpose
Ensure the draft does not violate:
- Constitution
- Contracts
- Explicit system boundaries

### Allowed Reviewers
- Agent (read-only)
- Human

### Allowed Actions
- Read draft
- Flag violations
- Cite document sections

### Forbidden Actions
- Editing
- Rewriting
- Approval
- Execution

### Output
DraftReview record with:
- review_type = "contract"
- severity
- notes
- references (required if flagged)

### Automation Level
Deterministic + agent-assisted flagging only.  
Agents may assist in identifying issues but may not decide outcomes.

---

## Review Pass 2 — System / Architecture Scope

### Purpose
Ensure the draft:
- Does not introduce scope creep
- Does not violate responsibility boundaries
- Does not imply automation or execution

### Allowed Reviewers
- Agent (read-only)
- Human

### Allowed Actions
- Read draft
- Flag boundary or scope issues

### Forbidden Actions
- Suggesting new features
- Proposing architecture changes
- Editing or rewriting

### Output
DraftReview record with:
- review_type = "architecture"
- severity
- notes

### Automation Level
Agent-assisted only.  
Human judgment required for disposition.

---

## Review Pass 3 — Clarity / User Impact

### Purpose
Evaluate whether the draft is:
- Understandable
- Actionable
- Appropriately scoped

### Allowed Reviewers
- Agent (read-only)
- Human

### Allowed Actions
- Flag unclear language
- Flag over- or under-specification

### Forbidden Actions
- Changing intent
- Adding requirements
- Rewriting content

### Output
DraftReview record with:
- review_type = "clarity"
- severity
- notes

### Automation Level
Agent-assisted.  
Non-authoritative and low risk.

---

## Prohibited Review Behaviors (Global)

Across all review passes, reviews may **never**:

- Edit drafts
- Rewrite drafts
- Approve drafts
- Execute changes
- Imply execution occurred
- Communicate across zones

These prohibitions are absolute.

---

## Human Decision Point

After any combination of review passes, a **human** decides:

- Approve draft
- Flag for revision
- Reject draft

This decision:
- Updates DraftWork.status
- Does **not** execute anything
- May precede execution later

---

## Mapping to Draft Work Log

- Each review creates a **DraftReview** record
- Draft content remains immutable
- Review history is preserved
- Status changes only by human action

---

## What This Enables

- Safe agent-assisted review
- Clear audit trail
- Review without authority leakage
- Deterministic governance boundaries

---

## What Is Explicitly Blocked

- Auto-approval
- Review-triggered execution
- Cross-review mutation
- Agent-driven scope expansion

---

## Alignment Notes

This document is aligned with:
- docs/fh-constitution.md
- docs/conversation_contract.md
- docs/llm-routing.md
- docs/agent_architecture_and_invocation_v1.md

No conflicts detected.

---

## Notes

- Review mechanics are governance rules, not implementation details
- Sequencing is defined here intentionally
- Execution behavior is defined elsewhere
