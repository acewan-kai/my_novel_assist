"""Provider Bank — built-in provider registry."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProviderInfo:
    name: str = ""
    base_url: str = ""
    api_key_env: str = ""
    default_model: str = ""
    local: bool = False
    models: list[str] = field(default_factory=list)
    enabled: bool = True


PROVIDER_BANK: dict[str, ProviderInfo] = {
    "openai": ProviderInfo("OpenAI", "https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini",
                          models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"]),
    "deepseek": ProviderInfo("DeepSeek", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", "deepseek-chat",
                           models=["deepseek-chat", "deepseek-reasoner"]),
    "anthropic": ProviderInfo("Anthropic", "https://api.anthropic.com", "ANTHROPIC_API_KEY", "claude-sonnet-4-6",
                            models=["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5"]),
    "google": ProviderInfo("Google", "https://generativelanguage.googleapis.com/v1beta/openai", "GOOGLE_API_KEY",
                          "gemini-2.5-flash", models=["gemini-2.5-flash", "gemini-2.5-pro"]),
    "ollama": ProviderInfo("Ollama", "http://localhost:11434/v1", "", "qwen2.5:7b", local=True, models=["*"]),
    "custom": ProviderInfo("Custom", "", "CUSTOM_API_KEY", "", models=["*"]),
}


def get_provider_info(name: str) -> ProviderInfo | None:
    return PROVIDER_BANK.get(name)


def list_available_providers() -> list[str]:
    return [k for k, v in PROVIDER_BANK.items() if v.enabled]
