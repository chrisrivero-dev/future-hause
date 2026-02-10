# Dashboard Scope Contract

## Purpose
This contract defines the role and limits of the Future Hause dashboard.

It exists to prevent UI-driven scope creep.

---

## Dashboard Role

The dashboard is:
- A summary surface
- A signal viewer
- A read-only observability layer

The dashboard is NOT:
- A system of record
- A command interface
- A place for state mutation

---

## Panel Behavior Rules

- Panels may auto-expand vertically up to a defined maximum height
- Panels do NOT auto-expand horizontally
- Overflow is handled via scroll or drill-in views
- Panels may optionally support manual vertical resizing

---

## Interaction Rules

- No dashboard panel may mutate state
- All actions must originate from conversation
- Drill-in views provide detail, not authority

---

## Explicit Prohibitions

The dashboard may NEVER:
- Become a dumping ground for all data
- Replace conversation as the primary interface
- Execute actions directly

---

## Governing Principle
Dashboard shows.
Conversation decides.
