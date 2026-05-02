"""Input governance — InkOS-inspired control plane."""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass


@dataclass
class ControlPlane:
    author_intent: str = ""
    current_focus: str = ""
    project_id: str = ""


@dataclass
class WordBudget:
    target: int = 2000
    min_words: int = 1500
    max_words: int = 3000
    tolerance: float = 0.2

    def check(self, count: int) -> tuple[bool, str]:
        lo = int(self.target * (1 - self.tolerance))
        hi = int(self.target * (1 + self.tolerance))
        if count < lo:
            return False, f"Below ({count} < {lo})"
        if count > hi:
            return False, f"Above ({count} > {hi})"
        return True, "OK"


class ControlPlaneManager:
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)

    def _dir(self, pid: str) -> Path:
        d = self.base_dir / "projects" / pid / "governance"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def read(self, pid: str) -> ControlPlane:
        d = self._dir(pid)
        return ControlPlane(
            project_id=pid,
            author_intent=d.joinpath("author_intent.md").read_text("utf-8") if d.joinpath("author_intent.md").exists() else "",
            current_focus=d.joinpath("current_focus.md").read_text("utf-8") if d.joinpath("current_focus.md").exists() else "",
        )

    def write_intent(self, pid: str, content: str):
        self._dir(pid).joinpath("author_intent.md").write_text(content, "utf-8")

    def write_focus(self, pid: str, content: str):
        self._dir(pid).joinpath("current_focus.md").write_text(content, "utf-8")
