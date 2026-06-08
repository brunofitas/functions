"""Run lifecycle control (be_013): pause/resume (gate backpressure), cancel, END.

pause clears a gate the runner awaits before each step (backpressure, per d_be_002);
cancel sets a flag so the runner drains and emits the END signal.
"""

from __future__ import annotations

import asyncio
from typing import Callable


class RunControl:
    def __init__(self) -> None:
        self._gate = asyncio.Event()
        self._gate.set()  # set == running
        self.cancelled = False

    @property
    def paused(self) -> bool:
        return not self._gate.is_set()

    def pause(self) -> None:
        self._gate.clear()

    def resume(self) -> None:
        self._gate.set()

    def cancel(self) -> None:
        self.cancelled = True
        self._gate.set()  # unblock any awaiter so it can observe cancellation

    async def checkpoint(self) -> None:
        """Block while paused; returns immediately when running or cancelled."""
        await self._gate.wait()

    async def wait_until(self, predicate: Callable[[], bool], poll: float = 0.01) -> None:
        """Wait until *predicate* holds or the run is cancelled (condition wait)."""
        while not predicate() and not self.cancelled:
            await asyncio.sleep(poll)
