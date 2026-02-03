# Claude Handoff Notes

Current state:
- All agent contracts are authoritative
- Agent runner and ingestion are skeletons only
- No execution is enabled
- No agent may be activated without instruction

Rules:
- Do not modify existing docs unless asked
- Do not wire agents together
- Do not emit events unless explicitly told
- Prefer documentation over code
- Default to read-only designs

When in doubt: ask before acting.
