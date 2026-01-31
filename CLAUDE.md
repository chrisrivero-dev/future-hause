# CLAUDE.md — AI Assistant Guide for Future Hause

This document provides essential context for AI assistants working with the Future Hause codebase.

---

## Project Overview

**Future Hause** is a local support intelligence assistant that collects support signals (e.g., Reddit posts), logs what it did, and produces structured artifacts for human review.

**Core principle:** Future Hause is an **analyst, not an actor**. It never talks to customers, makes decisions, or publishes content automatically.

**Current version:** v0.1 (in progress)

---

## Philosophy (CRITICAL)

These principles MUST be respected in all contributions:

1. **Human-in-the-loop by design** — All autonomous behavior is forbidden
2. **Transparency over autonomy** — Record everything, decide nothing
3. **Evidence before conclusions** — Raw data first, analysis later
4. **Boring, reliable automation** — No "AI magic," no customer-facing chat

If a feature looks like a "bot employee," it is out of scope.

---

## Repository Structure

```
future-hause/
├── config/
│   └── future_hause.yaml       # Main configuration (version, scope, safety)
├── docs/
│   ├── UI_LOCK.md              # UI finalization constraints
│   ├── animation_states.yaml   # 6 defined animation states
│   ├── dashboard_panels.yaml   # Panel-to-state mappings
│   ├── ui_state_contract.md    # Engine ↔ UI contract
│   └── ui_states.md            # UI state visual mappings
├── engine/
│   ├── run.py                  # Main execution script
│   └── resolve_animation.py    # Animation state resolver
├── ui/
│   ├── index.html              # Main dashboard HTML
│   ├── dashboard.js            # State toggle logic (demo)
│   ├── status-renderer.js      # Engine → UI renderer
│   ├── animations.css          # State-driven CSS animations
│   ├── dashboard.css           # Layout and styling
│   ├── styles.css              # Base styles
│   └── icon.svg                # Assistant icon (inline SVG)
├── README.md                   # Project overview
└── CLAUDE.md                   # This file
```

**Runtime files (gitignored, created at runtime):**
- `engine/state.json` — Current engine state
- `engine/log.json` — Timestamped event log
- `engine/status.json` — Status for UI consumption
- `data/raw/` — Collected signal data

---

## v0.1 Scope (LOCKED)

v0.1 does **only** the following:
- Collect Reddit posts (read-only)
- Save raw data locally
- Record job state: `idle → collecting → done`
- Log what happened during a run

**Explicitly excluded from v0.1:**
- No analysis
- No AI/LLM calls
- No UI interactions (read-only dashboard only)
- No network calls to external services

---

## State Machine

The engine uses a simple state machine:

| State | Meaning | Animation |
|-------|---------|-----------|
| `idle` | Engine is not running | `pulse-slow` |
| `collecting` | Actively collecting signals | `spin` |
| `done` | Completed successfully | `glow` |
| `error` | Failed, attention needed | `shake` |

The UI MUST react strictly to `engine/state.json`. The UI MUST NOT guess or infer state.

---

## Running the Engine

```bash
python engine/run.py
```

This will:
1. Load `config/future_hause.yaml`
2. Set state to `collecting`
3. Run enabled collectors (currently Reddit stub)
4. Write logs to `engine/log.json`
5. Set state to `done`

---

## Code Conventions

### Python (engine/)

- **Python 3.10+** required (uses `str | None` syntax)
- Use `pathlib.Path` for all path operations
- Use `yaml.safe_load()` for YAML parsing
- Function names: `snake_case`
- Explicit error messages in exceptions
- No side effects in pure functions (e.g., `resolve_animation`)

### JavaScript (ui/)

- **Vanilla JavaScript only** — no frameworks
- Use `querySelector` / `getElementById` with null checks
- Variable names: `camelCase`
- Clearly mark demo code with `// DEMO ONLY` comments
- Public API via `window.renderStatus(payload)`

### CSS (ui/)

- CSS Variables for theming (defined in `:root`)
- State classes: `state-{animation-name}` pattern
- Support `prefers-reduced-motion` and `prefers-contrast`
- Use `will-change` and `backface-visibility` for performance

### HTML

- Semantic markup: `<header>`, `<main>`, `<aside>`, `<section>`
- ARIA labels for accessibility
- Inline SVG for animation hooks

---

## Configuration Files

### config/future_hause.yaml

Main configuration with:
- `version` — Current version
- `mode` — `local_only` (no external connections)
- `scope.collect` — Which collectors are enabled
- `safety.human_in_loop_required` — Must be `true`
- `safety.auto_actions` — Must be `false`

### docs/animation_states.yaml

Defines 6 animations with intent and intensity:
- `pulse-slow` — Idle/waiting (low)
- `spin` — Active processing (medium)
- `glow` — Success/complete (medium)
- `shake` — Error/attention (high)
- `slide-in` — New information (medium)
- `dim` — Inactivity (low)

### docs/dashboard_panels.yaml

Maps panels to data sources and animations.

---

## UI Contract

From `docs/ui_state_contract.md`:

1. UI MUST read `engine/status.json`
2. UI MUST NOT guess state
3. UI MUST NOT trigger engine actions
4. UI MUST be read-only in v0.x
5. Animations are visual reflections of state only

---

## UI Lock Policy

From `docs/UI_LOCK.md`:

- UI is finalized
- No new panels without justification
- No charts until a metric proves its value
- Icon states drive layout, not vice versa

---

## Development Guidelines

### DO

- Add logging with `log_event()` for all significant actions
- Write state changes to `engine/state.json`
- Keep collectors read-only (no writes to external systems)
- Follow the existing code patterns
- Update documentation when adding features

### DO NOT

- Add auto-publishing or auto-actions
- Make the engine "smart" or autonomous
- Add customer-facing features
- Skip human review steps
- Add LLM/AI features in v0.1

---

## Testing

Currently uses demo controls in the UI for manual testing:
- Demo buttons in `ui/index.html` trigger state changes
- `window.renderStatus(payload)` can be called from console

No automated test framework yet.

---

## Planned Future Versions

- **v0.2** — Batch builder, structured datasets
- **v0.3** — Claude-assisted analysis, draft KB articles
- **v0.4+** — Read-only dashboard, state visualization, review interface

These are ideas, not commitments.

---

## Quick Reference

| Task | Command/Location |
|------|------------------|
| Run engine | `python engine/run.py` |
| Main config | `config/future_hause.yaml` |
| Engine state | `engine/state.json` (runtime) |
| Event log | `engine/log.json` (runtime) |
| UI entry point | `ui/index.html` |
| Animation defs | `docs/animation_states.yaml` |
| State contract | `docs/ui_state_contract.md` |

---

## Common Pitfalls

1. **Don't add autonomy** — Every feature needs human approval
2. **Don't skip state logging** — All transitions must be recorded
3. **Don't modify the UI arbitrarily** — Check `UI_LOCK.md` first
4. **Don't add external API calls in v0.1** — Local-only scope
5. **Don't infer state in UI** — Always read from engine state files
