# Future Hause — Agent Architecture & Invocation Rules (v1)

## Core Principles

Each agent has:
- A single responsibility
- A hard boundary
- A non-overlapping contract

Agents **never help each other implicitly**.  
All coordination is **explicit, event-driven, and logged**.

Agents **never self-invoke**.

This document is **authoritative**. Any behavior that contradicts it is invalid by definition.

---

## Agent Definitions

### 1. DraftAgent ✅ (Implemented)

**Purpose**  
Generate proposed content only.

**Allowed**
- Generate draft text
- Suggest changes
- Output markdown or structured proposals

**Forbidden**
- Editing files
- Refactoring
- Applying changes
- Interpreting logs

**Output Contract**
```json
{
  "agent": "DraftAgent",
  "type": "proposal",
  "target": "doc | code | config",
  "content": "...",
  "confidence": 0.00
}
```

---

### 2. DocAgent

**Purpose**  
Rewrite and clarify existing documentation only.

**Allowed**
- Edit markdown documentation
- Improve clarity, tone, and structure
- Fix grammar and ambiguity

**Forbidden**
- Logic changes
- Code edits
- Feature additions

**Guardrails**
- File type must be `.md`
- Diffs must be textual only

**Output Contract**
```json
{
  "agent": "DocAgent",
  "file": "docs/xxx.md",
  "summary": "What changed and why",
  "diff": "unified diff text"
}
```

---

### 3. RefactorAgent

**Purpose**  
Refactor code without changing behavior.

**Allowed**
- Rename variables
- Extract functions
- Reduce duplication
- Improve readability

**Forbidden**
- Behavior changes
- Feature changes
- Removing safety checks
- Silent edits

**Required Two-Step Contract**

**Step 1 — Proposal (mandatory)**
```json
{
  "agent": "RefactorAgent",
  "intent": "Refactor X to reduce duplication",
  "files": ["ui/dashboard.js"],
  "risk": "low | medium | high",
  "behavior_change": false
}
```

**Step 2 — Execution (approval required)**
```json
{
  "agent": "RefactorAgent",
  "approved": true,
  "diff": "unified diff text"
}
```

---

### 4. LogReviewAgent

**Purpose**  
Detect anomalies, risks, or regressions from logs only.  
This is the system’s early warning mechanism.

**Allowed**
- Read logs
- Pattern analysis
- Severity ranking
- Suggest next steps

**Forbidden**
- Editing code
- Fixing issues
- Speculation without evidence

**Evidence Requirement**  
All findings must cite log lines or timestamps.

**Output Contract**
```json
{
  "agent": "LogReviewAgent",
  "time_window": "ISO-8601 → ISO-8601",
  "findings": [
    {
      "severity": "low | medium | high | critical",
      "pattern": "description",
      "evidence": ["log line 123", "log line 456"],
      "impact": "what could go wrong",
      "next_step": "recommended human or agent action"
    }
  ]
}
```

---

### 5. OpsLedgerAgent

**Purpose**  
Create a machine-readable audit trail of what actually happened.

This agent is boring by design. That is its strength.

**Allowed**
- Record completed actions
- Serialize events

**Forbidden**
- Interpretation
- Judgment
- Summaries
- Opinions

**Output Schema (Strict)**

**JSON**
```json
{
  "timestamp": "ISO-8601",
  "agent": "RefactorAgent",
  "action": "Refactored dashboard icon logic",
  "files": ["ui/dashboard.css"],
  "commit": "70b102d",
  "approved_by": "human | system"
}
```

**CSV**
```csv
timestamp,agent,action,files,commit,approved_by
```

---

## How Agents Work Together (No Chaos)

### Execution Order (Typical Cycle)

1. **DraftAgent**  
   Proposes content or changes

2. **Human Decision**  
   Accept / reject / revise

3. **DocAgent** (if documentation involved)  
   Applies documentation-only edits

4. **RefactorAgent**  
   Proposal → approval → execution (manual only)

5. **LogReviewAgent**  
   Scans logs post-change  
   Flags anomalies

6. **OpsLedgerAgent**  
   Records what actually happened

---

## Dashboard Mapping (Authoritative)

| Dashboard Area | Source Agent |
|---|---|
| New Intel | DraftAgent |
| KB Opportunities | DocAgent |
| Projects | Approved RefactorAgent work |
| Action Log | OpsLedgerAgent |
| Warnings / Alerts | LogReviewAgent |

No agent writes directly to another agent’s column.

---

## Agent Invocation Rules

### Core Rule (Non-Negotiable)

Agents never self-invoke.  
Every run is triggered by a **system event** or **explicit human action**.

---

### System Events (Only Valid Triggers)

