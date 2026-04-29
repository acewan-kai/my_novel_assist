"""
Character — persistent persona + layered memory.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from config import CHARACTERS_DIR


@dataclass
class Character:
    # ── Immutable persona (never changed during play) ─────────────────────────
    name: str
    background: str = ""
    traits: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)

    # ── Mutable state ─────────────────────────────────────────────────────────
    emotional_state: str = "neutral"

    # ── Relationships: {other_name: {emotion, trust}} ─────────────────────────
    relationships: dict[str, dict] = field(default_factory=dict)

    # ── Memory layers ─────────────────────────────────────────────────────────
    # long_term_summaries: compressed summaries of old episodes
    long_term_summaries: list[str] = field(default_factory=list)
    # episodes: recent raw events [{scene_id, timestamp, content}]
    episodes: list[dict] = field(default_factory=list)

    # ── Persistence ───────────────────────────────────────────────────────────
    @property
    def path(self) -> Path:
        return CHARACTERS_DIR / f"{self.name.lower()}.json"

    @classmethod
    def load(cls, name: str) -> Character:
        path = CHARACTERS_DIR / f"{name.lower()}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Defensive: only pass known fields
            known = {k for k in cls.__dataclass_fields__}
            filtered = {k: v for k, v in data.items() if k in known}
            return cls(**filtered)
        return cls(name=name)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def exists(cls, name: str) -> bool:
        return (CHARACTERS_DIR / f"{name.lower()}.json").exists()

    def update_relationship(self, other: str, emotion: str, trust: int) -> None:
        self.relationships[other] = {"emotion": emotion, "trust": trust}
