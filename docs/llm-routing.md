# LLM Routing Rules v0 (Future Hause)

**Status:** Canonical Contract (authoritative)  
**Purpose:** Define intent-first, cost-minimizing routing rules for any LLM usage.  
**Non-negotiable:** Humans decide. The system advises. No implied actions.

---

## Core Goal

Routing must be **intent-first** and **cost-minimizing**.

Predictable behavior, explicit guardrails, and minimal token usage.

---

## Pre-LLM Classification (Required)

Before any LLM is used, the system MUST classify:

### 1) Intent (one of)
- **Question** — user asks for an answer.
- **Draft Request** — user asks for a draft output (email, summary, timesheet, etc.).
- **Observation** — user provides notes without a direct question.
- **Meta** — user asks about the system itself (purpose, capabilities, rules).
- **Action** — user requests changes or execution (run, write, commit, publish, log).

### 2) Risk (one of)
- **Low** — casual, non-sensitive, reversible drafts.
- **Medium** — could mislead, affect decisions, or be mistaken as record.
- **High** — anything that could be treated as system-of-record, legal/financial/medical, or irreversible.

### 3) Permanence (one of)
- **Ephemeral** — transient chat-only assistance.
- **Draft-only** — clearly labeled draft; no persistence; for review.
- **Record-adjacent** — could influence logs, tickets, KB, metrics, or documentation.

---

## Hard Rules (Always)

1) **Drafting is opt-in only.**  
   - The system should NOT draft unless the user asks for a draft or explicitly approves drafting.

2) **Questions must be answered directly.**  
   - If the user asks a question, Future Hause answers it directly (no detours into drafting).

3) **Observations without a question default to Draft mode (advisory).**  
   - BUT: do not generate a draft unless the user requested one. Otherwise, ask 1 clarifying question or respond with a lightweight acknowledgement and a suggested next question.

4) **No model may imply system actions unless confirmed in the Action Log.**  
   - The assistant must not claim: “I updated X”, “I logged Y”, “I saved Z”, “I changed state” unless it is explicitly recorded in the Action Log.

5) **“Nothing happened” must be explicit when applicable.**  
   - If no changes occurred, the response must say so plainly.

6) **No side effects by default.**  
   - No file writes, no API calls, no ticket creation, no Excel writes, no persistence unless a human explicitly triggers that workflow and it is logged.

7) **Action Log is human-write-only.**  
   - The system can propose an Action Log entry, but cannot write it automatically.

8) **Any behavior not explicitly allowed here is forbidden by default.**

---

## Cost Constraints (Strict)

1) Prefer deterministic logic over LLM calls whenever possible.
2) Use the cheapest viable model for classification.
3) Only call a full reasoning model when synthesis or explanation is required.
4) Never call more than **one** high-capability model for a single user input.
5) Avoid multi-model chains unless:
   - the input is **Record-adjacent** OR **Medium/High risk**, AND
   - the user explicitly asked for a higher-quality synthesis.

---

## Routing Policy (Conceptual)

### A) Classification step
- First attempt: deterministic keyword + pattern rules.
- If uncertain: use the cheapest classifier model.

### B) Answering
- **Question + Low risk + Ephemeral:** answer directly with minimal model or deterministic logic if possible.
- **Question + Medium/High risk:** answer + include assumptions + ask 1 clarifying question if needed.

### C) Drafting
- **Draft Request:** produce draft labeled **DRAFT**.
- If user did not ask for draft: do NOT draft; ask for permission or a clarifying question.

### D) Action intent
- For any Action request:
  - propose a plan
  - explicitly state: “No action taken”
  - require human confirmation step and Action Log entry (human authored)

---

## Output Requirements (For Any LLM Response)

Every response must clearly communicate:
- What you understood
- What you did
- What you did NOT do
- Next step (optional)
- If nothing changed: say “Nothing was changed.”

---

## Notes

These routing rules are the authoritative contract for implementation.
Any code or UI must conform to this document.