| Event ID | Description |
|---|---|
| EVT_INTEL_INGESTED | New intel observed |
| EVT_DRAFT_REQUESTED | Human requests a draft |
| EVT_DOC_REVIEW_REQUESTED | Human approves doc rewrite |
| EVT_CODE_REVIEW_REQUESTED | Human requests refactor analysis |
| EVT_DEPLOY_COMPLETE | Deployment finished |
| EVT_LOG_WINDOW_READY | Log window closed |
| EVT_ACTION_COMPLETED | Approved action finished |

If it’s not listed here, the agent does not run.

---

### DraftAgent — Invocation

**Triggers**
- EVT_INTEL_INGESTED
- EVT_DRAFT_REQUESTED

**Automatic**
- Yes, with gating

**Conditions**
- Confidence ≥ configured threshold
- Advisory targets only
- No unresolved high/critical alerts

**Never Runs When**
- Refactor in progress
- Deployment mid-flight
- Critical logs present

---

### DocAgent — Invocation

**Trigger**
- EVT_DOC_REVIEW_REQUESTED

**Automatic**
- No (human-only)

---

### RefactorAgent — Invocation

**Trigger**
- EVT_CODE_REVIEW_REQUESTED

**Automatic**
- Never

**Blocked If**
- High or critical log issues exist
- DraftAgent output is unreviewed
- Another refactor is running

---

### LogReviewAgent — Invocation

**Triggers**
- EVT_DEPLOY_COMPLETE
- EVT_LOG_WINDOW_READY

**Automatic**
- Yes (read-only)

**Severity Gating**

| Severity | Effect |
|---|---|
| Low | Informational |
| Medium | Blocks DraftAgent auto-runs |
| High | Blocks RefactorAgent |
| Critical | Freezes all agents except LogReviewAgent and OpsLedgerAgent |

---

### OpsLedgerAgent — Invocation

**Trigger**
- EVT_ACTION_COMPLETED

**Automatic**
- Always

**Special Rule**
- If OpsLedgerAgent fails → system raises alert  
  (no silent actions allowed)

---

# 🧠 ProjectFocusAgent — Active Project Focus Manager

## Overview

**ProjectFocusAgent** exists **only** to manage the **Active Project Focus** panel in the Future Hause dashboard.

It is intentionally constrained.

- It does **not** create content  
- It does **not** change system state  
- It does **not** make decisions  

It is a **context synthesizer**, not an actor.

This agent provides a real-time, read-only snapshot of what matters *right now* for the currently selected project.

---

## 1. Purpose

Maintain a real-time, read-only snapshot of the **currently selected project**.

Think of it as answering one question:

> **“What matters right now for this project?”**

This agent functions as the system’s **working memory layer**.

---

## 2. Allowed and Forbidden Actions

### ✅ Allowed

ProjectFocusAgent may:

- Read from the following data sources:
  - `intel_events.json`
  - `kb_opportunities.json`
  - `projects.json`
  - `action_log.json`
- Count and summarize **state**, not content
- Detect the **last agent activity** and timestamp
- Select **one** suggested next step (if applicable)
- Output a **single structured object** for the dashboard

---

### ❌ Forbidden

ProjectFocusAgent must **never**:

- Write or modify files
- Generate drafts or content
- Promote or demote items
- Make assumptions or interpretations
- Trigger other agents
- Persist state or memory

If any of these rules are violated, the agent is considered **invalid by definition**.

---

## 3. Output Contract (Strict)

This is the **only** output the Active Project Focus panel consumes.

```md
```json
{
  "agent": "ProjectFocusAgent",
  "project": "freshdesk-ai",
  "summary": {
    "open_items": 3,
    "drafts_pending": 1,
    "last_activity": {
      "agent": "DraftAgent",
      "timestamp": "2026-02-02T18:14:00Z"
    }
  },
  "suggested_next_step": {
    "type": "review",
    "label": "Review generated weekly work log",
    "source": "DraftAgent",
    "confidence": 0.82
  },
  "confidence": 0.91
}


## Agent Arbitration Rules

### Priority Order

1. LogReviewAgent  
2. OpsLedgerAgent  
3. RefactorAgent  
4. DocAgent  
5. DraftAgent
6. ProjectFocusAgent (read-only, non-blocking)


Higher-priority agents may block lower-priority agents.  
The reverse is never allowed.

---

## Safety Kill Switches

### Global Freeze

**Triggered When**
- LogReviewAgent emits critical severity
- Data corruption detected
- Manual human override

**Effect**
- All agents halted except LogReviewAgent and OpsLedgerAgent

---

## Configuration Snippet (Reference)

```yaml
agents:
  DraftAgent:
    auto_run: true
    min_confidence: 0.6

  DocAgent:
    auto_run: false

  RefactorAgent:
    auto_run: false

  LogReviewAgent:
    auto_run: true
    interval_minutes: 30

  OpsLedgerAgent:
    auto_run: true
```

---

## Why This Architecture Holds

- No agent can silently mutate the system  
- Every change is attributable  
- Agents are replaceable (model, human, cron)  
- Zero hidden state  
- Zero ambiguity  

**This document is authoritative.**
