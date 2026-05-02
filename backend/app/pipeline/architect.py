"""Architect Agent — designs chapter blueprint."""

from .base import BaseAgent, AgentContext, AgentResult

ARCHITECT_SYSTEM = """You are the Architect Agent. Design chapter blueprints.
Given outline, world context, hooks, and prior summaries, produce:
1. Scene breakdown (2-4 scenes)
2. POV character arc
3. Hooks to advance/resolve
4. Causal chain continuity
5. Emotional arc trajectory
Output as structured JSON."""


class ArchitectAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        prompt = f"""Design blueprint for Chapter {context.chapter_number}.
Outline: {context.chapter_outline}
World: {context.world_context}
Prior: {context.prior_summary}
Hooks: {context.pending_hooks}
Thread: {context.thread_context}"""
        resp = self.llm.complete(self._messages(ARCHITECT_SYSTEM, prompt))
        return AgentResult(success=resp.finished, content=resp.content)
