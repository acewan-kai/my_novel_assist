"""Chapter management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


class ChapterCreate(BaseModel):
    number: int
    title: str = ""
    pov_character: str = ""


class ChapterResponse(BaseModel):
    number: int
    title: str
    pov_character: str
    word_count: int = 0
    status: str = "draft"
    content: str = ""


_chapters: dict[str, dict[int, ChapterResponse]] = {}


@router.post("", response_model=ChapterResponse)
async def create_chapter(project_id: str, data: ChapterCreate):
    if project_id not in _chapters:
        _chapters[project_id] = {}
    ch = ChapterResponse(
        number=data.number,
        title=data.title,
        pov_character=data.pov_character,
    )
    _chapters[project_id][data.number] = ch
    return ch


@router.get("", response_model=list[ChapterResponse])
async def list_chapters(project_id: str):
    return list(_chapters.get(project_id, {}).values())


@router.get("/{chapter_number}", response_model=ChapterResponse)
async def get_chapter(project_id: str, chapter_number: int):
    ch = _chapters.get(project_id, {}).get(chapter_number)
    if not ch:
        raise HTTPException(404, "Chapter not found")
    return ch


@router.put("/{chapter_number}/content", response_model=ChapterResponse)
async def update_chapter_content(project_id: str, chapter_number: int, data: dict):
    ch = _chapters.get(project_id, {}).get(chapter_number)
    if not ch:
        raise HTTPException(404, "Chapter not found")
    ch.content = data.get("content", ch.content)
    ch.word_count = len(ch.content.replace("\n", " ").split())
    ch.status = data.get("status", ch.status)
    return ch
