# Future Hause — RAG Layer Specification (v1)

This document defines the retrieval-augmented generation (RAG) layer
used by Future Hause agents.

RAG is **infrastructure**, not an agent.

---

## Scope

### What RAG Is

- A retrieval layer that runs **before** generation
- Infrastructure shared by DraftAgent and ReviewAgent
- A source of grounded, citable material

### What RAG Is Not

- Not an agent
- Not a decision-maker
- Not a state modifier

### Execution Order

```
Event → RAG Retrieval → Agent (DraftAgent / ReviewAgent) → Output
```

RAG always runs first. If retrieval fails or returns nothing, generation is blocked.

---

## Sources (Initial)

| Source | Description | Priority |
|--------|-------------|----------|
| `docs/` | Authoritative rules, contracts, policies | Highest |
| Project knowledge bases | Per-project curated documentation | High |
| Curated links | Explicitly versioned external references | Medium |

### Explicitly Excluded

- Unverified external URLs
- User-submitted content (until approved)
- Logs older than retention window
- Draft content (ephemeral, not citable)

---

## Tagging Model

All RAG-indexed content must include the following metadata:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the chunk |
| `project_id` | string | Associated project (nullable for global) |
| `domain` | enum | `freshdesk-ai` \| `help-nearby` \| `futurehub` \| `global` |
| `source_type` | enum | `policy` \| `guide` \| `log` \| `link` \| `contract` |
| `last_verified` | ISO-8601 | When the source was last verified as accurate |
| `version` | string | Document version (if applicable) |

### Example Tag

```json
{
  "id": "doc-fh-constitution-001",
  "project_id": "futurehub",
  "domain": "futurehub",
  "source_type": "policy",
  "last_verified": "2025-01-15T00:00:00Z",
  "version": "v0"
}
```

---

## Constraints

### DraftAgent Constraints

- May **only** cite retrieved material
- No retrieval → no generation (hard block)
- Must include retrieval set IDs in output metadata

### ReviewAgent Constraints

- May **only** reference retrieved material for evidence
- Cannot generate new content
- Must cite source IDs for all findings

### Logging Requirements

- Retrieval set must be logged (IDs only, not content)
- Query must be logged (sanitized)
- Timestamp must be logged

### What Is NOT Logged

- Full retrieved content (too large)
- Embedding vectors
- Internal similarity scores

---

## Retrieval Behavior

### Query Construction

- Derived from event payload and context
- No user input passed directly to retrieval
- Query is deterministic given event + state

### Result Limits

- Maximum 10 chunks per retrieval
- Chunks must meet minimum relevance threshold
- Threshold is configurable but defaults to conservative

### Failure Modes

| Failure | Behavior |
|---------|----------|
| No results | Block generation, return advisory |
| Timeout | Block generation, log error |
| Invalid query | Block generation, raise validation error |

---

## Implementation Notes

This specification defines **what** RAG does, not **how**.

Implementation decisions (embeddings, vector store, chunking strategy)
are deferred and will be documented separately when ready.

---

## Versioning

| Version | Date | Status |
|---------|------|--------|
| v1 | 2025-02 | Draft specification |

---

This document is authoritative for RAG layer behavior.
