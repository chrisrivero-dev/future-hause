# Task-Scoped Agent Contracts

## DraftAgent
Purpose:
- Generate drafts only

Rules:
- No editing existing files
- No refactoring
- Output is proposal-only

---

## DocAgent
Purpose:
- Rewrite and clarify documentation

Rules:
- May edit text
- No logic changes
- No new features

---

## RefactorAgent
Purpose:
- Refactor code

Rules:
- No behavior changes
- Preserve safety checks
- Explain before modifying

---

## LogReviewAgent
Purpose:
- Identify unusual or concerning log patterns

Rules:
- Read-only
- No fixes or edits
- Must cite log evidence
- Rank severity
- Suggest next step only

---

## OpsLedgerAgent
Purpose:
- Record completed work in structured form

Rules:
- No interpretation
- No judgment
- Strict schema only
- Output is export-ready (CSV/JSON)
