# engine/review/providers/__init__.py
"""
Review providers — Model adapters for review generation.

Each provider MUST:
- Implement ReviewProvider interface
- Return schema-compliant payloads
- NOT call other providers
- NOT mutate state
"""

from .base import ReviewProvider
from .ollama import OllamaReviewProvider
from .kimi import KimiReviewProvider
from .openai import OpenAIReviewProvider
from .claude import ClaudeReviewProvider
from .gemini import GeminiReviewProvider

PROVIDERS = {
    'ollama': OllamaReviewProvider,
    'kimi': KimiReviewProvider,
    'openai': OpenAIReviewProvider,
    'claude': ClaudeReviewProvider,
    'gemini': GeminiReviewProvider,
}

__all__ = [
    'ReviewProvider',
    'OllamaReviewProvider',
    'KimiReviewProvider',
    'OpenAIReviewProvider',
    'ClaudeReviewProvider',
    'GeminiReviewProvider',
    'PROVIDERS',
]
