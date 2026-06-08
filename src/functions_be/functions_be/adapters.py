"""Runtime adapters + registry (be_004/005/006).

One interface per runtime: provision deps → execute (stream events) → collect outputs.
``bash``/``python``/``custom`` run subprocesses; ``claude`` drives the CLI and shares the
pipeline session. New runtimes register here with no core change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

from functions_shared import (
    FN_INPUTS,
    FN_OUTPUTS,
    Capabilities,
    FunctionManifest,
    input_env_mirror,
)

from . import sandbox
from .container import Container
from .events import Event


@dataclass
class RunContext:
    run_id: str
    step_id: str
    function: FunctionManifest
    function_dir: Path  # host dir (for reading prompt.md)
    function_cpath: str  # in-container path to the function dir
    container: Container
    inputs: dict
    env: dict
    session_id: str
    first_claude: bool = False
    returncode: int = 0
    output_rel: Optional[str] = None


class UnknownRuntimeError(ValueError):
    pass


def _prepare_io(ctx: RunContext) -> dict:
    """Write the inputs file (workspace-relative), point FN_INPUTS/FN_OUTPUTS at the
    in-container paths, and mirror scalar inputs to env."""
    in_rel = f".functions/{ctx.step_id}.in.json"
    out_rel = f".functions/{ctx.step_id}.out.json"
    in_cpath = ctx.container.write(in_rel, json.dumps(ctx.inputs))
    ctx.output_rel = out_rel
    env = dict(ctx.env)
    env[FN_INPUTS] = in_cpath
    env[FN_OUTPUTS] = ctx.container.container_path(out_rel)
    env.update(input_env_mirror(ctx.inputs))
    return env


class RuntimeAdapter:
    runtime: str = ""
    capabilities: Capabilities

    async def provision(self, fn: FunctionManifest, container: Container) -> None:
        return None

    async def execute(self, ctx: RunContext) -> AsyncIterator[Event]:  # pragma: no cover
        raise NotImplementedError
        yield  # pragma: no cover

    async def collect(self, ctx: RunContext) -> dict:
        text = ctx.container.read(ctx.output_rel) if ctx.output_rel else ""
        return json.loads(text) if text.strip() else {}


class SubprocessAdapter(RuntimeAdapter):
    def _argv(self, fn: FunctionManifest, function_cpath: str) -> list[str]:
        raise NotImplementedError

    def _deps(self, fn: FunctionManifest) -> list[str]:
        return []

    def _install_argv(self, deps: list[str]) -> Optional[list[str]]:
        return None

    async def provision(self, fn, container):
        deps = self._deps(fn)
        argv = self._install_argv(deps) if deps else None
        if argv is None:
            return
        async for _ in container.exec_stream(argv):
            pass

    async def execute(self, ctx):
        env = _prepare_io(ctx)
        argv = self._argv(ctx.function, ctx.function_cpath)
        async for line in ctx.container.exec_stream(argv, env=env):
            yield Event("text", ctx.run_id, ctx.step_id, 0, {"text": line})
        ctx.returncode = ctx.container.last_returncode


class BashAdapter(SubprocessAdapter):
    runtime = "bash"
    capabilities = Capabilities(
        is_llm=False, memory="none", default_entrypoint="run.sh", dep_kinds=["system"]
    )

    def _argv(self, fn, function_cpath):
        return ["bash", f"{function_cpath}/{fn.resolved_entrypoint()}"]

    def _deps(self, fn):
        return fn.dependencies.system

    def _install_argv(self, deps):
        return ["apt-get", "install", "-y", *deps]


class PythonAdapter(SubprocessAdapter):
    runtime = "python"
    capabilities = Capabilities(
        is_llm=False, memory="none", default_entrypoint="main.py", dep_kinds=["python"]
    )

    def _argv(self, fn, function_cpath):
        return ["python3", f"{function_cpath}/{fn.resolved_entrypoint()}"]

    def _deps(self, fn):
        return fn.dependencies.python

    def _install_argv(self, deps):
        return ["python3", "-m", "pip", "install", *deps]


class CustomAdapter(SubprocessAdapter):
    runtime = "custom"
    capabilities = Capabilities(
        is_llm=False, memory="none", default_entrypoint="Makefile", dep_kinds=[]
    )

    def _argv(self, fn, function_cpath):
        return ["make", "-C", function_cpath, "run"]


class ClaudeAdapter(RuntimeAdapter):
    runtime = "claude"
    capabilities = Capabilities(
        is_llm=True, memory="session", default_entrypoint="prompt.md", dep_kinds=[]
    )

    def build_argv(self, ctx: RunContext, prompt: str) -> list[str]:
        session_flag = "--session-id" if ctx.first_claude else "--resume"
        return [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            *sandbox.claude_permission_args(),
            "--add-dir",
            ctx.function_cpath,
            session_flag,
            ctx.session_id,
        ]

    async def execute(self, ctx):
        env = _prepare_io(ctx)
        prompt = (ctx.function_dir / ctx.function.resolved_entrypoint()).read_text()
        argv = self.build_argv(ctx, prompt)
        async for line in ctx.container.exec_stream(argv, env=env):
            for event in self._translate(line, ctx):
                yield event
        ctx.returncode = ctx.container.last_returncode

    def _translate(self, line: str, ctx: RunContext):
        line = line.strip()
        if not line:
            return
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            return
        kind = obj.get("type")
        if kind == "assistant":
            for block in obj.get("message", {}).get("content", []):
                if block.get("type") == "text" and block.get("text"):
                    yield Event("text", ctx.run_id, ctx.step_id, 0, {"text": block["text"]})
                elif block.get("type") == "tool_use":
                    yield Event("tool", ctx.run_id, ctx.step_id, 0, {"name": block.get("name")})
        elif kind == "result" and obj.get("result"):
            yield Event("text", ctx.run_id, ctx.step_id, 0, {"text": obj["result"]})


def build_registry() -> dict[str, RuntimeAdapter]:
    adapters = [BashAdapter(), PythonAdapter(), ClaudeAdapter(), CustomAdapter()]
    return {a.runtime: a for a in adapters}


def get_adapter(registry: dict[str, RuntimeAdapter], runtime: str) -> RuntimeAdapter:
    try:
        return registry[runtime]
    except KeyError:
        raise UnknownRuntimeError(f"unknown runtime: {runtime!r}") from None
