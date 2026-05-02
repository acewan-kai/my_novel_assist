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


@router.post("/chapter", response_model=GenerateResponse)
async def generate_chapter(req: GenerateRequest):
    """Run the full 7-agent pipeline to generate a chapter."""
    try:
        from ..pipeline import PipelineOrchestrator
        from ..llm import create_provider
        from ..config import settings

        provider = create_provider(settings)
        orchestrator = PipelineOrchestrator(provider=provider)

        result = await orchestrator.run(
            chapter_number=req.chapter_number,
            outline=req.outline or f"Chapter {req.chapter_number}",
            world_context=req.world_context,
            pov_character=req.pov_character,
            prior_summary=req.prior_summary,
        )

        if result.success:
            return GenerateResponse(
                success=True,
                chapter_number=result.chapter_number,
                content=result.content,
                phases=[p.to_dict() for p in result.phases],
                passed_audit=result.passed,
            )
        else:
            return GenerateResponse(
                success=False,
                chapter_number=req.chapter_number,
                error=result.error or "Generation failed",
            )
    except Exception as e:
        raise HTTPException(500, str(e))
