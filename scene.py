"""
Scene — the virtual stage: location, present characters, working memory.
"""
from __future__ import annotations
import json
import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from config import WORLD_DIR, WORKING_MEMORY_MAX

_STATE_FILE = WORLD_DIR / "scene_state.json"


@dataclass
class Scene:
    name: str
    description: str = ""
    scene_id: str = ""
    present_characters: list[str] = field(default_factory=list)
    working_memory: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.scene_id:
            self.scene_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Persistence ───────────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> Optional[Scene]:
        if _STATE_FILE.exists():
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            known = {k for k in cls.__dataclass_fields__}
            filtered = {k: v for k, v in data.items() if k in known}
            return cls(**filtered)
        return None

    def save(self) -> None:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    # ── Character management ──────────────────────────────────────────────────

    def add_character(self, name: str) -> None:
        if name not in self.present_characters:
            self.present_characters.append(name)
            self.save()

    def remove_character(self, name: str) -> None:
        if name in self.present_characters:
            self.present_characters.remove(name)
            self.save()

    # ── Working memory ────────────────────────────────────────────────────────

    def add_to_working_memory(self, entry: str) -> None:
        self.working_memory.append(entry)
        # Trim to prevent unbounded growth
        if len(self.working_memory) > WORKING_MEMORY_MAX:
            self.working_memory = self.working_memory[-WORKING_MEMORY_MAX:]
        self.save()

    def clear_working_memory(self) -> None:
        self.working_memory.clear()
        self.save()
