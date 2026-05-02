"""Generation API — triggers the 7-agent pipeline with provider selection."""

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
    audit_report: str = ""
    observer_notes: str = ""
    summary: str = ""
    metadata: dict = {}


def _build_orchestrator():
    """Build PipelineOrchestrator using configured LLM provider."""
    from ..config import settings
    from ..llm import LLMConfig, create_provider

    # Provider → config mapping
    provider_settings = {
        "openai":    ("openai", settings.openai_api_key, settings.openai_base_url),
        "deepseek":  ("openai", settings.deepseek_api_key, settings.deepseek_base_url),
        "anthropic": ("anthropic", settings.anthropic_api_key, ""),
        "ollama":    ("openai", "", settings.ollama_base_url),
        "google":    ("openai", "", ""),
        "custom":    ("openai", "", ""),
    }

    provider_name = settings.llm_provider.lower()
    ptype, api_key, base_url = provider_settings.get(
        provider_name,
        ("openai", settings.openai_api_key, settings.openai_base_url),
    )

    cfg = LLMConfig(provider=ptype, api_key=api_key or "", base_url=base_url or "")
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
        from ..narrative.engine import NarrativeEngine

        orch = _build_orchestrator()

        # 注入叙事节奏
        ne = NarrativeEngine()
        beats = ne.get_required_beats(req.chapter_number, 20)
        narrative_ctx = "本章叙事阶段: " + " → ".join(beats) + "\n"
        for b in beats:
            narrative_ctx += f"- {b}: {ne.get_stage_prompt(b)}\n"

        context = AgentContext(
            chapter_number=req.chapter_number,
            chapter_outline=req.outline or f"Chapter {req.chapter_number}",
            world_context=req.world_context,
            pov_character=req.pov_character,
            prior_summary=req.prior_summary,
            project_id=req.project_id,
            thread_context=narrative_ctx,
        )

        result = await orch.run(context)
        errors = [p.error for p in result.phases if p.error]
        failed_phases = [p.name for p in result.phases if not p.success]

        # 提取各阶段输出
        audit_report = ""
        observer_notes = ""
        summary_txt = ""
        for p in result.phases:
            if p.name.startswith("auditor"):
                audit_report = p.result
            elif p.name == "observer":
                observer_notes = p.result
            elif p.name == "summary":
                summary_txt = p.result

        return GenerateResponse(
            success=result.passed,
            chapter_number=result.chapter_number,
            content=result.content,
            phases=[p.__dict__ for p in result.phases],
            passed_audit=result.passed,
            error="; ".join(errors) if errors else (
                "Failed phases: " + ", ".join(failed_phases) if failed_phases else ""
            ),
            audit_report=audit_report,
            observer_notes=observer_notes,
            summary=summary_txt,
            metadata=result.metadata,
        )
    except Exception as e:
        raise HTTPException(500, str(e))
