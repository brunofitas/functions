import pytest
from pydantic import ValidationError

from functions_shared import FunctionManifest, PipelineManifest, Step
from functions_shared.models import Capabilities


def test_function_manifest_defaults_and_ref_id():
    fn = FunctionManifest(namespace="aws", name="login", version="0.1.0", runtime="claude")
    assert fn.kind == "function"
    assert fn.api_version == "functions/v1"
    assert fn.ref_id == "aws/login@0.1.0"
    assert fn.dependencies.system == []
    assert fn.requirements.inputs == []


def test_function_manifest_accepts_apiversion_alias():
    fn = FunctionManifest.model_validate(
        {"apiVersion": "functions/v1", "namespace": "x", "name": "y", "runtime": "bash"}
    )
    assert fn.api_version == "functions/v1"


@pytest.mark.parametrize(
    "runtime,expected",
    [("bash", "run.sh"), ("python", "main.py"), ("claude", "prompt.md"), ("custom", "Makefile")],
)
def test_resolved_entrypoint_defaults(runtime, expected):
    fn = FunctionManifest(namespace="n", name="f", runtime=runtime)
    assert fn.resolved_entrypoint() == expected


def test_resolved_entrypoint_explicit_and_unknown_runtime():
    assert FunctionManifest(namespace="n", name="f", runtime="bash", entrypoint="go.sh").resolved_entrypoint() == "go.sh"
    assert FunctionManifest(namespace="n", name="f", runtime="rust").resolved_entrypoint() == "run.sh"


def test_function_manifest_requires_runtime():
    with pytest.raises(ValidationError):
        FunctionManifest(namespace="n", name="f")


def test_step_with_alias():
    s = Step.model_validate({"id": "a", "use": "ns/f@1", "with": {"k": "v"}})
    assert s.with_ == {"k": "v"}


def test_pipeline_manifest_and_flow_defaults():
    p = PipelineManifest(
        namespace="acme",
        name="deploy",
        version="1.0.0",
        steps=[{"id": "login", "use": "aws/login@0.1.0"}],
    )
    assert p.kind == "pipeline"
    assert p.flow.mode == "standalone"
    assert p.flow.end.signal == "END"
    assert p.ref_id == "acme/deploy@1.0.0"
    assert p.steps[0].id == "login"


def test_capabilities():
    c = Capabilities(is_llm=True, memory="session", default_entrypoint="prompt.md")
    assert c.is_llm and c.memory == "session"
