# CLAUDE.md — AI Assistant Guide for Future Hause

This document provides essential context for AI assistants working with the Future Hause codebase.

---

## Project Overview

**Future Hause** is a local support intelligence and project analysis assistant.

It observes public and internal signals related to a target company (currently: FutureBit), including:
- Community discussions (e.g., Reddit)
- Official websites and documentation
- Release notes and announcements

It synthesizes new or changed information and produces structured artifacts for human review, such as:
- Knowledge base opportunities
- Canned responses opportunities
- Documentation gaps
- Project status summaries
- Action and insight logs

Future Hause does not take autonomous action. It does not publish content, contact customers, modify production systems, or execute decisions.

**Core principle:** Future Hause is an **analyst, not an actor**. A human is always the final decision-maker.

**Current version:** v0.1 (in progress)
## Scope Clarification

v0.1 implements a limited subset of the long-term vision.

Currently implemented:
- Reddit signal collection
- State logging and artifact generation

Planned (not yet implemented):
- Official website and documentation monitoring
- Knowledge base gap detection
- Project and deliverable tracking
- Progress summaries and recommendations

AI assistants must not assume planned features exist unless explicitly implemented.


---

## Output Contract (v0.1 — Frozen)

Future Hause produces structured, read-only intelligence artifacts under the `/outputs/` directory.
These artifacts are the sole source of truth for downstream analysis and UI rendering.

The following output files are considered core for v0.1:

- `intel_events.json` — Observed external signals and detected changes
- `kb_opportunities.json` — Suggested knowledge base gaps or updates
- `projects.json` — System-derived project state and deliverables (fully automatic)
- `action_log.json` — Traceable recommendations and rationale

Design rules:
- Outputs are append-only and human-reviewable
- Field names are explicit by design
- Confidence scoring is intentionally excluded
- Outputs may expand beyond these four files in future versions without breaking compatibility

AI assistants must not alter schemas or introduce new output structures without explicit human approval.

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
│   └── assets/
│       └── future-hause-icon.svg   # Dashboard icon (FROZEN)
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
- External SVG via `<img>` for icons (no inline SVG)

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

## Dashboard Icon (FROZEN)

**Single source of truth:** `ui/assets/future-hause-icon.svg`

Verification hash: `APPROVED_FH_ICON_v1_SHA: 7d3c9e1`

Rules:
1. **No inline SVG** — The icon MUST be loaded via `<img src="./assets/future-hause-icon.svg">`
2. **No redesign** — Do not regenerate, approximate, or substitute the SVG
3. **Wrapper-only animations** — CSS animations target `.dashboard-icon-wrapper`, not SVG internals
4. **Fail silently** — Animations must degrade gracefully when `prefers-reduced-motion` is set

Animation states (applied to wrapper):
| State | Animation | Effect |
|-------|-----------|--------|
| `idle` | `icon-idle-pulse` | Subtle opacity pulse |
| `processing` | `icon-processing-spin` | Full rotation |
| `success` | `icon-success-glow` | Green drop-shadow |
| `error` | `icon-error-shake` | Horizontal shake + red glow |

AI assistants must NOT modify the icon SVG without explicit human approval.

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
| Dashboard icon | `ui/assets/future-hause-icon.svg` (FROZEN) |
| Animation defs | `docs/animation_states.yaml` |
| State contract | `docs/ui_state_contract.md` |

---

## Common Pitfalls

1. **Don't add autonomy** — Every feature needs human approval
2. **Don't skip state logging** — All transitions must be recorded
3. **Don't modify the UI arbitrarily** — Check `UI_LOCK.md` first
4. **Don't add external API calls in v0.1** — Local-only scope
5. **Don't infer state in UI** — Always read from engine state files
6. **Don't modify or inline the icon** — Use `ui/assets/future-hause-icon.svg` via `<img>` only
