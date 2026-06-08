import asyncio


from conftest import collect_events, make_function
from functions_be import LocalContainer, RunControl, run_pipeline
from functions_shared import PipelineManifest


def _pipeline(tmp_path, mode="standalone"):
    fn = make_function(
        tmp_path / "noop",
        runtime="bash",
        name="noop",
        entrypoint="run.sh",
        body='printf \'{"ok":true}\' > "$FN_OUTPUTS"\n',
        manifest_extra={"outputs": [{"name": "ok", "type": "boolean"}]},
    )
    return PipelineManifest.model_validate(
        {
            "namespace": "demo",
            "name": "p",
            "flow": {"mode": mode},
            "steps": [{"id": "a", "use": str(fn)}, {"id": "b", "use": str(fn)}],
        }
    )


def test_control_pause_resume_cancel_state():
    c = RunControl()
    assert not c.paused
    c.pause()
    assert c.paused
    c.resume()
    assert not c.paused
    c.cancel()
    assert c.cancelled and not c.paused  # cancel unblocks the gate


async def test_checkpoint_blocks_until_resumed():
    c = RunControl()
    c.pause()
    task = asyncio.ensure_future(c.checkpoint())
    await asyncio.sleep(0.01)
    assert not task.done()  # blocked while paused
    c.resume()
    await asyncio.wait_for(task, timeout=1)


async def test_cancel_stops_pipeline_and_emits_end(tmp_path):
    control = RunControl()
    control.cancel()  # cancel before it starts → no steps run, END emitted
    container = LocalContainer(tmp_path / "work")
    events = await collect_events(
        run_pipeline(_pipeline(tmp_path), base_dir=tmp_path, container=container, control=control)
    )
    kinds = [e.kind for e in events]
    assert "step_start" not in kinds  # cancelled before any step
    assert "end" in kinds and kinds[-1] == "run_end"


async def test_streaming_mode_emits_end_signal(tmp_path):
    container = LocalContainer(tmp_path / "work")
    events = await collect_events(
        run_pipeline(_pipeline(tmp_path, mode="streaming"), base_dir=tmp_path, container=container)
    )
    end = next(e for e in events if e.kind == "end")
    assert end.payload["signal"] == "END"


async def test_wait_until_predicate(tmp_path):
    c = RunControl()
    flag = {"ready": False}

    async def flip():
        await asyncio.sleep(0.02)
        flag["ready"] = True

    asyncio.ensure_future(flip())
    await asyncio.wait_for(c.wait_until(lambda: flag["ready"]), timeout=1)
    assert flag["ready"]
