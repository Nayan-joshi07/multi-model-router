from .base import Provider, Completion
from .mock import MockProvider
from .openai_p import OpenAIProvider
from .anthropic_p import AnthropicProvider
from .gemini_p import GeminiProvider

REGISTRY: dict[str, type[Provider]] = {
    "mock": MockProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}
__all__ = ["Provider", "Completion", "REGISTRY"]
