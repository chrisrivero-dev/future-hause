# Future Hause – UI State & Animation Contract

This document defines how the Future Hause assistant may visually represent
system state in a future dashboard or avatar.

Visuals must reflect real system state only.
No visuals may imply intent, judgment, or autonomy.

---

## State Mapping

### idle
- Meaning: System is inactive
- Avatar: Neutral
- Motion: None
- Notes: Default resting state

### collecting
- Meaning: Data ingestion in progress
- Avatar: Subtle pulse or glow
- Motion: Slow, rhythmic
- Notes: Indicates background activity, not “thinking”

### done
- Meaning: Run completed successfully
- Avatar: Steady highlight
- Motion: None
- Notes: Awaiting human review

### error
- Meaning: Run failed or blocked
- Avatar: Dimmed or muted
- Motion: None
- Notes: User should check logs

---

## Non-Goals

- No emotional expressions
- No conversational cues
- No autonomous behavior indicators
- No progress bars without real metrics

---

## Design Principle

Future Hause visualizes **process state**, not cognition.
