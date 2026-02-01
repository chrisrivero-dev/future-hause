# Presence Rail — Layout Proposal

**Status:** Exploratory (not finalized)
**Scope:** CSS + minimal HTML changes only
**Reversibility:** Full (additive changes, no destructive edits)

---

## Concept

A narrow left-side rail dedicated to Future Hause's system presence.

**Goals:**
- Visually separate system awareness from intelligence content
- Give the icon and status a clear, intentional home
- Allow main dashboard columns to move up and breathe

**Constraints:**
- Passive only (no controls, no mutations, no navigation)
- No new data fetching
- No new logic
- Narrow (~72px)

---

## Current Layout

```
┌──────────────────────────────────────────────────────────┐
│ HEADER                                                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [icon] Activity Feed                                    │
│                                                          │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                 │
│  │ Col1 │  │ Col2 │  │ Col3 │  │ Col4 │                 │
│  │      │  │      │  │      │  │      │                 │
│  └──────┘  └──────┘  └──────┘  └──────┘                 │
│                                                          │
│  [Action Log]                                            │
│  [System Metadata]                                       │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ FOOTER                                                   │
└──────────────────────────────────────────────────────────┘
```

---

## Proposed Layout

```
┌──────────────────────────────────────────────────────────┐
│ HEADER                                                   │
├────────┬─────────────────────────────────────────────────┤
│        │                                                 │
│ ┌────┐ │  Activity Feed                                  │
│ │icon│ │                                                 │
│ └────┘ │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│        │  │ Col1 │  │ Col2 │  │ Col3 │  │ Col4 │        │
│ status │  │      │  │      │  │      │  │      │        │
│  text  │  └──────┘  └──────┘  └──────┘  └──────┘        │
│        │                                                 │
│ ······ │  [Action Log]                                   │
│ feed   │  [System Metadata]                              │
│ ······ │                                                 │
│        │                                                 │
├────────┴─────────────────────────────────────────────────┤
│ FOOTER                                                   │
└──────────────────────────────────────────────────────────┘
```

---

## HTML Structure Changes

**New wrapper inside `<main class="dashboard-main">`:**

```html
<main class="dashboard-main">
  <div class="dashboard-layout">

    <!-- NEW: Presence Rail -->
    <aside class="presence-rail" aria-label="System Presence">
      <div class="presence-icon-wrapper" id="dashboard-icon" data-state="idle">
        <img src="./icon.svg" class="presence-icon" alt="Future Hause" width="48" height="48" />
      </div>
      <div class="presence-status">
        <span class="presence-status-text">Idle</span>
      </div>
      <div class="presence-feed" aria-label="Active Feed (placeholder)">
        <!-- Optional: visual activity indicator -->
        <div class="presence-feed-empty">—</div>
      </div>
    </aside>

    <!-- Existing content moves here -->
    <div class="dashboard-content">
      <section class="primary-intelligence">...</section>
      <div class="secondary-sections">...</div>
    </div>

  </div>
</main>
```

**Removed from current location:**
- Icon wrapper moves from `.section-header` to `.presence-rail`

---

## CSS Changes

### New: Dashboard Layout Container

```css
.dashboard-layout {
  display: flex;
  gap: var(--spacing-lg);
  align-items: flex-start;
}

.dashboard-content {
  flex: 1;
  min-width: 0;  /* Prevent grid blowout */
}
```

### New: Presence Rail Styles

```css
/* ----------------------------------------------------------------------------
   PRESENCE RAIL — System Awareness Surface
   - Narrow, passive, read-only
   - Contains: icon (state-aware), status text, feed placeholder
   - No controls, no mutations
   ---------------------------------------------------------------------------- */

.presence-rail {
  width: 72px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-md) 0;

  /* Visual treatment: subtle, not dominant */
  background: transparent;
  border-right: 1px solid var(--border-color-subtle);
}

/* Icon container — inherits existing animation states */
.presence-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  will-change: transform, filter, opacity;
  backface-visibility: hidden;
}

.presence-icon {
  width: 48px;
  height: 48px;
  display: block;
  pointer-events: none;
}

/* Status text — one line, muted */
.presence-status {
  text-align: center;
  padding: 0 var(--spacing-xs);
}

.presence-status-text {
  font-size: 0.65rem;
  font-family: var(--font-mono);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Feed placeholder — visual only */
.presence-feed {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm);
  overflow: hidden;
}

.presence-feed-empty {
  font-size: 0.7rem;
  color: var(--text-muted);
  opacity: 0.5;
}

/* Optional: subtle activity dots (visual only, no data) */
.presence-feed-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--text-muted);
  opacity: 0.3;
  margin-bottom: var(--spacing-xs);
}
```

### Responsive: Collapse on Mobile

```css
@media (max-width: 768px) {
  .dashboard-layout {
    flex-direction: column;
  }

  .presence-rail {
    width: 100%;
    flex-direction: row;
    justify-content: center;
    border-right: none;
    border-bottom: 1px solid var(--border-color-subtle);
    padding: var(--spacing-sm) var(--spacing-md);
    gap: var(--spacing-md);
  }

  .presence-feed {
    display: none;  /* Hide feed on mobile */
  }

  .presence-icon-wrapper {
    width: 32px;
    height: 32px;
  }

  .presence-icon {
    width: 32px;
    height: 32px;
  }
}
```

---

## Section Header Adjustment

With icon moved to rail, simplify the section header:

```css
.section-header {
  margin-bottom: var(--spacing-lg);
  /* Remove flex layout if icon is gone */
}

.section-title {
  /* Remains as-is */
}
```

---

## Animation State Inheritance

Existing icon animation states apply to `.presence-icon-wrapper`:

| State | Animation | Notes |
|-------|-----------|-------|
| `idle` | none | Static |
| `processing` | `icon-processing-shift` | Horizontal motion |
| `thinking` | `icon-thinking-breathe` | Soft scale pulse |
| `success` | `icon-success-glow` | Green drop-shadow |
| `error` | `icon-error-shake` | Red shake |

No changes to keyframes required.

---

## What This Proposal Does NOT Include

- No new JavaScript logic
- No new data sources
- No fetch calls
- No interactive controls
- No navigation
- No mutations
- No finalization

---

## Open Questions

1. Should the feed placeholder show activity dots, or remain empty?
2. Should status text reflect `data-state` (e.g., "Processing..." when active)?
3. Should rail have a subtle background, or remain transparent?
4. Should rail stick to viewport, or scroll with content?

---

## Reversal Path

To remove:
1. Delete `.presence-rail` element from HTML
2. Delete `.dashboard-layout` wrapper
3. Restore icon to `.section-header`
4. Remove CSS additions (rail, layout)

All changes are additive and isolated.

---

**Version:** Proposal v0
**Status:** Awaiting review
