"""Reviser Agent — fixes issues found by Auditor."""

from .base import BaseAgent, AgentContext, AgentResult

REVISER_SYSTEM = """You are the Reviser Agent. Fix chapter issues.
Given original chapter and audit report, fix ALL critical/warning issues.
Don't change passing elements. Preserve author's voice.
Output revised chapter content ONLY."""


class ReviserAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        audit = context.extra.get("audit_report", "")
        mode = context.extra.get("mode", "spot-fix")
        prompt = f"""Revise Chapter {context.chapter_number}. Mode: {mode}
Original: {context.chapter_outline}
Audit: {audit}"""
        resp = self.llm.complete(self._messages(REVISER_SYSTEM, prompt))
        return AgentResult(success=resp.finished, content=resp.content,
                          data={"mode": mode})
