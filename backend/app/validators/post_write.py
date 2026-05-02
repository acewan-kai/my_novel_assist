"""Post-write validation — checks content quality after generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


class PostWriteValidator:
    def __init__(self, min_words: int = 200, max_repeat_sentence: int = 3):
        self.min_words = min_words
        self.max_repeat_sentence = max_repeat_sentence

    @staticmethod
    def _word_count(text: str) -> int:
        """Count words, handling both English and Chinese text."""
        import re
        if not text.strip():
            return 0
        cjk = len(re.findall(r'[一-鿿㐀-䶿豈-﫿]', text))
        non_cjk = len(text.replace("\n", " ").split())
        return max(cjk, non_cjk)

    def validate(self, text: str, context: dict[str, Any] | None = None) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        metrics: dict[str, float] = {}

        # Word count (handles Chinese + English)
        wc = self._word_count(text)
        metrics["word_count"] = float(wc)
        if wc < self.min_words:
            errors.append(f"Word count {wc} below minimum {self.min_words}")

        # Empty check
        if not text.strip():
            errors.append("Content is empty")

        # Repeated paragraphs
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        if len(paragraphs) >= 2:
            repeats = sum(1 for i in range(len(paragraphs) - 1)
                          if paragraphs[i] == paragraphs[i + 1])
            if repeats > self.max_repeat_sentence:
                warnings.append(f"Consecutive repeated paragraphs: {repeats}")

        # Repeated sentence starters
        sentences = [s.strip() for s in text.replace("。", ".").split(".") if s.strip()]
        if len(sentences) >= 5:
            starters = [s.split()[0] if s.split() else "" for s in sentences[:20]]
            if len(set(starters)) < len(starters) * 0.3:
                warnings.append("Low sentence starter variety")

        metrics["quality_score"] = self._score(wc, len(errors), len(warnings))
        return ValidationResult(passed=len(errors) == 0, errors=errors,
                                warnings=warnings, metrics=metrics)

    def _score(self, wc: int, err_count: int, warn_count: int) -> float:
        s = 1.0
        if wc < self.min_words:
            s -= 0.3
        s -= err_count * 0.2
        s -= warn_count * 0.05
        return max(0.0, min(1.0, s))
