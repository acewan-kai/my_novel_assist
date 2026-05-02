"""Observer Agent — extracts facts from written chapter content."""

from .base import BaseAgent, AgentContext, AgentResult

OBSERVER_SYSTEM = """You are the Observer Agent. Extract structured facts from chapter text:
1. Character position/location changes
2. Emotional state shifts (character: emotion: 1-10)
3. Relationship changes
4. New hooks (type: mystery/promise/foreshadow/conflict)
5. Hooks resolved/advanced
6. Key events for causal chain
7. New information revealed
8. Resource/status changes
Output as structured JSON. Be exhaustive."""


class ObserverAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        prompt = f"""Extract observations from Chapter {context.chapter_number}.
Content: {context.chapter_outline}"""
        resp = self.llm.complete(self._messages(OBSERVER_SYSTEM, prompt))
        return AgentResult(success=resp.finished, content=resp.content)
