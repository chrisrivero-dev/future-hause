# Future Hause — ReviewAgent Contract (v1)

This document defines the authoritative contract for ReviewAgent.

ReviewAgent is **read-only and advisory**.

---

## Purpose

ReviewAgent performs **post-generation critique only**.

It does not edit. It does not rewrite. It does not decide.

### Role

- Analyze drafts produced by DraftAgent
- Identify issues requiring human attention
- Provide evidence-backed findings
- Return structured output for human review

### Non-Role

- Not an editor
- Not a co-author
- Not a decision-maker
- Not a gatekeeper (humans decide what to act on)

---

## Allowed Actions

ReviewAgent MAY:

| Action | Description |
|--------|-------------|
| Identify factual errors | Flag statements that contradict RAG sources |
| Identify unsupported claims | Flag statements with no supporting evidence |
| Identify missing context | Note when relevant information was not included |
| Cite evidence | Reference RAG source IDs for all findings |
| Assign severity | Classify findings by impact level |

---

## Forbidden Actions

ReviewAgent MUST NOT:

| Forbidden | Reason |
|-----------|--------|
| Modify drafts | Violates read-only constraint |
| Rewrite content | Violates advisory-only constraint |
| Trigger other agents | Agents do not invoke agents |
| Make decisions | Humans decide, agents advise |
| Block publication | Advisory only, no veto power |
| Access external systems | No network calls, no APIs |
| Write state | No persistence, no logs (except findings) |

---

## Input Contract

ReviewAgent receives:

```json
{
  "draft_id": "string",
  "draft_content": "string",
  "rag_retrieval_ids": ["string"],
  "context": {
    "project_id": "string",
    "domain": "string",
    "event_type": "string"
  }
}
```

### Required Fields

- `draft_id` — Unique identifier for the draft being reviewed
- `draft_content` — The text to analyze
- `rag_retrieval_ids` — IDs of sources used during draft generation

---

## Output Contract

ReviewAgent returns:

```json
{
  "review_id": "string",
  "draft_id": "string",
  "timestamp": "ISO-8601",
  "findings": [
    {
      "finding_id": "string",
      "type": "factual_error | unsupported_claim | missing_context | style_issue",
      "severity": "high | medium | low | info",
      "location": "string (quote or line reference)",
      "description": "string",
      "evidence": {
        "source_ids": ["string"],
        "explanation": "string"
      },
      "suggestion": "string (optional, advisory only)"
    }
  ],
  "summary": {
    "total_findings": 0,
    "high_severity": 0,
    "medium_severity": 0,
    "low_severity": 0,
    "info": 0
  },
  "recommendation": "approve | review_required | major_issues",
  "disclaimer": "This review is advisory only. Human judgment required."
}
```

### Finding Types

| Type | Description |
|------|-------------|
| `factual_error` | Statement contradicts verified source |
| `unsupported_claim` | Statement has no supporting evidence |
| `missing_context` | Important information was omitted |
| `style_issue` | Tone, clarity, or formatting concern |

### Severity Levels

| Severity | Meaning |
|----------|---------|
| `high` | Likely incorrect, should not publish as-is |
| `medium` | Potentially misleading, needs human review |
| `low` | Minor issue, optional to address |
| `info` | Observation only, no action needed |

### Recommendation Values

| Value | Meaning |
|-------|---------|
| `approve` | No significant issues found |
| `review_required` | Human should examine findings before proceeding |
| `major_issues` | Significant problems detected, careful review needed |

---

## Evidence Requirements

All findings MUST include evidence:

- At least one `source_id` from RAG retrieval
- Clear explanation of why the source is relevant
- No findings without citations

If no evidence can be cited, the finding is invalid and must not be included.

---

## Execution Constraints

- ReviewAgent runs **after** DraftAgent
- ReviewAgent requires RAG retrieval (same as DraftAgent)
- ReviewAgent does not block DraftAgent output
- ReviewAgent output is always shown alongside draft

---

## Human-in-the-Loop

ReviewAgent findings are **advisory**.

- Humans read findings
- Humans decide whether to act
- Humans may ignore findings
- Humans may override recommendations

ReviewAgent has no authority to enforce its findings.

---

## Versioning

| Version | Date | Status |
|---------|------|--------|
| v1 | 2025-02 | Draft contract |

---

This document is authoritative for ReviewAgent behavior.
