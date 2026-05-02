"""Ollama local provider."""

from __future__ import annotations

import json
import httpx
from .base import BaseProvider, LLMConfig, LLMMessage, LLMResponse


class OllamaProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        raw = [{"role": m.role, "content": m.content} for m in messages]
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(f"{self.base_url.rstrip('/')}/v1/chat/completions", json={
                    "model": self.config.model, "messages": raw,
                    "temperature": self.config.temperature, "max_tokens": self.config.max_tokens,
                })
                data = resp.json()
                choice = data["choices"][0]
                return LLMResponse(content=choice["message"]["content"],
                                  model=data.get("model", self.config.model),
                                  finished=choice.get("finish_reason") == "stop")
        except Exception as e:
            return LLMResponse(content=f"Error: {e}", finished=False)

    def stream(self, messages: list[LLMMessage]):
        raw = [{"role": m.role, "content": m.content} for m in messages]
        try:
            with httpx.Client(timeout=120) as client:
                with client.stream("POST", f"{self.base_url.rstrip('/')}/v1/chat/completions", json={
                    "model": self.config.model, "messages": raw,
                    "temperature": self.config.temperature, "max_tokens": self.config.max_tokens, "stream": True,
                }) as resp:
                    for line in resp.iter_lines():
                        if line and line.startswith("data: "):
                            data = json.loads(line[6:])
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if delta.get("content"):
                                yield delta["content"]
        except Exception as e:
            yield f"Error: {e}"
