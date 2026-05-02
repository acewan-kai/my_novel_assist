"""Configuration system."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "qwen2.5:7b"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    data_dir: str = str(Path(__file__).parent.parent / "data")
    secret_key: str = "change-me-in-production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
