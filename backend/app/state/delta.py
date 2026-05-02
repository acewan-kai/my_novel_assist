"""Delta state tracking — record and replay narrative changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StateDelta:
    field: str = ""
    old_value: Any = None
    new_value: Any = None
    timestamp: str = ""
    agent: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class DeltaStore:
    def __init__(self):
        self._deltas: list[StateDelta] = []
        self._checkpoints: dict[str, int] = {}

    def record(self, field: str, old: Any, new: Any, agent: str = "system"):
        self._deltas.append(StateDelta(field=field, old_value=old, new_value=new, agent=agent))

    def checkpoint(self, label: str) -> bool:
        self._checkpoints[label] = len(self._deltas)
        return True

    def rollback(self, label: str) -> list[StateDelta]:
        idx = self._checkpoints.get(label)
        if idx is None:
            return []
        reverted = self._deltas[idx:]
        self._deltas = self._deltas[:idx]
        return reverted

    @property
    def history(self) -> list[StateDelta]:
        return list(self._deltas)

    def clear(self):
        self._deltas.clear()
        self._checkpoints.clear()
