"""Agent Coordinator — orchestrates 7-layer pipeline with phase tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .base import AgentContext


@dataclass
class PhaseResult:
    name: str = ""
    duration: float = 0.0
    success: bool = True
    result: str = ""
    error: str = ""

    @property
    def duration_ms(self) -> int:
        return int(self.duration * 1000)


@dataclass
class PipelineResult:
    chapter_number: int = 0
    content: str = ""
    phases: list[PhaseResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    passed: bool = False


class PipelineOrchestrator:
    def __init__(self):
        self.agents: dict[str, Any] = {}

    def register(self, name: str, agent: Any):
        self.agents[name] = agent

    async def run(self, context: AgentContext) -> PipelineResult:
        start = time.time()
        result = PipelineResult(chapter_number=context.chapter_number)
        phases = []

        # Phase 1: Plan
        if p := self.agents.get("planner"):
            t0 = time.time()
            try:
                r = await p.run(context)
                phases.append(PhaseResult("planner", time.time() - t0, r.success, r.content))
                context.extra["intent"] = r.content
            except Exception as e:
                phases.append(PhaseResult("planner", time.time() - t0, False, error=str(e)))

        # Phase 2: Architect
        if a := self.agents.get("architect"):
            t0 = time.time()
            try:
                r = await a.run(context)
                phases.append(PhaseResult("architect", time.time() - t0, r.success, r.content))
                context.extra["blueprint"] = r.content
            except Exception as e:
                phases.append(PhaseResult("architect", time.time() - t0, False, error=str(e)))

        # Phase 3: Write
        if w := self.agents.get("writer"):
            t0 = time.time()
            try:
                r = await w.run(context)
                phases.append(PhaseResult("writer", time.time() - t0, r.success, r.content))
                result.content = r.content
                context.extra["chapter_draft"] = r.content
            except Exception as e:
                phases.append(PhaseResult("writer", time.time() - t0, False, error=str(e)))

        # Phase 4: Audit → Revise loop
        if au := self.agents.get("auditor"):
            for rnd in range(3):
                t0 = time.time()
                try:
                    r = await au.run(context)
                    phases.append(PhaseResult(f"auditor_r{rnd}", time.time() - t0, r.success, r.content))
                    context.extra["audit_report"] = r.content
                except Exception as e:
                    phases.append(PhaseResult(f"auditor_r{rnd}", time.time() - t0, False, error=str(e)))
                    break
                if "❌ FAIL" not in r.content and "⚠️ WARNING" not in r.content:
                    break
                if rv := self.agents.get("reviser"):
                    t0 = time.time()
                    try:
                        context.extra["mode"] = "spot-fix" if rnd == 0 else "rewrite-section"
                        r2 = await rv.run(context)
                        phases.append(PhaseResult(f"reviser_r{rnd}", time.time() - t0, r2.success, r2.content))
                        context.extra["chapter_draft"] = r2.content
                        context.chapter_outline = r2.content
                    except Exception as e:
                        phases.append(PhaseResult(f"reviser_r{rnd}", time.time() - t0, False, error=str(e)))
                        break

        # Phase 5: Observe
        if o := self.agents.get("observer"):
            t0 = time.time()
            try:
                r = await o.run(context)
                phases.append(PhaseResult("observer", time.time() - t0, r.success, r.content))
            except Exception as e:
                phases.append(PhaseResult("observer", time.time() - t0, False, error=str(e)))

        # Phase 6: Summary
        if s := self.agents.get("summary"):
            t0 = time.time()
            try:
                r = await s.run(context)
                phases.append(PhaseResult("summary", time.time() - t0, r.success, r.content))
            except Exception as e:
                phases.append(PhaseResult("summary", time.time() - t0, False, error=str(e)))

        result.phases = phases
        total = time.time() - start
        result.metadata = {
            "total_duration_ms": int(total * 1000),
            "agent_performance": {p.name: {"duration_ms": p.duration_ms, "success": p.success} for p in phases},
        }
        result.passed = all(p.success for p in phases if not p.name.startswith("reviser"))
        return result
