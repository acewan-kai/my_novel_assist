"""Project CRUD API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    title: str
    author: str = ""
    premise: str = ""


class ProjectResponse(BaseModel):
    id: str
    title: str
    author: str
    premise: str
    chapter_count: int = 0
    created: str = ""
    updated: str = ""


_projects: dict[str, ProjectResponse] = {}


@router.post("", response_model=ProjectResponse)
async def create_project(data: ProjectCreate):
    import uuid
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    proj = ProjectResponse(
        id=str(uuid.uuid4())[:8],
        title=data.title,
        author=data.author,
        premise=data.premise,
        created=now,
        updated=now,
    )
    _projects[proj.id] = proj
    return proj


@router.get("", response_model=list[ProjectResponse])
async def list_projects():
    return list(_projects.values())


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    proj = _projects.get(project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    return proj


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    if project_id not in _projects:
        raise HTTPException(404, "Project not found")
    del _projects[project_id]
    return {"ok": True}
