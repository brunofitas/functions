"""End-to-end engine/runner tests — a real bash→python pipeline + a mocked claude step."""

import pytest

from conftest import FakeContainer, collect_events, make_function
from functions_be import (
    DictSecretStore,
    Engine,
    EnvBus,
    LocalContainer,
    StepError,
    build_registry,
    load_function,
    run_pipeline,
)
from functions_shared import OutputValidationError, PipelineManifest

GREET_SH = 'echo "greeting $INPUT_NAME"\nprintf \'{"greeting":"hello %s"}\' "$INPUT_NAME" > "$FN_OUTPUTS"\n'
SHOUT_PY = (
    "import json, os\n"
    "inp = json.load(open(os.environ['FN_INPUTS']))\n"
    "print('shouting')\n"
    "json.dump({'shout': inp['greeting'].upper()}, open(os.environ['FN_OUTPUTS'], 'w'))\n"
)


async def test_mixed_runtime_pipeline_end_to_end(tmp_path):
    greet = make_function(
        tmp_path / "greet",
        runtime="bash",
        name="greet",
        entrypoint="run.sh",
        body=GREET_SH,
        manifest_extra={
            "outputs": [{"name": "greeting", "type": "string"}],
            "requirements": {"inputs": [{"name": "name", "type": "string"}]},
        },
    )
    shout = make_function(
        tmp_path / "shout",
        runtime="python",
        name="shout",
        entrypoint="main.py",
        body=SHOUT_PY,
        manifest_extra={
            "outputs": [{"name": "shout", "type": "string"}],
            "requirements": {"inputs": [{"name": "greeting", "type": "string"}]},
        },
    )
    pipeline = PipelineManifest.model_validate(
        {
            "namespace": "demo",
            "name": "p",
            "steps": [
                {"id": "greet", "use": str(greet), "with": {"name": "world"}},
                {
                    "id": "shout",
                    "use": str(shout),
                    "with": {"greeting": "${{ steps.greet.outputs.greeting }}"},
                },
            ],
        }
    )
    container = LocalContainer(tmp_path / "work")
    events = await collect_events(
        run_pipeline(pipeline, base_dir=tmp_path, container=container, run_id="r1")
    )
    kinds = [e.kind for e in events]
    assert kinds[0] == "run_start" and kinds[-1] == "run_end"
    texts = [e.payload["text"] for e in events if e.kind == "text"]
    assert "greeting world" in texts and "shouting" in texts
    shout_end = next(e for e in events if e.kind == "step_end" and e.step_id == "shout")
    assert shout_end.payload["outputs"] == {"shout": "HELLO WORLD"}


async def test_claude_step_shares_session_across_steps(tmp_path):
    fn_dir = make_function(
        tmp_path / "ask",
        runtime="claude",
        name="ask",
        entrypoint="prompt.md",
        body="say hi",
    )
    loaded = load_function(fn_dir)
    lines = ['{"type":"assistant","message":{"content":[{"type":"text","text":"hello"}]}}']
    container = FakeContainer(tmp_path / "work", lines=lines)
    engine = Engine(container, build_registry(), EnvBus(), "r", "sess-1")

    e1 = await collect_events(engine.run_step(loaded, "a", {}))
    e2 = await collect_events(engine.run_step(loaded, "b", {}))
    assert any(e.kind == "text" and e.payload["text"] == "hello" for e in e1)
    assert any(e.kind == "step_end" for e in e2)
    # first claude step uses --session-id, second resumes
    assert "--session-id" in container.calls[0]
    assert "--resume" in container.calls[1]


async def test_strict_output_validation_fails_step(tmp_path):
    bad = make_function(
        tmp_path / "bad",
        runtime="bash",
        name="bad",
        entrypoint="run.sh",
        body='echo hi\n',  # never writes FN_OUTPUTS
        manifest_extra={"outputs": [{"name": "must_have", "type": "string"}]},
    )
    loaded = load_function(bad)
    engine = Engine(LocalContainer(tmp_path / "work"), build_registry(), EnvBus(), "r", "s")
    with pytest.raises(OutputValidationError, match="must_have"):
        await collect_events(engine.run_step(loaded, "bad", {}))


async def test_nonzero_exit_raises_step_error(tmp_path):
    boom = make_function(
        tmp_path / "boom", runtime="bash", name="boom", entrypoint="run.sh", body="exit 3\n"
    )
    loaded = load_function(boom)
    engine = Engine(LocalContainer(tmp_path / "work"), build_registry(), EnvBus(), "r", "s")
    with pytest.raises(StepError, match="exited 3"):
        await collect_events(engine.run_step(loaded, "boom", {}))


async def test_secrets_masked_in_stream(tmp_path):
    fn = make_function(
        tmp_path / "leak",
        runtime="bash",
        name="leak",
        entrypoint="run.sh",
        body='echo "the token is $TOKEN"\n',
        manifest_extra={"requirements": {"secrets": [{"name": "TOKEN"}]}},
    )
    loaded = load_function(fn)
    bus = EnvBus(store=DictSecretStore({"TOKEN": "s3cr3t"}))
    engine = Engine(LocalContainer(tmp_path / "work"), build_registry(), bus, "r", "s")
    events = await collect_events(engine.run_step(loaded, "leak", {}))
    texts = " ".join(e.payload["text"] for e in events if e.kind == "text")
    assert "s3cr3t" not in texts and "••••" in texts
