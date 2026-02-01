# Intelligence Pipeline v0

**Canonical contract:** `docs/intelligence_contract_v0.md`

This document defines the local-first intelligence pipeline for Future Hause.
It describes how raw inputs become structured intelligence artifacts.

**Core principle:** Humans decide. The system advises.

---

## Pipeline Overview

```
Raw Inputs
    ↓
[Stage 1: Local Inference]  →  Candidate New Intel
    ↓
[Stage 2: Mid-Tier Synthesis]  →  Cleaned New Intel + Candidate KB Opportunities
    ↓
[Stage 3: Final Clarity Pass]  →  Explainable Recommendations
    ↓
Human Review
    ↓
Action Log (human actions only)
```

---

## Stage 1: Local Inference

**Provider:** Ollama / Mistral (local)

**Role:** Pattern spotting only

**Inputs:**
- Raw signals (community posts, release notes, documentation changes)
- Existing project context (read-only)

**Outputs:**
- Candidate New Intel objects

**Contract fields populated:**
- `id` — generated locally
- `source_type` — external / internal / self-reflection
- `summary` — raw observation, unedited
- `related_projects[]` — empty (not inferred at this stage)
- `confidence` — not set (deferred to Stage 2)
- `created_at` — timestamp of observation

**Allowed operations:**
- Detect change or novelty
- Extract factual observations
- Tag source type

**Forbidden operations:**
- Ranking or prioritization
- Synthesis across signals
- Language normalization
- Confidence scoring
- Generating recommendations
- Linking to projects

**Guardrails:**
- Output is append-only to staging area
- No promotion to official New Intel
- No cross-referencing between candidates
- Must preserve original wording

---

## Stage 2: Mid-Tier Synthesis

**Provider:** OpenAI

**Role:** Normalize, deduplicate, and cross-link

**Inputs:**
- Candidate New Intel objects from Stage 1
- Existing New Intel (read-only, for deduplication)
- Project registry (read-only, for linking)

**Outputs:**
- Cleaned New Intel (ready for human review)
- Candidate KB Opportunities

**Contract fields populated (New Intel):**
- `id` — preserved from Stage 1
- `source_type` — preserved
- `summary` — normalized language, same meaning
- `related_projects[]` — populated via keyword/semantic match
- `confidence` — scored (low / medium / high)
- `created_at` — preserved

**Contract fields populated (KB Opportunity candidates):**
- `id` — generated
- `originating_intel_id` — linked to source New Intel
- `gap_type` — inferred (documentation / response / process)
- `evidence_refs[]` — references to supporting intel
- `suggested_action` — draft, pending human refinement

**Allowed operations:**
- Normalize language (same meaning, clearer wording)
- Deduplicate against existing intel
- Assign confidence scores
- Link intel to related projects
- Identify documentation or response gaps
- Draft KB Opportunity candidates

**Forbidden operations:**
- Creating new observations (only transforms Stage 1 output)
- Promoting intel to official status
- Generating recommendations
- Modifying existing official intel
- Auto-approving KB Opportunities

**Guardrails:**
- Original Stage 1 candidates preserved for audit
- Confidence scoring must be conservative (default: low)
- KB Opportunity candidates are drafts, not official
- No write access to official output files

---

## Stage 3: Final Clarity Pass

**Provider:** Claude

**Role:** Explain and de-risk

**Inputs:**
- Cleaned New Intel from Stage 2
- Candidate KB Opportunities from Stage 2
- Historical Action Log (read-only, for context)

**Outputs:**
- Explainable Recommendations (advisory only)

**Contract fields populated (Recommendation):**
- `id` — generated
- `rationale` — human-readable explanation of why this matters
- `source_intel_ids[]` — linked to originating intel
- `impact_level` — low / medium / high
- `reversible` — true / false

**Allowed operations:**
- Explain observations in plain language
- Clarify rationale for recommendations
- Assess reversibility of suggested actions
- De-risk tone (remove urgency, speculation, certainty)
- Contextualize against past actions

**Forbidden operations:**
- Creating new intelligence (no new observations)
- Synthesizing new patterns (only explains existing)
- Promoting intel or KB Opportunities
- Executing any recommendation
- Modifying confidence scores from Stage 2

**Guardrails:**
- Recommendations are advisory only
- All recommendations must cite source intel
- Language must be neutral and professional
- No urgency or pressure language
- No claims of certainty

---

## Human Review Gate

**Location:** Between pipeline output and official records

**Human actions available:**
- Accept recommendation → recorded in Action Log
- Dismiss intel → recorded in Action Log
- Promote intel → project → recorded in Action Log
- Approve KB Opportunity → moves to official status
- Edit any artifact before approval

**Pipeline cannot:**
- Write to official output files
- Promote any artifact automatically
- Skip human review
- Record actions on behalf of humans

---

## Action Log

**Trigger:** Human action only

**Logged events (per contract):**
- Accept recommendation
- Dismiss intel
- Promote intel → project

**Contract fields:**
- `id` — generated at log time
- `timestamp` — moment of human action
- `action_type` — accept / dismiss / promote
- `target_id` — id of affected artifact
- `rationale` — human-provided reason (optional but encouraged)

**Guardrails:**
- Pipeline stages never write to Action Log
- Only human-initiated events are recorded
- Rationale field is for humans, not system-generated

---

## Summary of Stage Boundaries

| Stage | Provider | Creates | Cannot Create |
|-------|----------|---------|---------------|
| 1 | Ollama/Mistral | Candidate New Intel | KB Opps, Recommendations |
| 2 | OpenAI | Cleaned Intel, Candidate KB Opps | Recommendations |
| 3 | Claude | Recommendations | New Intel, KB Opps |

---

## Invariants

1. No stage may skip ahead or merge roles
2. No automatic promotion between intelligence types
3. All artifacts are drafts until human approval
4. Action Log is human-write-only
5. Original observations are preserved for audit
6. Pipeline is read-only against official outputs
7. Humans always decide

---

**Version:** v0
**Status:** Architecture definition (no implementation)
