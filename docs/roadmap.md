# Future Hause — Roadmap

## Phase 0 (Complete)
- Agent architecture defined
- Event model defined
- Agent runner skeleton (blocked)
- Ingestion skeleton (blocked)
- RAG specs and rollout plan
- ReviewAgent contract
- ProjectFocusAgent contract

## Phase 1 (Design Only)
- Ingest payload contract
- ProjectFocusAgent UI contract
- OpsLedger event schema

## Phase 2 (Read-Only Wiring)
- Ingest emits EVT_INTEL_INGESTED (disabled by default)
- ProjectFocusAgent consumes events (read-only)
- No agent execution enabled

## Phase 3 (Controlled Enablement)
- DraftAgent RAG-enabled (Freshdesk AI only)
- ReviewAgent critiques drafts
- OpsLedger logs actions

## Phase 4 (Automation, Optional)
- Selective auto-draft
- Human-in-the-loop gates
- Metrics & regressions

No phase may begin without explicit approval.
