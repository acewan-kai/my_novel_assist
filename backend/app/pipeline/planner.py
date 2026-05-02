"""Planner Agent — reads control plane, produces chapter intent."""

from .base import BaseAgent, AgentContext, AgentResult

PLANNER_SYSTEM = """You are a Planning Agent for a novel writing system.
Read the author's intent, current focus, and chapter outline,
then produce a structured chapter intent as JSON with:
- must_keep: elements to preserve
- must_avoid: elements to avoid
- focus_areas: 2-3 specific focus areas
- word_budget_target: target word count"""


class PlannerAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        intent = context.extra.get("author_intent", "")
        focus = context.extra.get("current_focus", "")
        prompt = f"""Chapter {context.chapter_number}
Outline: {context.chapter_outline}
Author Intent: {intent}
Current Focus: {focus}
Prior: {context.prior_summary}
Hooks: {context.pending_hooks}"""
        resp = self.llm.complete(self._messages(PLANNER_SYSTEM, prompt))
        return AgentResult(success=resp.finished, content=resp.content)
