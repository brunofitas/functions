"""The Event type — the universal stream shape (d_be_002)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

EVENT_KINDS = (
    "run_start",
    "step_start",
    "text",
    "tool",
    "status",
    "error",
    "step_end",
    "run_end",
    "end",
)


@dataclass(frozen=True)
class Event:
    kind: str
    run_id: str
    step_id: Optional[str] = None
    seq: int = 0
    payload: Optional[dict] = None
