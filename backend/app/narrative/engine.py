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

# 中文阶段名称
STAGE_NAMES_CN: dict[str, str] = {
    "setup": "开场",
    "inciting_incident": "激励事件",
    "response": "回应",
    "pursuit": "追逐",
    "ally_intro": "盟友登场",
    "antagonist_rise": "对手崛起",
    "first_turning_point": "第一次转折",
    "midpoint": "中点",
    "crisis_buildup": "危机升级",
    "betrayal": "背叛",
    "dark_night": "至暗时刻",
    "second_turning_point": "第二次转折",
    "final_preparations": "最终准备",
    "climax": "高潮",
    "denouement": "落幕",
    "resolution": "结局",
}

# 中文阶段写作提示
STAGE_PROMPTS_CN: dict[str, str] = {
    "setup": "建立世界观、基调和主角的日常生活",
    "inciting_incident": "引入打破平静的事件",
    "response": "展现主角的初始反应和犹豫",
    "pursuit": "主角投入新的方向",
    "ally_intro": "引入关键盟友，建立关系",
    "antagonist_rise": "展示反派的势力和风险",
    "first_turning_point": "第一次重大挫折或发现改变一切",
    "midpoint": "重大事件将被动转为主动",
    "crisis_buildup": "紧张升级，压力增大",
    "betrayal": "信任破裂，关键关系断裂",
    "dark_night": "最低谷，希望渺茫",
    "second_turning_point": "新信息或决心带来转机",
    "final_preparations": "主角为最后对决做准备",
    "climax": "与核心冲突的终极对抗",
    "denouement": "高潮的余波，收束线索",
    "resolution": "新常态确立，故事收尾",
}


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

    def get_stage_name_cn(self, stage: str) -> str:
        """返回阶段的中文名称。"""
        return STAGE_NAMES_CN.get(stage, stage)

    def get_stage_prompt_cn(self, stage: str) -> str:
        """返回阶段的中文写作提示。"""
        return STAGE_PROMPTS_CN.get(stage, self.get_stage_prompt(stage))

    def get_required_beats_cn(self, chapter: int, total_chapters: int) -> list[str]:
        """返回中文阶段名称的节拍列表。"""
        return [self.get_stage_name_cn(b) for b in self.get_required_beats(chapter, total_chapters)]

    def get_beats_info_cn(self, chapter: int, total_chapters: int) -> str:
        """返回中文阶段信息字符串，含提示。"""
        parts = []
        for b in self.get_required_beats(chapter, total_chapters):
            cn = self.get_stage_name_cn(b)
            prompt = self.get_stage_prompt_cn(b)
            parts.append(f"{cn}：{prompt}")
        return " → ".join(parts)

    def reset(self):
        self.state = StoryState()
