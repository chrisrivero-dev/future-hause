import {
  DraftAdapter,
  DraftRequest,
  DraftResult,
  DraftRiskFlag,
} from './DraftAdapter';

/**
 * OllamaDraftAdapter
 * ------------------------------------------------------------
 * Local-only draft generation via Ollama HTTP API.
 * This adapter MUST fail closed and never escalate silently.
 */

type OllamaResponse = {
  response?: string;
};

export class OllamaDraftAdapter implements DraftAdapter {
  private readonly baseUrl: string;
  private readonly model: string;
  private readonly timeoutMs: number;

  constructor(options?: {
    baseUrl?: string; // default: http://localhost:11434
    model?: string; // default: mistral
    timeoutMs?: number;
  }) {
    this.baseUrl = options?.baseUrl ?? 'http://localhost:11434';
    this.model = options?.model ?? 'mistral';
    this.timeoutMs = options?.timeoutMs ?? 15_000;
  }

  async generateDraft(request: DraftRequest): Promise<DraftResult> {
    const start = Date.now();
    const riskFlags: DraftRiskFlag[] = [];

    let draftText = '';
    let confidence = 0.5;

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

      const prompt = this.buildPrompt(request);

      const response = await fetch(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.model,
          prompt,
          stream: false,
          options: {
            num_predict: request.maxTokens ?? 512,
          },
        }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        riskFlags.push('unknown_error');
        throw new Error(`Ollama HTTP ${response.status}`);
      }

      const data = (await response.json()) as OllamaResponse;

      if (!data.response || !data.response.trim()) {
        riskFlags.push('low_confidence');
        riskFlags.push('missing_context');
        throw new Error('Empty response from model');
      }

      draftText = data.response.trim();

      confidence = this.estimateConfidence(draftText, request, riskFlags);
    } catch (err: any) {
      if (err?.name === 'AbortError') {
        riskFlags.push('model_timeout');
      } else if (riskFlags.length === 0) {
        riskFlags.push('unknown_error');
      }

      return {
        draftText: '',
        confidence: 0.0,
        model: this.model,
        latencyMs: Date.now() - start,
        riskFlags,
      };
    }

    return {
      draftText,
      confidence,
      model: this.model,
      latencyMs: Date.now() - start,
      riskFlags,
    };
  }

  /* ============================================================
   * Helpers
   * ============================================================
   */

  private buildPrompt(request: DraftRequest): string {
    const constraints = request.constraints?.length
      ? `\n\nConstraints:\n- ${request.constraints.join('\n- ')}`
      : '';

    return `
Intent: ${request.intent}

Task:
${request.prompt}
${constraints}

Rules:
- Produce a draft only
- Do NOT assume missing information
- Do NOT make decisions
- Do NOT claim certainty
`.trim();
  }

  private estimateConfidence(
    text: string,
    request: DraftRequest,
    riskFlags: DraftRiskFlag[]
  ): number {
    let score = 0.6;

    if (text.length < 100) {
      score -= 0.15;
      riskFlags.push('low_confidence');
    }

    if (/I am not sure|cannot determine|unclear/i.test(text)) {
      score -= 0.15;
      riskFlags.push('ambiguous_request');
    }

    if (!request.prompt || request.prompt.length < 20) {
      score -= 0.2;
      riskFlags.push('missing_context');
    }

    if (/definitely|guaranteed|certain/i.test(text)) {
      score -= 0.1;
      riskFlags.push('possible_hallucination');
    }

    return Math.max(0, Math.min(1, score));
  }
}
