"""
StoryRecorder — append-only markdown log of all story events.
"""
from __future__ import annotations
import datetime
from pathlib import Path
from config import STORIES_DIR


class StoryRecorder:
    def __init__(self, story_file: Path | None = None) -> None:
        if story_file is None:
            date_str = datetime.date.today().strftime("%Y%m%d")
            self.story_file = STORIES_DIR / f"story_{date_str}.md"
        else:
            self.story_file = story_file

        # Write header if new file
        if not self.story_file.exists():
            with open(self.story_file, "w", encoding="utf-8") as f:
                started = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                f.write(f"# Story — {started}\n\n")

    def append_entry(
        self,
        speaker: str,
        content: str,
        entry_type: str = "dialogue",
    ) -> None:
        """
        entry_type: 'dialogue' | 'narration'
        """
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with open(self.story_file, "a", encoding="utf-8") as f:
            if entry_type == "narration":
                f.write(f"\n*[{ts}] {content}*\n")
            else:
                f.write(f"\n**{speaker}** `[{ts}]`: {content}\n")

    def print_story(self) -> str:
        if self.story_file.exists():
            return self.story_file.read_text(encoding="utf-8")
        return "*(no story yet)*"

    @property
    def path(self) -> Path:
        return self.story_file
