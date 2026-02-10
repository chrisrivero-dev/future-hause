# State Mutation Contract

## Purpose
This contract defines how and when system state is allowed to change.

State mutation is considered a privileged operation and is strictly governed.

---

## What Counts as State

State includes, but is not limited to:
- Projects
- Project status or priority
- Active Project Focus
- Knowledge Base entries
- Stored notes
- System configuration

---

## Core Rules

1. Conversation is the ONLY write interface.
2. No state may be changed automatically.
3. All state changes must be drafted first.
4. Drafts must be explicitly approved by a human.
5. The Draft Work Log is the audit gate for all mutations.

---

## Draft Requirement

All proposed state changes must:
- Be presented as a draft
- Be reviewable
- Be editable
- Be rejectable

No exception exists for “obvious” or “low-risk” changes.

---

## Explicit Prohibitions

The system may NEVER:
- Apply state changes silently
- Batch or chain mutations without review
- Mutate state based on inference
- Learn preferences that expand authority

---

## Governing Principle
Draft first.
Human approves.
State changes once.
