"""Anthropic Claude provider."""

from __future__ import annotations

from anthropic import Anthropic
from .base import BaseProvider, LLMConfig, LLMMessage, LLMResponse


class AnthropicProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = Anthropic(api_key=config.api_key)

    def _prepare(self, messages: list[LLMMessage]):
        system = None
        msgs = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                msgs.append({"role": m.role, "content": m.content})
        return system, msgs

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        system, msgs = self._prepare(messages)
        kwargs = dict(model=self.config.model, messages=msgs,
                      max_tokens=self.config.max_tokens, temperature=self.config.temperature)
        if system:
            kwargs["system"] = system
        try:
            resp = self.client.messages.create(**kwargs)
            content = "".join(b.text for b in resp.content if b.type == "text")
            return LLMResponse(content=content, model=resp.model,
                              usage={"input_tokens": resp.usage.input_tokens,
                                     "output_tokens": resp.usage.output_tokens})
        except Exception as e:
            return LLMResponse(content=f"Error: {e}", finished=False)

    def stream(self, messages: list[LLMMessage]):
        system, msgs = self._prepare(messages)
        kwargs = dict(model=self.config.model, messages=msgs,
                      max_tokens=self.config.max_tokens, temperature=self.config.temperature, stream=True)
        if system:
            kwargs["system"] = system
        try:
            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"Error: {e}"
