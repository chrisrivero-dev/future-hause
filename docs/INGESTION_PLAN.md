# Future Hause — Data Ingestion Plan (Draft)

This document tracks *planned* ingestion sources.
No ingestion logic is implemented yet.

## Target Sources (future)
- Freshdesk (tickets, activity logs)
- Reddit (intel signals)
- Project repositories (commits, PRs)
- Company websites (docs, changelogs)

## Constraints
- Ingestion must emit EVT_* events only
- No agent may ingest data directly
- engine/ingest.py will act as the single intake point

⚠️ This file is informational only.
