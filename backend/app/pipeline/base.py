"""Base Agent class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..llm.base import BaseProvider


@dataclass
class AgentContext:
    chapter_number: int = 0
    chapter_outline: str = ""
    world_context: str = ""
    prior_summary: str = ""
    pending_hooks: str = ""
    pov_character: str = ""
    thread_context: str = ""
    project_id: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    success: bool = True
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class BaseAgent(ABC):
    def __init__(self, llm_provider: BaseProvider, name: str = ""):
        self.llm = llm_provider
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        ...

    def _messages(self, system: str, user: str):
        from ..llm.base import LLMMessage
        return [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)]
