/*
  Future Hause — LLM Router (stub)
  Purpose: prevent JS execution aborts until router is fully implemented
*/

window.llmRouter = {
  route(input) {
    console.warn('[llmRouter] Stub route called:', input);
    return {
      presenceState: 'idle',
      summary: 'Router unavailable.',
      whatIDid: ['Attempted to classify intent'],
      whatIDidNot: ['Could not route — llmRouter stub'],
      nextStep: 'Implement llmRouter.js'
    };
  }
};

console.info('[Future Hause] llmRouter stub loaded');
