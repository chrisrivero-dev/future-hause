# Intelligence Contract v0

---

## New Intel

**Purpose:**
Represents raw, uncommitted signals or observations.

**Sources (abstract):**
- External (community, updates, chatter)
- Internal (projects, past actions)
- Self-reflection (patterns noticed)

**Required fields:**
- id
- source_type
- summary
- related_projects[]
- confidence
- created_at

---

## KB Opportunity

**Purpose:**
Identified documentation or response gaps.

**Derived from:**
- Intel
- Repeated issues
- Confusion patterns

**Required fields:**
- id
- originating_intel_id
- gap_type
- evidence_refs[]
- suggested_action

---

## Recommendation

**Purpose:**
Human-actionable suggestion.

**Rules:**
- Never auto-executed
- Always explainable

**Required fields:**
- id
- rationale
- source_intel_ids[]
- impact_level
- reversible (true/false)

---

## Action Log

**Purpose:**
Immutable audit trail.

**Logged events:**
- Accept recommendation
- Dismiss intel
- Promote intel → project

**Required fields:**
- id
- timestamp
- action_type
- target_id
- rationale
