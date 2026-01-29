# Future Hause — UI State Contract (v0.1)

This document defines the only states the Future Hause UI may display.
The UI must never infer or invent state. It reacts strictly to `engine/status.json`.

---

## Engine States

### idle
- Meaning: Engine is not running
- UI:
  - Assistant icon: calm / neutral
  - Status text: "Idle"
  - No animation

---

### starting
- Meaning: Engine process has launched
- UI:
  - Assistant icon: subtle pulse
  - Status text: "Starting up…"
  - Disable actions

---

### collecting
- Meaning: Engine is actively collecting signals
- UI:
  - Assistant icon: thinking animation
  - Status text: "Collecting signals"
  - Show active sources (e.g. Reddit)

---

### done
- Meaning: Engine completed successfully
- UI:
  - Assistant icon: satisfied / completed
  - Status text: "Up to date"
  - Show summary counts

---

### error
- Meaning: Engine failed
- UI:
  - Assistant icon: warning / alert
  - Status text: "Attention needed"
  - Display last error from log

---

## Rules

- UI MUST read `engine/status.json`
- UI MUST NOT guess state
- UI MUST NOT trigger engine actions
- UI MUST be read-only in v0.x

---

## Animation Policy

Animations are visual reflections of state only.
They do not represent reasoning or intelligence.

