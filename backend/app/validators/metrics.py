"""Quality metrics — NovelGenerator-inspired scoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualityMetrics:
    coherence: float = 0.0
    integration: float = 0.0
    polish: float = 0.0

    @property
    def overall(self) -> float:
        return (self.coherence + self.integration + self.polish) / 3

    @property
    def passed(self) -> bool:
        return self.overall >= 0.6

    def to_dict(self) -> dict:
        return {"coherence": round(self.coherence, 2), "integration": round(self.integration, 2),
                "polish": round(self.polish, 2), "overall": round(self.overall, 2)}
