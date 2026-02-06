/* ============================================================
 * Draft Adapter — Canonical Interface
 * ------------------------------------------------------------
 * Purpose:
 *  - Safely invoke local LLMs for draft generation only
 *  - Return structured, inspectable draft metadata
 *  - NEVER mutate state, memory, or auto-send output
 * ============================================================
 */

/* ---------- Input Types ---------- */

export type DraftRequest = {
  /** Router-determined intent (deterministic, not LLM-generated) */
  intent: string;

  /** User or system prompt content */
  prompt: string;

  /** Optional guardrails or formatting constraints */
  constraints?: string[];

  /** Upper bound only — adapter may choose lower */
  maxTokens?: number;
};

/* ---------- Output Types ---------- */

export type DraftResult = {
  /** Generated draft text (non-authoritative) */
  draftText: string;

  /** Heuristic confidence score (0.0 – 1.0) */
  confidence: number;

  /** Model identifier used (e.g., "mistral:7b") */
  model: string;

  /** End-to-end latency for the draft call */
  latencyMs: number;

  /** Explicit risk signals for downstream routing / UX */
  riskFlags: DraftRiskFlag[];
};

/* ---------- Risk Flags ---------- */

export type DraftRiskFlag =
  | 'low_confidence'
  | 'ambiguous_request'
  | 'missing_context'
  | 'possible_hallucination'
  | 'format_violation'
  | 'model_timeout'
  | 'unknown_error';

/* ---------- Adapter Contract ---------- */

export interface DraftAdapter {
  /**
   * Generate a draft using a local model.
   *
   * HARD RULES:
   * - Must fail closed (throw or return riskFlags)
   * - Must NOT auto-escalate to premium models
   * - Must NOT write memory or mutate state
   */
  generateDraft(request: DraftRequest): Promise<DraftResult>;
}
