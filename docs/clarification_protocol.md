# Clarification Protocol

## Purpose
This protocol defines how Future Hause handles ambiguous user input.

It replaces confidence thresholds, probability scoring, and intent guessing.

---

## Definition of Ambiguity

A message is considered ambiguous if it could reasonably be interpreted as:
- A command OR
- Commentary, reflection, or speculation

Ambiguity is determined conservatively.

---

## Mandatory Rule

If ambiguity exists:
- The system MUST ask a clarifying question.
- The system MUST NOT draft or propose any action.
- The system MUST NOT mutate state.

---

## Clarifying Question Format

Clarifying questions must:
- Be explicit
- Offer clear options
- Use “this or that” phrasing

Example:
- “Do you want me to add this as a project, or just note it for later?”

---

## Explicit Prohibitions

The system may NEVER:
- Guess user intent
- Choose an option on behalf of the user
- Escalate ambiguous input into proposals

---

## Governing Principle
When unsure, ask.
Never assume.
