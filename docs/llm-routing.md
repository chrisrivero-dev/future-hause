# LLM Routing Contract

**Status:** Authoritative
**Version:** v0
**Source of truth:** This document

---

## Purpose

This contract defines how Future Hause routes input to the appropriate LLM stage.
Routing is **deterministic** and **local** — no network calls during routing.

---

## Routing Decision

The router examines input text and returns a **routing decision**, not a model response.

```
routeLLM(text) → RoutingDecision
```

### RoutingDecision Schema

```javascript
{
  stage: 1 | 2 | 3,
  provider: 'ollama' | 'openai' | 'claude',
  role: string,
  reason: string,
  inputHash: string,
  timestamp: string
}
```

---

## Stage Mapping

| Stage | Provider | Role | Trigger |
|-------|----------|------|---------|
| 1 | Ollama/Mistral | Pattern spotting | Raw observations, new signals |
| 2 | OpenAI | Synthesis | Structured data, cross-linking |
| 3 | Claude | Explain / de-risk | Recommendations, human-facing |

---

## Routing Rules (Deterministic)

### Route to Stage 1 (Ollama)
Input matches any:
- Raw observation (unstructured text)
- New signal detection request
- Pattern spotting request
- Default fallback for ambiguous input

### Route to Stage 2 (OpenAI)
Input matches any:
- Request for synthesis or summary
- Cross-linking or deduplication request
- Confidence scoring request
- KB gap detection

### Route to Stage 3 (Claude)
Input matches any:
- Request for explanation or rationale
- Recommendation clarity request
- De-risking or tone adjustment
- Human-facing content generation

---

## Routing Keywords (v0)

These keywords influence routing. Order of precedence: Stage 3 > Stage 2 > Stage 1.

### Stage 3 Keywords
```
explain, clarify, rationale, recommend, advise, de-risk,
human-readable, plain language, why, impact
```

### Stage 2 Keywords
```
synthesize, summarize, deduplicate, link, connect,
confidence, score, gap, opportunity, normalize
```

### Stage 1 Keywords (or default)
```
observe, detect, pattern, signal, raw, new, watch, spot
```

---

## Guardrails

1. **No network calls during routing** — routing is local and synchronous
2. **No model execution** — router returns decision only
3. **No persistence** — routing decisions are ephemeral
4. **No side effects** — routing is pure function
5. **Deterministic** — same input always produces same decision

---

## Integration Points

### UI (dashboard.js)
```javascript
import { routeLLM } from './llmRouter.js';

const decision = routeLLM(userInput);
// Render decision in response schema
// Do NOT call model yet
```

### Response Schema Addition
When rendering response, include routing transparency:

```
Status:
• Presence State: Observing
• Mode: Draft / Advisory
• Side Effects: None
• Routed To: Stage 1 (Ollama) — Pattern spotting

Summary:
• [summary]

What I did:
• Analyzed input for routing keywords
• Determined appropriate pipeline stage
• Prepared routing decision for review

What I did NOT do:
• No model was called
• No data was persisted
• No external systems were modified
```

---

## Invariants

1. Routing happens before any model call
2. Routing decision is visible to user
3. User may override routing (future)
4. Default route is Stage 1 (safest)
5. Routing never fails — always returns valid decision

---

**Canonical reference:** `docs/llm-routing.md`
**Implementation:** `ui/llmRouter.js`
