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
