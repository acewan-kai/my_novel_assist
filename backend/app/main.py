"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import projects, chapters, generation

app = FastAPI(
    title="My Novel Assist",
    version="0.2.0",
    description="AI-powered novel writing assistant — Dramatica-flow inspired 7-agent pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(generation.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
