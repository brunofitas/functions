"""Sequential shared-session execution engine (be_001) + I/O mapping (be_007).

Runs steps from a fixed root, threads one Claude session across LLM steps, validates
outputs strictly, applies exports to the env bus, and masks secrets in streamed text.
"""

from __future__ import annotations

from typing import AsyncIterator

from functions_shared import validate_outputs

from .adapters import RunContext, RuntimeAdapter, get_adapter
from .container import Container
from .env import EnvBus, mask
from .events import Event
from .loader import LoadedFunction


class StepError(RuntimeError):
    pass


class Engine:
    def __init__(self, container: Container, registry, env_bus: EnvBus, run_id: str, session_id: str):
        self.container = container
        self.registry = registry
        self.env_bus = env_bus
        self.run_id = run_id
        self.session_id = session_id
        self._claude_started = False
        self.outputs_by_step: dict[str, dict] = {}

    async def run_step(
        self, loaded: LoadedFunction, step_id: str, inputs: dict
    ) -> AsyncIterator[Event]:
        fn = loaded.manifest
        adapter: RuntimeAdapter = get_adapter(self.registry, fn.runtime)
        env = self.env_bus.step_env(fn)
        first_claude = adapter.capabilities.is_llm and not self._claude_started
        ctx = RunContext(
            run_id=self.run_id,
            step_id=step_id,
            function=fn,
            function_dir=loaded.dir,
            container=self.container,
            inputs=inputs,
            env=env,
            session_id=self.session_id,
            first_claude=first_claude,
        )
        yield Event("step_start", self.run_id, step_id, 0, {"runtime": fn.runtime})
        await adapter.provision(fn, self.container)

        secrets = list(self.env_bus.secret_values().values())
        async for event in adapter.execute(ctx):
            if event.kind == "text" and event.payload and "text" in event.payload:
                masked = {**event.payload, "text": mask(event.payload["text"], secrets)}
                event = Event(event.kind, event.run_id, event.step_id, event.seq, masked)
            yield event

        if adapter.capabilities.memory == "session":
            self._claude_started = True

        if ctx.returncode != 0:
            yield Event("error", self.run_id, step_id, 0, {"returncode": ctx.returncode})
            raise StepError(f"step {step_id!r} exited {ctx.returncode}")

        outputs = await adapter.collect(ctx)
        validate_outputs(fn.outputs, outputs)  # ALWAYS STRICT (d_001 §5)
        self.env_bus.apply_exports(fn, outputs)
        self.outputs_by_step[step_id] = outputs
        yield Event("step_end", self.run_id, step_id, 0, {"outputs": outputs})
