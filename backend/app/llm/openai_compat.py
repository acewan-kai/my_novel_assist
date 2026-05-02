"""OpenAI-compatible provider."""

from __future__ import annotations

from openai import OpenAI
from .base import BaseProvider, LLMConfig, LLMMessage, LLMResponse


class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = OpenAI(api_key=config.api_key or "dummy-key", base_url=config.base_url)

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        raw = [{"role": m.role, "content": m.content} for m in messages]
        try:
            resp = self.client.chat.completions.create(
                model=self.config.model, messages=raw,
                temperature=self.config.temperature, max_tokens=self.config.max_tokens,
            )
            choice = resp.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                model=resp.model,
                usage={"prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                       "completion_tokens": resp.usage.completion_tokens if resp.usage else 0},
                finished=choice.finish_reason == "stop",
            )
        except Exception as e:
            return LLMResponse(content=f"Error: {e}", finished=False)

    def stream(self, messages: list[LLMMessage]):
        raw = [{"role": m.role, "content": m.content} for m in messages]
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model, messages=raw,
                temperature=self.config.temperature, max_tokens=self.config.max_tokens, stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            yield f"Error: {e}"
