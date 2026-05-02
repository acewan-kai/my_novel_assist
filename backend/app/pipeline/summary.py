"""Summary Agent — generates chapter summaries."""

from .base import BaseAgent, AgentContext, AgentResult

SUMMARY_SYSTEM = """You are the Summary Agent. Create concise chapter summary:
1. Major plot events (2-3 sentences)
2. Character arc progression
3. Key revelations
4. Emotional trajectory
5. Hook status changes
6. Relationship states
Keep to 3-5 paragraphs. Factual, neutral language."""


class SummaryAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        prompt = f"""Summarize Chapter {context.chapter_number}.
Content: {context.chapter_outline}
Prior: {context.prior_summary}"""
        resp = self.llm.complete(self._messages(SUMMARY_SYSTEM, prompt))
        return AgentResult(success=resp.finished, content=resp.content)
