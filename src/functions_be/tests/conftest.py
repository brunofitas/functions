from pathlib import Path

from functions_be import RunContext
from functions_shared import FunctionManifest


class FakeContainer:
    """In-memory container for unit tests: records exec calls, replays canned lines."""

    def __init__(self, workspace, lines=None):
        self._ws = Path(workspace)
        self._ws.mkdir(parents=True, exist_ok=True)
        self._lines = list(lines or [])
        self.last_returncode = 0
        self.calls: list[list[str]] = []

    @property
    def workspace(self):
        return self._ws

    def write(self, rel, content):
        p = self._ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return str(p)

    def read(self, rel):
        p = self._ws / rel
        return p.read_text() if p.exists() else ""

    def container_path(self, rel):
        return str(self._ws / rel)

    def mount_function(self, host_dir):
        return str(host_dir)

    async def exec_stream(self, argv, *, cwd=None, env=None):
        self.calls.append(argv)
        for line in self._lines:
            yield line


def make_function(directory: Path, *, runtime, name, entrypoint, body, manifest_extra=None):
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {
        "kind": "function",
        "namespace": "demo",
        "name": name,
        "runtime": runtime,
        **(manifest_extra or {}),
    }
    import yaml

    (directory / "function.yaml").write_text(yaml.safe_dump(manifest))
    (directory / entrypoint).write_text(body)
    return directory


def make_context(function_dir: Path, container, *, runtime="claude", inputs=None, first_claude=True):
    fn = FunctionManifest(namespace="demo", name="f", runtime=runtime)
    return RunContext(
        run_id="r",
        step_id="s",
        function=fn,
        function_dir=function_dir,
        function_cpath=str(function_dir),
        container=container,
        inputs=inputs or {},
        env={},
        session_id="sess-1",
        first_claude=first_claude,
    )


async def collect_events(agen):
    return [event async for event in agen]
