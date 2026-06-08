"""Container abstraction. LocalContainer (host, for dev/tests) + DockerContainer.

The execution engine talks to a Container; the real warm-container lifecycle (create /
recreate / warm-up / reuse) is hardened in infra_002. LocalContainer runs steps on the
host so the engine is fully testable without Docker.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncIterator, Optional, Protocol, runtime_checkable


@runtime_checkable
class Container(Protocol):
    @property
    def workspace(self) -> Path: ...

    @property
    def last_returncode(self) -> int: ...

    def path(self, rel: str) -> Path: ...

    def exec_stream(
        self, argv: list[str], *, cwd: Optional[str] = None, env: Optional[dict] = None
    ) -> AsyncIterator[str]: ...


class LocalContainer:
    """Runs steps on the host in a workspace directory (no Docker)."""

    def __init__(self, workspace: str | Path):
        self._ws = Path(workspace)
        self._ws.mkdir(parents=True, exist_ok=True)
        self._rc = 0

    @property
    def workspace(self) -> Path:
        return self._ws

    @property
    def last_returncode(self) -> int:
        return self._rc

    def path(self, rel: str) -> Path:
        return self._ws / rel

    async def exec_stream(self, argv, *, cwd=None, env=None) -> AsyncIterator[str]:
        full_env = {**os.environ, **(env or {})}
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=str(cwd or self._ws),
            env=full_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout is not None
        async for raw in proc.stdout:
            yield raw.decode(errors="replace").rstrip("\n")
        self._rc = await proc.wait()


class DockerContainer:
    """Runs steps inside a Docker container via ``docker exec``.

    Volume/mount mapping for I/O files is wired by infra_002; here we build the exec
    command. The live stream requires a running daemon, so it is not unit-tested.
    """

    def __init__(self, container_id: str, workspace: str | Path = "/work"):
        self._cid = container_id
        self._ws = Path(workspace)
        self._rc = 0

    @property
    def workspace(self) -> Path:
        return self._ws

    @property
    def last_returncode(self) -> int:
        return self._rc

    def path(self, rel: str) -> Path:
        return self._ws / rel

    def docker_argv(self, argv, *, cwd=None, env=None) -> list[str]:
        out = ["docker", "exec", "-w", str(cwd or self._ws)]
        for key, value in (env or {}).items():
            out += ["-e", f"{key}={value}"]
        out += [self._cid, *argv]
        return out

    async def exec_stream(self, argv, *, cwd=None, env=None) -> AsyncIterator[str]:  # pragma: no cover
        full = self.docker_argv(argv, cwd=cwd, env=env)
        proc = await asyncio.create_subprocess_exec(
            *full, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        assert proc.stdout is not None
        async for raw in proc.stdout:
            yield raw.decode(errors="replace").rstrip("\n")
        self._rc = await proc.wait()
