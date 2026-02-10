# Draft Work Log — Data Model & Lifecycle

*(Governance-aligned, no new behavior)*

---

## Purpose

This document defines the **Draft Work Log** as a first-class governance artifact in Future Hause.

It:

- Makes **Draft Work** a durable, inspectable object
- Gives the **Review Zone** something concrete to evaluate
- Keeps **Execution** explicitly human-only
- Allows all dashboard sections to reference a single source of truth

This document defines **architecture and lifecycle only**.
It does **not** introduce new system behavior or implementation details.

---

## 1) Core Entity: `DraftWork`

### Required Fields

```ts
DraftWork {
  draft_id: string;              // unique, immutable identifier
  created_at: ISO8601;
  created_by: "human" | "agent"; // origin only, not authority

  source: {
    message_id: string;          // originating user input
    router_intent: string;       // per docs/llm-routing.md
  };

  zone: "work";                  // drafts always exist in Work Zone

  content: {
    body: string;                // draft text or artifact
    format: "text" | "md" | "json" | "code";
  };

  status: DraftStatus;           // lifecycle state (see below)

  tags: string[];                // e.g. ["intel", "kb-gap", "project"]
}
```

### Draft Status Enum (Locked)

```ts
type DraftStatus =
  | "drafted"        // created in Work Zone
  | "under_review"   // read-only review initiated
  | "flagged"        // review identified issues
  | "approved"       // human-approved (no execution implied)
  | "rejected";      // explicitly declined
```

> **Important:**  
> `approved` does **not** mean executed. Approval only permits a human to take a future action.

---

## 2) Review Attachments (Non-Mutating)

Reviews do **not** edit drafts. They attach findings as separate records.

```ts
DraftReview {
  review_id: string;
  draft_id: string;

  reviewer: "agent" | "human";
  review_type: "contract" | "architecture" | "clarity";

  findings: {
    severity: "low" | "medium" | "high";
    notes: string;               // flags only, no rewrites
    references?: string[];       // constitution sections, if applicable
  };

  created_at: ISO8601;
}
```

---

## 3) Lifecycle Rules (Authoritative)

### Creation

Triggered by:
- User explicitly requesting a draft
- Router classifying intent as `draft_request`

Zone:
- **Work Zone**

Initial Status:
- `drafted`

---

### Review

Triggered by:
- Human initiating review

Zone:
- **Review Zone**

Status:
- `under_review`

Reviewers may:
- Read draft content
- Flag issues

Reviewers may **NOT**:
- Edit
- Rewrite
- Approve
- Execute

---

### Decision

Actor:
- **Human only**

Outcomes:
- `approved` → eligible for future execution
- `flagged` → returns to Work Zone
- `rejected` → closed

---

### Execution

Execution is **out of scope** for this document.

Handled via:
- Human State Mutation
- Action Log entries

The Draft Work Log remains immutable history.

---

## 4) Mapping to Dashboard Sections

| Dashboard Section | Reads From |
|------------------|-----------|
| Draft Work | DraftWork where status ≠ `rejected` |
| New Intel | DraftWork tagged `intel` |
| KB Opportunities | DraftWork tagged `kb-gap` |
| Projects | DraftWork tagged `project` |
| Recommendations | DraftReview summaries |
| Active Project Focus | Human-selected `draft_id` |
| Action Log | Separate Execution Zone system |

---

## 5) Explicitly Blocked Behaviors

This model prevents:

- Silent edits
- Agent approvals
- Agent execution
- Drafts disappearing without record

All constraints align with:

- `docs/fh-constitution.md`
- `docs/conversation_contract.md`
- `docs/llm-routing.md`
