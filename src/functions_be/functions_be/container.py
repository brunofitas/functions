"""Container abstraction. LocalContainer (host) + DockerContainer (real Docker).

The engine addresses files by a *workspace-relative* path; the container maps that to
where bytes are written on the host and to the path the process sees. For LocalContainer
host == container; for DockerContainer the host workspace is bind-mounted at /work, so we
write host-side and hand the process the in-container path. Functions are made available
inside the container via ``mount_function`` (copied under the workspace).
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import AsyncIterator, Optional, Protocol, runtime_checkable


@runtime_checkable
class Container(Protocol):
    @property
    def workspace(self) -> Path: ...

    @property
    def last_returncode(self) -> int: ...

    def write(self, rel: str, content: str) -> str: ...  # → in-container path

    def read(self, rel: str) -> str: ...

    def container_path(self, rel: str) -> str: ...

    def mount_function(self, host_dir: Path) -> str: ...  # → in-container path

    def exec_stream(
        self, argv: list[str], *, cwd: Optional[str] = None, env: Optional[dict] = None
    ) -> AsyncIterator[str]: ...


class LocalContainer:
    """Runs steps on the host in a workspace directory (no Docker). host == container."""

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

    def write(self, rel: str, content: str) -> str:
        p = self._ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return str(p)

    def read(self, rel: str) -> str:
        p = self._ws / rel
        return p.read_text() if p.exists() else ""

    def container_path(self, rel: str) -> str:
        return str(self._ws / rel)

    def mount_function(self, host_dir: Path) -> str:
        return str(host_dir)

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

    The host workspace dir is bind-mounted at ``workspace`` (default /work) by the
    ContainerManager, so workspace-relative writes happen host-side and the process sees
    the in-container path.
    """

    def __init__(self, container_id: str, host_workspace: str | Path, workspace: str = "/work"):
        self._cid = container_id
        self._host = Path(host_workspace)  # created by the caller / write() as needed
        self._ws = Path(workspace)
        self._rc = 0

    @property
    def workspace(self) -> Path:
        return self._ws

    @property
    def last_returncode(self) -> int:
        return self._rc

    def container_path(self, rel: str) -> str:
        return f"{self._ws.as_posix()}/{rel}"

    def write(self, rel: str, content: str) -> str:
        p = self._host / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return self.container_path(rel)

    def read(self, rel: str) -> str:
        p = self._host / rel
        return p.read_text() if p.exists() else ""

    def mount_function(self, host_dir: Path) -> str:
        name = Path(host_dir).name
        dest = self._host / ".fn" / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(host_dir, dest)
        return self.container_path(f".fn/{name}")

    def docker_argv(self, argv, *, cwd=None, env=None) -> list[str]:
        out = ["docker", "exec", "-w", str(cwd or self._ws.as_posix())]
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
