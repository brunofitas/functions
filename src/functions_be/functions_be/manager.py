"""Container lifecycle manager (infra_002).

Implements d_infra_001: fresh-per-run container off the shared base image, with
workspace/lib/dep-cache volumes, recreate-on-missing, and teardown. Docker invocations
go through an injectable CLI runner so the logic is testable without a daemon.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

from .container import DockerContainer

CliRunner = Callable[[list[str]], "tuple[int, str]"]


class DockerError(RuntimeError):
    pass


def _default_runner(argv: list[str]) -> tuple[int, str]:  # pragma: no cover — shells to docker
    proc = subprocess.run(argv, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "").strip()


@dataclass
class Mounts:
    workspace: str  # → /work (per run)
    lib: str  # → /lib (function library)
    cache: str  # → /cache (shared dependency cache)


class ContainerManager:
    def __init__(self, image: str = "functions-base:local", runner: Optional[CliRunner] = None):
        self.image = image
        self._run: CliRunner = runner or _default_runner

    def name(self, run_id: str) -> str:
        return f"functions-{run_id}"

    def create_argv(self, run_id: str, mounts: Mounts) -> list[str]:
        return [
            "docker", "run", "-d", "--name", self.name(run_id),
            "-v", f"{mounts.workspace}:/work",
            "-v", f"{mounts.lib}:/lib",
            "-v", f"{mounts.cache}:/cache",
            "-w", "/work",
            self.image, "sleep", "infinity",
        ]

    def rm_argv(self, run_id: str) -> list[str]:
        return ["docker", "rm", "-f", self.name(run_id)]

    def exists(self, run_id: str) -> bool:
        rc, out = self._run(["docker", "ps", "-aq", "-f", f"name=^{self.name(run_id)}$"])
        return rc == 0 and bool(out.strip())

    def ensure_ready(self, run_id: str, mounts: Mounts) -> DockerContainer:
        """Create the run's container if missing (recreate-on-missing); return a handle."""
        if not self.exists(run_id):
            rc, out = self._run(self.create_argv(run_id, mounts))
            if rc != 0:
                raise DockerError(f"failed to create container {self.name(run_id)}: {out}")
        return DockerContainer(self.name(run_id), workspace="/work")

    def teardown(self, run_id: str) -> None:
        self._run(self.rm_argv(run_id))
