"""Pipeline runner — sequential chain from a pipeline manifest (be_009)."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator, Optional

from functions_shared import PipelineManifest, parse_ref, resolve

from .adapters import build_registry
from .container import Container
from .control import RunControl
from .engine import Engine
from .env import EnvBus
from .events import Event
from .loader import load_function, resolve_local_ref


async def run_pipeline(
    pipeline: PipelineManifest,
    *,
    base_dir: str | Path,
    container: Container,
    env_bus: Optional[EnvBus] = None,
    registry: Optional[dict] = None,
    run_id: str = "run",
    session_id: str = "session",
    control: Optional[RunControl] = None,
) -> AsyncIterator[Event]:
    env_bus = env_bus or EnvBus()
    registry = registry or build_registry()
    engine = Engine(container, registry, env_bus, run_id, session_id)
    streaming = pipeline.flow.mode == "streaming"
    context: dict = {
        "steps": {},
        "secrets": env_bus.secret_values(),
        "env": env_bus.global_env,
        "inputs": {},
    }

    yield Event("run_start", run_id, payload={"mode": pipeline.flow.mode})
    for step in pipeline.steps:
        if control is not None:
            await control.checkpoint()  # pause = backpressure
            if control.cancelled:
                break
        ref = parse_ref(step.use)
        fn_dir = resolve_local_ref(ref, base_dir)
        loaded = load_function(fn_dir)
        inputs = resolve(step.with_, context)
        async for event in engine.run_step(loaded, step.id, inputs):
            yield event
        context["steps"][step.id] = {"outputs": engine.outputs_by_step.get(step.id, {})}

    # END signal propagates downstream on shutdown (streaming) or cancellation.
    if streaming or (control is not None and control.cancelled):
        yield Event("end", run_id, payload={"signal": pipeline.flow.end.signal})
    yield Event("run_end", run_id)
