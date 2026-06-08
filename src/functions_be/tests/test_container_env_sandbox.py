from functions_be import DictSecretStore, EnvBus, LocalContainer, load_env_file, mask
from functions_be.container import DockerContainer
from functions_be import sandbox
from functions_shared import FunctionManifest


async def test_local_container_runs_and_streams(tmp_path):
    c = LocalContainer(tmp_path / "work")
    lines = [line async for line in c.exec_stream(["bash", "-c", "echo hi; echo bye"])]
    assert lines == ["hi", "bye"]
    assert c.last_returncode == 0
    assert c.path("x").parent == c.workspace


async def test_local_container_returncode(tmp_path):
    c = LocalContainer(tmp_path / "work")
    _ = [line async for line in c.exec_stream(["bash", "-c", "exit 3"])]
    assert c.last_returncode == 3


def test_docker_argv_builder(tmp_path):
    c = DockerContainer("cid123", host_workspace=tmp_path, workspace="/work")
    argv = c.docker_argv(["bash", "x.sh"], env={"K": "V"})
    assert argv[:4] == ["docker", "exec", "-w", "/work"]
    assert "-e" in argv and "K=V" in argv and "cid123" in argv and argv[-2:] == ["bash", "x.sh"]


def test_docker_container_maps_paths(tmp_path):
    c = DockerContainer("cid", host_workspace=tmp_path, workspace="/work")
    cpath = c.write(".functions/in.json", '{"a":1}')
    assert cpath == "/work/.functions/in.json"  # in-container path
    assert (tmp_path / ".functions" / "in.json").read_text() == '{"a":1}'  # written host-side
    assert c.read(".functions/in.json") == '{"a":1}'
    (tmp_path / "fn").mkdir()
    (tmp_path / "fn" / "run.sh").write_text("echo hi")
    mounted = c.mount_function(tmp_path / "fn")
    assert mounted == "/work/.fn/fn"
    assert (tmp_path / ".fn" / "fn" / "run.sh").exists()


def _fn(**kw):
    return FunctionManifest(namespace="n", name="f", runtime="bash", **kw)


def test_envbus_precedence_and_least_privilege():
    bus = EnvBus(
        global_env={"REGION": "global"},
        store=DictSecretStore({"TOKEN": "s3cr3t", "OTHER": "nope"}),
    )
    bus.bus["REGION"] = "bus"  # global should win over bus
    fn = _fn(
        requirements={
            "environment": [{"name": "REGION", "default": "def"}],
            "secrets": [{"name": "TOKEN"}],
        }
    )
    env = bus.step_env(fn)
    assert env["REGION"] == "global"  # global > bus > default
    assert env["TOKEN"] == "s3cr3t"  # declared secret injected
    assert "OTHER" not in env  # undeclared secret NOT injected (least-privilege)


def test_envbus_exports_promotes_outputs_to_bus():
    bus = EnvBus()
    fn = _fn(exports=["AWS_PROFILE"])
    bus.apply_exports(fn, {"AWS_PROFILE": "prod", "ignored": "x"})
    assert bus.bus == {"AWS_PROFILE": "prod"}


def test_mask_redacts_secret_values():
    assert mask("token=s3cr3t end", ["s3cr3t", ""]) == "token=•••• end"


def test_load_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# comment\nA=1\nB = two \ngarbage\n")
    assert load_env_file(p) == {"A": "1", "B": "two"}


def test_sandbox_posture():
    assert sandbox.claude_permission_args() == ["--permission-mode", "bypassPermissions"]
    assert "/work" in sandbox.trust_summary()
