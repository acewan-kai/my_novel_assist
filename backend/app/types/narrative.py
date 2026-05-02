"""Narrative type definitions — Dramatica-inspired."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StoryPoint:
    name: str = ""
    description: str = ""
    chapter: int = 0
    resolved: bool = False


@dataclass
class SceneBeat:
    index: int = 0
    summary: str = ""
    pov: str = ""
    location: str = ""
    duration: str = ""
    objective: str = ""


@dataclass
class NarrativeArc:
    name: str = ""
    type: str = ""  # main, sub, character
    beats: list[SceneBeat] = field(default_factory=list)
    status: str = "active"


@dataclass
class CharacterState:
    name: str = ""
    arc_type: str = ""  # change, steadfast, growth, fall
    motivation: str = ""
    conflict: str = ""
    current_goal: str = ""


@dataclass
class PlotThread:
    name: str = ""
    type: str = ""  # action, decision, investigation
    status: str = "active"
    resolution_chapter: int = 0


@dataclass
class ThemeElement:
    name: str = ""
    value: str = ""  # e.g., "justice vs mercy"
    resolution: str = ""
