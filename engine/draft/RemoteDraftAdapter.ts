import {
  DraftAdapter,
  DraftRequest,
  DraftResult,
  DraftRiskFlag,
} from './DraftAdapter';

/**
 * RemoteDraftAdapter
 * ------------------------------------------------------------
 * Remote draft generation using ChatGPT (or equivalent).
 * Used ONLY when explicitly selected by the Router (e.g. WORK_REMOTE mode).
 *
 * This adapter is:
 * - Draft-only
 * - Non-authoritative
 * - Cost-visible
 * - Never silent
 */

type OpenAIResponse = {
  choices?: Array<{
    message?: {
      content?: string;
    };
  }>;
};

export class RemoteDraftAdapter implements DraftAdapter {
  private readonly apiKey: string;
  private readonly model: string;
  private readonly timeoutMs: number;

  constructor(options: {
    apiKey: string;
    model?: string; // default: gpt-4o-mini
    timeoutMs?: number;
  }) {
    if (!options.apiKey) {
      throw new Error('RemoteDraftAdapter requires an API key');
    }

    this.apiKey = options.apiKey;
    this.model = options.model ?? 'gpt-4o-mini';
    this.timeoutMs = options.timeoutMs ?? 15_000;
  }

  async generateDraft(request: DraftRequest): Promise<DraftResult> {
    const start = Date.now();
    const riskFlags: DraftRiskFlag[] = [];

    let draftText = '';
    let confidence = 0.55; // remote draft is helpful but not trusted

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

      const response = await fetch(
        'https://api.openai.com/v1/chat/completions',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${this.apiKey}`,
          },
          body: JSON.stringify({
            model: this.model,
            temperature: 0.3,
            max_tokens: request.maxTokens ?? 512,
            messages: [
              {
                role: 'system',
                content:
                  'You are generating a draft only. Do not make decisions. Do not assume missing information.',
              },
              {
                role: 'user',
                content: this.buildPrompt(request),
              },
            ],
          }),
          signal: controller.signal,
        }
      );

      clearTimeout(timeout);

      if (!response.ok) {
        riskFlags.push('unknown_error');
        throw new Error(`OpenAI HTTP ${response.status}`);
      }

      const data = (await response.json()) as OpenAIResponse;
      const content = data.choices?.[0]?.message?.content;

      if (!content || !content.trim()) {
        riskFlags.push('low_confidence');
        riskFlags.push('missing_context');
        throw new Error('Empty response from remote model');
      }

      draftText = content.trim();
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
- Draft only
- No decisions
- No assumptions
- Flag uncertainty explicitly
`.trim();
  }

  private estimateConfidence(
    text: string,
    request: DraftRequest,
    riskFlags: DraftRiskFlag[]
  ): number {
    let score = 0.6;

    if (text.length < 120) {
      score -= 0.15;
      riskFlags.push('low_confidence');
    }

    if (/uncertain|not sure|cannot determine/i.test(text)) {
      score -= 0.15;
      riskFlags.push('ambiguous_request');
    }

    if (!request.prompt || request.prompt.length < 20) {
      score -= 0.2;
      riskFlags.push('missing_context');
    }

    if (/guaranteed|definitely|always/i.test(text)) {
      score -= 0.1;
      riskFlags.push('possible_hallucination');
    }

    return Math.max(0, Math.min(1, score));
  }
}
