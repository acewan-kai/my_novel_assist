"""LLM Provider layer."""

from .base import BaseProvider, LLMConfig, LLMMessage, LLMResponse
from .provider_bank import PROVIDER_BANK, get_provider_info, list_available_providers
from .openai_compat import OpenAICompatibleProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider


def create_provider(config: LLMConfig) -> BaseProvider:
    if config.provider == "anthropic":
        return AnthropicProvider(config)
    elif config.provider == "ollama":
        return OllamaProvider(config)
    else:
        return OpenAICompatibleProvider(config)
