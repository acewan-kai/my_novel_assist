"""Narrative engine — Dramatica-inspired story progression tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Dramatica-inspired standard 16-stage structure
NARRATIVE_STAGES = [
    "setup", "inciting_incident", "response", "pursuit",
    "ally_intro", "antagonist_rise", "first_turning_point",
    "midpoint", "crisis_buildup", "betrayal", "dark_night",
    "second_turning_point", "final_preparations", "climax",
    "denouement", "resolution"
]


@dataclass
class StoryState:
    stage_index: int = 0
    completed_stages: list[str] = field(default_factory=list)
    active_threads: dict[str, Any] = field(default_factory=dict)
    resolved_threads: dict[str, Any] = field(default_factory=dict)
    character_arcs: dict[str, Any] = field(default_factory=dict)

    @property
    def current_stage(self) -> str:
        if self.stage_index < len(NARRATIVE_STAGES):
            return NARRATIVE_STAGES[self.stage_index]
        return "complete"

    @property
    def progress(self) -> float:
        return self.stage_index / len(NARRATIVE_STAGES)

    @property
    def is_complete(self) -> bool:
        return self.stage_index >= len(NARRATIVE_STAGES)


class NarrativeEngine:
    def __init__(self):
        self.state = StoryState()

    def advance(self, stages: int = 1) -> str:
        current = self.state.current_stage
        if current not in self.state.completed_stages:
            self.state.completed_stages.append(current)
        self.state.stage_index = min(self.state.stage_index + stages, len(NARRATIVE_STAGES))
        return self.state.current_stage

    def get_required_beats(self, chapter: int, total_chapters: int) -> list[str]:
        ratio = chapter / max(total_chapters, 1)
        if ratio <= 0.1:
            return ["setup", "inciting_incident"]
        elif ratio <= 0.25:
            return ["response", "pursuit"]
        elif ratio <= 0.4:
            return ["ally_intro", "antagonist_rise"]
        elif ratio <= 0.5:
            return ["first_turning_point", "midpoint"]
        elif ratio <= 0.65:
            return ["crisis_buildup", "betrayal"]
        elif ratio <= 0.8:
            return ["dark_night", "second_turning_point"]
        elif ratio <= 0.9:
            return ["final_preparations", "climax"]
        else:
            return ["denouement", "resolution"]

    def get_stage_prompt(self, stage: str) -> str:
        prompts = {
            "setup": "Establish the world, tone, and ordinary life of the protagonist.",
            "inciting_incident": "Introduce the event that disrupts the status quo.",
            "response": "Show the protagonist's initial reaction and reluctance.",
            "pursuit": "The protagonist commits to the new direction.",
            "ally_intro": "Introduce key allies and build relationships.",
            "antagonist_rise": "Show antagonist power and establish stakes.",
            "first_turning_point": "First major setback or revelation changes everything.",
            "midpoint": "A major event shifts passive to active pursuit.",
            "crisis_buildup": "Tension escalates; pressure on protagonist mounts.",
            "betrayal": "Trust is broken; a key relationship fractures.",
            "dark_night": "The lowest point; hope seems lost.",
            "second_turning_point": "New information or resolve sparks recovery.",
            "final_preparations": "Protagonist prepares for final confrontation.",
            "climax": "The ultimate confrontation with the central conflict.",
            "denouement": "Fallout from the climax; loose ends begin to tie.",
            "resolution": "The new normal is established; story closes.",
        }
        return prompts.get(stage, "Continue the narrative progression.")

    def reset(self):
        self.state = StoryState()
