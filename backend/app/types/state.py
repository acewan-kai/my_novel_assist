"""State type definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChapterState:
    number: int = 0
    title: str = ""
    word_count: int = 0
    pov_character: str = ""
    status: str = "draft"
    scenes: list[str] = field(default_factory=list)
    hooks: list[dict[str, Any]] = field(default_factory=list)
    causal_chain: list[str] = field(default_factory=list)


@dataclass
class ProjectState:
    project_id: str = ""
    title: str = ""
    author: str = ""
    premise: str = ""
    chapters: list[ChapterState] = field(default_factory=list)
    current_chapter: int = 0
    created: str = ""
    updated: str = ""

    def get_chapter(self, n: int) -> ChapterState | None:
        for c in self.chapters:
            if c.number == n:
                return c
        return None


@dataclass
class NarrativeState:
    arcs: dict[str, Any] = field(default_factory=dict)
    characters: dict[str, Any] = field(default_factory=dict)
    themes: dict[str, Any] = field(default_factory=dict)
    plot_threads: dict[str, Any] = field(default_factory=dict)
