/**
 * LLM Router (v0)
 *
 * Canonical routing rules live in: docs/llm-routing.md
 * This module must conform to that contract. No implicit actions.
 *
 * This file is intentionally deterministic + cheap:
 * - Classification is heuristics only (no model calls here)
 * - No persistence
 * - No side effects
 */

/** @typedef {"question"|"draft_request"|"observation"|"meta"|"action"} Intent */
/** @typedef {"low"|"medium"|"high"} Risk */
/** @typedef {"ephemeral"|"draft_only"|"record_adjacent"} Permanence */

export function classifyIntent(text) {
  const t = (text || "").toLowerCase().trim();

  // Meta
  if (
    t.includes("what is your purpose") ||
    t.includes("what do you do") ||
    t.includes("who are you") ||
    t.includes("what is future hause") ||
    t.includes("explain yourself")
  ) return "meta";

  // Action
  if (
    t.startsWith("do ") ||
    t.startsWith("run ") ||
    t.includes("commit") ||
    t.includes("push") ||
    t.includes("write to") ||
    t.includes("update the file") ||
    t.includes("change the code") ||
    t.includes("log this")
  ) return "action";

  // Draft request
  if (
    t.includes("draft") ||
    t.includes("write me") ||
    t.includes("create a") ||
    t.includes("generate a") ||
    t.includes("timesheet") ||
    t.includes("work log")
  ) return "draft_request";

  // Question (simple heuristic: question mark OR question words)
  if (
    t.includes("?") ||
    t.startsWith("what ") ||
    t.startsWith("why ") ||
    t.startsWith("how ") ||
    t.startsWith("when ") ||
    t.startsWith("can you")
  ) return "question";

  return "observation";
}

export function classifyRisk(text) {
  const t = (text || "").toLowerCase();

  if (
    t.includes("legal") ||
    t.includes("medical") ||
    t.includes("financial") ||
    t.includes("invoice") ||
    t.includes("compliance") ||
    t.includes("lawsuit")
  ) return "high";

  if (
    t.includes("record") ||
    t.includes("audit") ||
    t.includes("action log") ||
    t.includes("publish") ||
    t.includes("send") ||
    t.includes("customer") ||
    t.includes("ticket")
  ) return "medium";

  return "low";
}

export function classifyPermanence(text) {
  const t = (text || "").toLowerCase();

  if (
    t.includes("action log") ||
    t.includes("save") ||
    t.includes("persist") ||
    t.includes("record") ||
    t.includes("publish") ||
    t.includes("ticket") ||
    t.includes("kb")
  ) return "record_adjacent";

  if (t.includes("draft") || t.includes("timesheet") || t.includes("work log")) {
    return "draft_only";
  }

  return "ephemeral";
}

/**
 * Returns a routing decision. This does NOT call any model.
 * @returns {{
 *   intent: Intent,
 *   risk: Risk,
 *   permanence: Permanence,
 *   allow_draft: boolean,
 *   must_answer_directly: boolean
 * }}
 */
export function routeLLM(text) {
  const intent = classifyIntent(text);
  const risk = classifyRisk(text);
  const permanence = classifyPermanence(text);

  const must_answer_directly = intent === "question" || intent === "meta";
  const allow_draft = intent === "draft_request";

  return { intent, risk, permanence, allow_draft, must_answer_directly };
}

// Expose on window for non-module scripts (dashboard.js)
window.routeLLM = routeLLM;
