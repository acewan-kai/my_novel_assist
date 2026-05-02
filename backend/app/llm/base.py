"""LLM Provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: str = ""
    base_url: str = ""


@dataclass
class LLMMessage:
    role: str = "user"
    content: str = ""


@dataclass
class LLMResponse:
    content: str = ""
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    finished: bool = True


class BaseProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        ...

    @abstractmethod
    def stream(self, messages: list[LLMMessage]):
        ...
