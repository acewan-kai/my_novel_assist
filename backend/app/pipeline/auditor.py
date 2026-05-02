"""Auditor Agent — evaluates chapter quality (temperature=0)."""

from .base import BaseAgent, AgentContext, AgentResult

AUDITOR_SYSTEM = """You are the Auditor Agent. Evaluate chapter quality (temperature=0).
DIMENSIONS:
1. OOC — characters act against known traits?
2. Info boundary — characters know things they shouldn't?
3. Causal consistency — follows from prior events?
4. Emotional arc — natural progression?
5. Outline deviation — follows planned outline?
6. Pacing — appropriate rhythm?
7. Hook management — properly planted/advanced/resolved?
8. De-AI-fication — obvious AI tells?
9. Continuity — consistent world rules?
10. End hook — reason to continue?
Rate: ✅ PASS / ⚠️ WARNING / ❌ FAIL. JSON output. Be harsh."""


class AuditorAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        prompt = f"""Audit Chapter {context.chapter_number}.
Content: {context.chapter_outline}
Prior: {context.prior_summary}
World: {context.world_context}"""
        resp = self.llm.complete(self._messages(AUDITOR_SYSTEM, prompt))
        return AgentResult(success=resp.finished, content=resp.content)
