"""Generation API endpoints — triggers the 7-agent pipeline."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/generate", tags=["generation"])


class GenerateRequest(BaseModel):
    project_id: str
    chapter_number: int
    outline: str = ""
    world_context: str = ""
    pov_character: str = ""
    prior_summary: str = ""


class GenerateResponse(BaseModel):
    success: bool
    chapter_number: int
    content: str = ""
    phases: list[dict] = []
    passed_audit: bool = False
    error: str = ""


def _build_orchestrator():
    """Build a fully registered PipelineOrchestrator."""
    from ..config import settings
    from ..llm import LLMConfig, create_provider

    cfg = LLMConfig(
        provider="openai",
        api_key=settings.openai_api_key or "",
        base_url=settings.openai_base_url or "",
    )
    provider = create_provider(cfg)

    from ..pipeline import PipelineOrchestrator
    from ..pipeline.planner import PlannerAgent
    from ..pipeline.architect import ArchitectAgent
    from ..pipeline.writer import WriterAgent
    from ..pipeline.auditor import AuditorAgent
    from ..pipeline.reviser import ReviserAgent
    from ..pipeline.observer import ObserverAgent
    from ..pipeline.summary import SummaryAgent

    orch = PipelineOrchestrator()
    orch.register("planner", PlannerAgent(provider))
    orch.register("architect", ArchitectAgent(provider))
    orch.register("writer", WriterAgent(provider))
    orch.register("auditor", AuditorAgent(provider))
    orch.register("reviser", ReviserAgent(provider))
    orch.register("observer", ObserverAgent(provider))
    orch.register("summary", SummaryAgent(provider))
    return orch


@router.post("/chapter", response_model=GenerateResponse)
async def generate_chapter(req: GenerateRequest):
    """Run the full 7-agent pipeline to generate a chapter."""
    try:
        from ..pipeline.base import AgentContext

        orch = _build_orchestrator()
        context = AgentContext(
            chapter_number=req.chapter_number,
            chapter_outline=req.outline or f"Chapter {req.chapter_number}",
            world_context=req.world_context,
            pov_character=req.pov_character,
            prior_summary=req.prior_summary,
            project_id=req.project_id,
        )

        result = await orch.run(context)
        errors = [p.error for p in result.phases if p.error]
        failed_phases = [p.name for p in result.phases if not p.success]

        return GenerateResponse(
            success=result.passed,
            chapter_number=result.chapter_number,
            content=result.content,
            phases=[p.__dict__ for p in result.phases],
            passed_audit=result.passed,
            error="; ".join(errors) if errors else ("Failed phases: " + ", ".join(failed_phases) if failed_phases else ""),
        )
    except Exception as e:
        raise HTTPException(500, str(e))
