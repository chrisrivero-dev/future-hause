# Presence Column — Layout Proposal

**Status:** Proposal refinement (not finalized)
**Scope:** Design direction only
**Reference:** Klaus-style presence pattern

---

## Design Intent

**Metaphor:** A coworker standing beside the board.

Future Hause should feel present — not as a tool, but as a quiet collaborator.
The Presence Column gives the system a place to exist without demanding attention.

**Feeling:** Calm, ambient, always visible.

---

## What It IS

- A left-side **Presence Column**
- Avatar at top (the Future Hause icon)
- Name + state beneath (e.g., "Idle", "Thinking", "Observing")
- Subtle divider from main content
- Always visible, never intrusive

## What It Is NOT

- **NOT navigation** — no links, no routing
- **NOT a menu** — no dropdowns, no options
- **NOT interactive** (yet) — no clicks, no toggles
- **NOT a sidebar** — sidebars are for tools; this is for presence

---

## Presence States

The column reflects Future Hause's current awareness:

| State | Meaning | Visual Treatment |
|-------|---------|------------------|
| **Idle** | Waiting, at rest | Static, calm |
| **Thinking** | Processing, contemplating | Soft breathe animation |
| **Observing** | Actively watching signals | Subtle pulse |

State is read-only. It reflects engine status, not user input.

---

## Visual Structure

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                      │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│  ┌────┐  │  Activity Feed                                   │
│  │    │  │                                                  │
│  │ FH │  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │    │  │  │      │  │      │  │      │  │      │         │
│  └────┘  │  │ Col1 │  │ Col2 │  │ Col3 │  │ Col4 │         │
│          │  │      │  │      │  │      │  │      │         │
│  Future  │  └──────┘  └──────┘  └──────┘  └──────┘         │
│  Hause   │                                                  │
│          │  [Action Log]                                    │
│  Idle    │  [System Metadata]                               │
│          │                                                  │
│          │                                                  │
│          │                                                  │
├──────────┴──────────────────────────────────────────────────┤
│ FOOTER                                                      │
└─────────────────────────────────────────────────────────────┘
```

**Column contents (top to bottom):**
1. **Avatar** — Future Hause icon (state-aware)
2. **Name** — "Future Hause" (static text)
3. **State** — Current state label (Idle / Thinking / Observing)
4. **Empty space** — Column extends down, ambient presence

**Main content area:**
- Shifts right to make room
- Moves up (no icon in section header anymore)
- Breathes with more vertical space

---

## Column Specifications

| Property | Value | Notes |
|----------|-------|-------|
| Width | ~80-96px | Narrow but readable |
| Position | Sticky | Stays visible on scroll |
| Background | Transparent or subtle | Not dominant |
| Divider | 1px subtle border | Separates from content |
| Avatar size | 48-56px | Prominent but not huge |
| Name text | Small, muted | Secondary to avatar |
| State text | Small, mono | Reflects current state |

---

## Comparison: Before and After

**Before:**
- Icon embedded in section header
- Mixed with "Activity Feed" title
- Feels like decoration

**After:**
- Icon has dedicated home
- Name and state clearly visible
- Feels like a presence

---

## Animation Inheritance

Existing icon animation states apply to avatar:

| State | Animation | Duration |
|-------|-----------|----------|
| `idle` | None (static) | — |
| `thinking` | Soft breathe | 3s ease-in-out |
| `processing` | Horizontal shift | 1.2s ease-in-out |
| `success` | Green glow | 2s ease-in-out |
| `error` | Shake + red glow | 0.5s |

No new animations required.

---

## Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| Desktop (>1024px) | Column on left, content on right |
| Tablet (≤1024px) | Column collapses to horizontal strip |
| Mobile (≤768px) | Minimal: avatar + state only |

On smaller screens, the "coworker" steps back but remains visible.

---

## What This Proposal Does NOT Include

- No implementation code
- No CSS changes (yet)
- No HTML changes (yet)
- No JavaScript logic
- No data fetching
- No interactive behavior
- No navigation

---

## Open Questions

1. **Name visibility** — Should "Future Hause" text always show, or only on hover?
2. **State mapping** — What engine states map to "Observing"?
3. **Column width** — 72px (current) vs 96px (more readable)?
4. **Sticky behavior** — Full height sticky, or scroll with content?
5. **Feed placeholder** — Keep the placeholder area, or remove entirely?

---

## Next Steps (If Approved)

1. Finalize column width and spacing
2. Update HTML structure (move icon, add name/state text)
3. Refine CSS for column layout
4. Map engine states to presence states
5. Test responsive collapse behavior

---

**Version:** Proposal v1 (Klaus-aligned)
**Status:** Awaiting design approval
