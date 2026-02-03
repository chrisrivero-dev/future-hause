# Future Hause — Event Model (v1)

This document defines the authoritative event contracts used to invoke agents
within the Future Hause system.

Events are **data**, not behavior.

If an event is not defined here, it is invalid by definition.

---

## Core Principles

- Events do not execute agents directly
- Events are emitted by humans or system actions
- Events are consumed by the agent runner
- Agents never self-invoke

---

## Event Envelope (Base Schema)

All events MUST conform to this base structure.

```json
{
  "event": "EVT_*",
  "timestamp": "ISO-8601",
  "source": "human | system",
  "project": "futurehub | help-nearby | freshdesk-ai | other",
  "payload": {}
}
```

---

## Defined Events

### EVT_INTEL_INGESTED

Emitted when new raw intel is observed.

```json
{
  "event": "EVT_INTEL_INGESTED",
  "timestamp": "ISO-8601",
  "source": "system",
  "project": "freshdesk-ai",
  "payload": {
    "source_type": "reddit | notes | external",
    "confidence": 0.0
  }
}
```

### EVT_DRAFT_REQUESTED

Emitted when a human explicitly requests a draft.

```json
{
  "event": "EVT_DRAFT_REQUESTED",
  "timestamp": "ISO-8601",
  "source": "human",
  "project": "futurehub",
  "payload": {
    "target": "doc | code | config",
    "context": "free text"
  }
}
```

### EVT_DOC_REVIEW_REQUESTED

Emitted when a human approves a documentation rewrite.

```json
{
  "event": "EVT_DOC_REVIEW_REQUESTED",
  "timestamp": "ISO-8601",
  "source": "human",
  "project": "help-nearby",
  "payload": {
    "file": "docs/example.md"
  }
}
```

### EVT_CODE_REVIEW_REQUESTED

Emitted when a human requests refactor analysis.

```json
{
  "event": "EVT_CODE_REVIEW_REQUESTED",
  "timestamp": "ISO-8601",
  "source": "human",
  "project": "futurehub",
  "payload": {
    "files": ["ui/dashboard.js"]
  }
}
```

### EVT_DEPLOY_COMPLETE

Emitted after deployment finishes.

```json
{
  "event": "EVT_DEPLOY_COMPLETE",
  "timestamp": "ISO-8601",
  "source": "system",
  "project": "futurehub",
  "payload": {
    "commit": "sha"
  }
}
```

### EVT_LOG_WINDOW_READY

Emitted when a log review window closes.

```json
{
  "event": "EVT_LOG_WINDOW_READY",
  "timestamp": "ISO-8601",
  "source": "system",
  "project": "any",
  "payload": {
    "window_start": "ISO-8601",
    "window_end": "ISO-8601"
  }
}
```

### EVT_ACTION_COMPLETED

Emitted after an approved action finishes.

```json
{
  "event": "EVT_ACTION_COMPLETED",
  "timestamp": "ISO-8601",
  "source": "system",
  "project": "freshdesk-ai",
  "payload": {
    "agent": "RefactorAgent",
    "commit": "sha"
  }
}
```

### EVT_PROJECT_SELECTED

Emitted when the active project changes in the dashboard.

```json
{
  "event": "EVT_PROJECT_SELECTED",
  "timestamp": "ISO-8601",
  "source": "human",
  "project": "freshdesk-ai",
  "payload": {}
}
```

---

This file is authoritative.
