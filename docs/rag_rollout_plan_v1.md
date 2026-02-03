# Future Hause — RAG Rollout Plan (v1)

This document defines the rollout plan for the RAG layer.

**Freshdesk AI is the first project to receive RAG.**

---

## Why Freshdesk AI First

### Rationale

| Reason | Explanation |
|--------|-------------|
| Highest signal volume | Most active project with frequent intel ingestion |
| Clearest use case | Support-related drafts benefit most from grounded retrieval |
| Best-defined sources | Existing documentation and KB structure |
| Lowest risk | Errors are advisory, not customer-facing |
| Fastest feedback loop | Active usage means quick iteration |

### Secondary Considerations

- Freshdesk AI has the most mature contracts
- DraftAgent is already scoped for this project
- Success here validates the architecture for other projects

---

## Initial Sources (Freshdesk AI)

### Included

| Source | Type | Description |
|--------|------|-------------|
| `docs/fh-constitution.md` | policy | Core behavioral contract |
| `docs/llm-routing.md` | contract | Intent classification rules |
| `docs/intelligence_contract_v0.md` | contract | DraftAgent intelligence rules |
| `docs/agent_architecture_v1.md` | guide | Agent structure and boundaries |
| `docs/events.md` | contract | Event model definitions |
| Freshdesk KB articles | guide | Approved knowledge base content |
| Freshdesk canned responses | guide | Approved response templates |

### Explicitly Excluded

| Source | Reason |
|--------|--------|
| Customer tickets | Privacy, PII risk |
| Internal Slack | Unverified, ephemeral |
| Reddit raw data | Unverified, needs curation |
| Draft content | Ephemeral, not authoritative |
| User notes | Not yet approved |
| External URLs | Not verified, version unknown |

### Future Consideration

- Curated Reddit summaries (after human review)
- Approved external documentation (explicitly versioned)
- Historical action log entries (after retention policy defined)

---

## Rollout Phases

### Phase 0: Specification (Current)

- Define RAG spec (complete)
- Define ReviewAgent contract (complete)
- Define rollout plan (this document)
- No code, no implementation

### Phase 1: Index Creation

- Index Freshdesk AI sources only
- Validate tagging model
- Manual verification of indexed content
- No agent integration yet

### Phase 2: DraftAgent Integration

- Connect DraftAgent to RAG retrieval
- Enforce "no retrieval → no generation" rule
- Log retrieval IDs with all outputs
- Human review of grounded drafts

### Phase 3: ReviewAgent Integration

- Connect ReviewAgent to RAG retrieval
- Generate findings for all drafts
- Display findings alongside drafts
- Gather feedback on finding quality

### Phase 4: Evaluation

- Measure grounding accuracy
- Measure finding relevance
- Identify missing sources
- Decide on expansion to other projects

---

## Success Criteria

RAG is considered "working" when:

| Criterion | Measurement |
|-----------|-------------|
| Retrieval returns relevant content | >80% of queries return at least 1 relevant chunk |
| Drafts cite sources | 100% of drafts include retrieval IDs |
| No hallucination | 0% of drafts contain claims not in sources |
| Review findings are actionable | >70% of findings cite valid sources |
| No false positives | <20% of findings are irrelevant |
| Human trust | Users report increased confidence in drafts |

### Failure Criteria

RAG rollout is paused if:

- Retrieval consistently returns irrelevant content
- Drafts routinely cite incorrect sources
- ReviewAgent findings are consistently wrong
- Users lose trust in grounded content

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Stale sources | Require `last_verified` timestamp, alert on age |
| Missing coverage | Track "no results" queries, expand sources |
| Over-reliance | Always show source IDs, encourage verification |
| Index corruption | Immutable indexing, version control |

---

## Timeline

This is a plan, not a commitment.

| Phase | Status |
|-------|--------|
| Phase 0: Specification | In progress |
| Phase 1: Index Creation | Not started |
| Phase 2: DraftAgent Integration | Not started |
| Phase 3: ReviewAgent Integration | Not started |
| Phase 4: Evaluation | Not started |

No dates are assigned. Progress is gated by human approval.

---

## Out of Scope

The following are explicitly NOT part of this rollout:

- Embedding model selection
- Vector store implementation
- Chunking strategy
- Query optimization
- Multi-project indexing
- Real-time ingestion
- Automated source updates

These decisions are deferred until Phase 1 begins.

---

## Versioning

| Version | Date | Status |
|---------|------|--------|
| v1 | 2025-02 | Draft plan |

---

This document is authoritative for RAG rollout decisions.
