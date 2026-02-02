/**
 * LLM Router — Deterministic Routing for Future Hause
 *
 * Canonical contract: docs/llm-routing.md
 *
 * This module determines which LLM stage should handle input.
 * It does NOT call any models — routing is local and synchronous.
 *
 * GUARDRAILS:
 * - No network calls
 * - No model execution
 * - No persistence
 * - No side effects
 * - Deterministic (same input → same decision)
 */

/* --------------------------------------
   STAGE DEFINITIONS
   -------------------------------------- */

const STAGES = {
  STAGE_1: {
    stage: 1,
    provider: 'ollama',
    role: 'Pattern spotting'
  },
  STAGE_2: {
    stage: 2,
    provider: 'openai',
    role: 'Synthesis'
  },
  STAGE_3: {
    stage: 3,
    provider: 'claude',
    role: 'Explain / de-risk'
  }
};

/* --------------------------------------
   ROUTING KEYWORDS
   Order of precedence: Stage 3 > Stage 2 > Stage 1
   -------------------------------------- */

const STAGE_3_KEYWORDS = [
  'explain', 'clarify', 'rationale', 'recommend', 'advise', 'de-risk',
  'human-readable', 'plain language', 'why', 'impact', 'help me understand',
  'what does this mean', 'draft', 'write'
];

const STAGE_2_KEYWORDS = [
  'synthesize', 'summarize', 'deduplicate', 'link', 'connect',
  'confidence', 'score', 'gap', 'opportunity', 'normalize',
  'compare', 'relate', 'combine', 'merge'
];

const STAGE_1_KEYWORDS = [
  'observe', 'detect', 'pattern', 'signal', 'raw', 'new', 'watch', 'spot',
  'notice', 'found', 'saw', 'heard', 'reddit', 'post', 'comment'
];

/* --------------------------------------
   ROUTING LOGIC
   -------------------------------------- */

/**
 * Check if text contains any keywords from a list
 * @param {string} text - Input text (lowercased)
 * @param {string[]} keywords - Keywords to match
 * @returns {string|null} Matched keyword or null
 */
function matchKeywords(text, keywords) {
  for (const keyword of keywords) {
    if (text.includes(keyword.toLowerCase())) {
      return keyword;
    }
  }
  return null;
}

/**
 * Generate simple hash for input (for traceability)
 * @param {string} text - Input text
 * @returns {string} Short hash
 */
function hashInput(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(16).slice(0, 8);
}

/**
 * Route input to appropriate LLM stage
 *
 * IMPORTANT: This function does NOT call any model.
 * It returns a routing decision only.
 *
 * @param {string} text - User input text
 * @returns {object} RoutingDecision
 */
function routeLLM(text) {
  if (!text || typeof text !== 'string') {
    // Invalid input — route to Stage 1 (safest default)
    return {
      ...STAGES.STAGE_1,
      reason: 'Invalid or empty input — defaulting to Stage 1',
      matchedKeyword: null,
      inputHash: 'invalid',
      timestamp: new Date().toISOString()
    };
  }

  const normalizedText = text.toLowerCase().trim();

  // Check Stage 3 first (highest precedence)
  const stage3Match = matchKeywords(normalizedText, STAGE_3_KEYWORDS);
  if (stage3Match) {
    return {
      ...STAGES.STAGE_3,
      reason: `Matched Stage 3 keyword: "${stage3Match}"`,
      matchedKeyword: stage3Match,
      inputHash: hashInput(text),
      timestamp: new Date().toISOString()
    };
  }

  // Check Stage 2
  const stage2Match = matchKeywords(normalizedText, STAGE_2_KEYWORDS);
  if (stage2Match) {
    return {
      ...STAGES.STAGE_2,
      reason: `Matched Stage 2 keyword: "${stage2Match}"`,
      matchedKeyword: stage2Match,
      inputHash: hashInput(text),
      timestamp: new Date().toISOString()
    };
  }

  // Check Stage 1
  const stage1Match = matchKeywords(normalizedText, STAGE_1_KEYWORDS);
  if (stage1Match) {
    return {
      ...STAGES.STAGE_1,
      reason: `Matched Stage 1 keyword: "${stage1Match}"`,
      matchedKeyword: stage1Match,
      inputHash: hashInput(text),
      timestamp: new Date().toISOString()
    };
  }

  // Default to Stage 1 (safest)
  return {
    ...STAGES.STAGE_1,
    reason: 'No specific keywords matched — defaulting to Stage 1 (pattern spotting)',
    matchedKeyword: null,
    inputHash: hashInput(text),
    timestamp: new Date().toISOString()
  };
}

/**
 * Format routing decision for display
 * @param {object} decision - RoutingDecision from routeLLM
 * @returns {string} Human-readable routing summary
 */
function formatRoutingDecision(decision) {
  return `Stage ${decision.stage} (${decision.provider}) — ${decision.role}`;
}

// Export for use in dashboard.js
// Note: Using window for browser compatibility (no bundler)
if (typeof window !== 'undefined') {
  window.routeLLM = routeLLM;
  window.formatRoutingDecision = formatRoutingDecision;
  window.LLM_STAGES = STAGES;
}

// Export for testing (Node.js)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { routeLLM, formatRoutingDecision, STAGES };
}
