"""Writer Agent — generates chapter prose."""

from .base import BaseAgent, AgentContext, AgentResult

WRITER_SYSTEM = """You are the Writer Agent. Write chapter prose.
IRON LAWS:
1. Never break POV character's perspective
2. Every scene serves the causal chain
3. Characters only know what they've learned
4. Show emotions through action/dialogue
5. End with a hook
Write in Chinese. Use active voice. Show don't tell.
End with ===SETTLEMENT=== section for character/emotional/hook changes."""


class WriterAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        prompt = f"""Write Chapter {context.chapter_number}.
Blueprint: {context.chapter_outline}
World: {context.world_context}
Prior: {context.prior_summary}
POV: {context.pov_character}
Thread: {context.thread_context}
Hooks: {context.pending_hooks}"""
        resp = self.llm.complete(self._messages(WRITER_SYSTEM, prompt))
        return AgentResult(success=resp.finished, content=resp.content,
                          data={"word_count": len(resp.content)})
