/* ============================================================
 * Runtime Modes
 * ------------------------------------------------------------
 * Explicit execution context for Future Hause.
 * Used ONLY by the Router to select resources.
 * ============================================================
 */

export type RuntimeMode =
  | 'LOCAL' // Local Ollama available
  | 'WORK_REMOTE' // No local inference; allow remote draft adapter
  | 'DEMO' // Safe demo mode (remote draft only, capped)
  | 'AIRPLANE'; // No LLM calls allowed

export const DEFAULT_RUNTIME_MODE: RuntimeMode = 'LOCAL';
