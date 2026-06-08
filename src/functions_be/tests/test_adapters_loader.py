import pytest

from conftest import FakeContainer, make_context, make_function
from functions_be import (
    ClaudeAdapter,
    FunctionLoadError,
    PythonAdapter,
    UnknownRuntimeError,
    build_registry,
    get_adapter,
    load_function,
    resolve_local_ref,
)
from functions_shared import parse_ref


def test_registry_has_v1_runtimes_and_capabilities():
    reg = build_registry()
    assert set(reg) == {"bash", "python", "claude", "custom"}
    assert reg["claude"].capabilities.is_llm is True
    assert reg["claude"].capabilities.memory == "session"
    assert reg["bash"].capabilities.is_llm is False


def test_get_adapter_unknown_raises():
    with pytest.raises(UnknownRuntimeError):
        get_adapter(build_registry(), "rust")


async def test_python_provision_issues_pip_install(tmp_path):
    c = FakeContainer(tmp_path / "work")
    adapter = PythonAdapter()
    fn = type("F", (), {"dependencies": type("D", (), {"python": ["boto3==1.0"]})()})()
    await adapter.provision(fn, c)
    assert c.calls == [["python3", "-m", "pip", "install", "boto3==1.0"]]


async def test_provision_noop_without_deps(tmp_path):
    c = FakeContainer(tmp_path / "work")
    fn = type("F", (), {"dependencies": type("D", (), {"python": []})()})()
    await PythonAdapter().provision(fn, c)
    assert c.calls == []


def test_claude_build_argv_session_then_resume(tmp_path):
    adapter = ClaudeAdapter()
    first = make_context(tmp_path, FakeContainer(tmp_path / "w"), first_claude=True)
    later = make_context(tmp_path, FakeContainer(tmp_path / "w2"), first_claude=False)
    a1 = adapter.build_argv(first, "hi")
    a2 = adapter.build_argv(later, "hi")
    assert "--session-id" in a1 and "--resume" not in a1
    assert "--resume" in a2 and "--session-id" not in a2
    assert a1[:2] == ["claude", "-p"] and "stream-json" in a1
    assert "--permission-mode" in a1 and "bypassPermissions" in a1


def test_claude_translate_parses_streamjson(tmp_path):
    adapter = ClaudeAdapter()
    ctx = make_context(tmp_path, FakeContainer(tmp_path / "w"))
    assistant = '{"type":"assistant","message":{"content":[{"type":"text","text":"hello"},{"type":"tool_use","name":"Bash"}]}}'
    result = '{"type":"result","result":"done"}'
    events = list(adapter._translate(assistant, ctx)) + list(adapter._translate(result, ctx))
    kinds = [(e.kind, (e.payload or {}).get("text") or (e.payload or {}).get("name")) for e in events]
    assert ("text", "hello") in kinds
    assert ("tool", "Bash") in kinds
    assert ("text", "done") in kinds
    assert list(adapter._translate("not json", ctx)) == []
    assert list(adapter._translate("   ", ctx)) == []


def test_load_function_and_errors(tmp_path):
    d = make_function(
        tmp_path / "fn", runtime="bash", name="greet", entrypoint="run.sh", body="echo hi\n"
    )
    loaded = load_function(d)
    assert loaded.manifest.name == "greet" and loaded.dir == d

    with pytest.raises(FunctionLoadError, match="not a function directory"):
        load_function(tmp_path / "missing")

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FunctionLoadError, match="no function manifest"):
        load_function(empty)


def test_resolve_local_ref(tmp_path):
    rel = resolve_local_ref(parse_ref("./fn"), tmp_path)
    assert rel == (tmp_path / "fn").resolve()
    assert resolve_local_ref(parse_ref("/abs/fn"), tmp_path).as_posix() == "/abs/fn"
    with pytest.raises(FunctionLoadError, match="resolver"):
        resolve_local_ref(parse_ref("ns/name@1"), tmp_path)
