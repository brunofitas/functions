import pytest

from functions_be.manager import ContainerManager, DockerError, Mounts

MOUNTS = Mounts(workspace="/host/work", lib="/host/lib", cache="/host/cache")


class FakeDocker:
    def __init__(self, exists=False, create_rc=0):
        self.exists = exists
        self.create_rc = create_rc
        self.calls: list[list[str]] = []

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[:3] == ["docker", "ps", "-aq"]:
            return (0, "abc123" if self.exists else "")
        if argv[:2] == ["docker", "run"]:
            return (self.create_rc, "" if self.create_rc == 0 else "boom")
        return (0, "")


def test_argv_builders():
    m = ContainerManager(image="functions-base:1.0")
    create = m.create_argv("r1", MOUNTS)
    assert m.name("r1") == "functions-r1"
    assert "functions-r1" in create
    assert "/host/work:/work" in create
    assert "/host/lib:/srv/functions" in create  # NOT /lib (would shadow system libs)
    assert "/host/cache:/cache" in create
    assert create[-3:] == ["functions-base:1.0", "sleep", "infinity"]
    assert m.rm_argv("r1") == ["docker", "rm", "-f", "functions-r1"]


def test_argv_with_entrypoint_and_env():
    m = ContainerManager(image="claude-docker:latest", entrypoint="sleep", env={"TOK": "x"})
    create = m.create_argv("r2", MOUNTS)
    assert "--entrypoint" in create and "sleep" in create
    assert "-e" in create and "TOK=x" in create
    assert create[-2:] == ["claude-docker:latest", "infinity"]  # entrypoint sleep + arg infinity


def test_ensure_ready_creates_when_missing():
    fake = FakeDocker(exists=False)
    m = ContainerManager(runner=fake)
    container = m.ensure_ready("r1", MOUNTS)
    assert container.workspace.as_posix() == "/work"
    assert any(c[:2] == ["docker", "run"] for c in fake.calls)


def test_ensure_ready_reuses_when_present():
    fake = FakeDocker(exists=True)
    m = ContainerManager(runner=fake)
    m.ensure_ready("r1", MOUNTS)
    assert not any(c[:2] == ["docker", "run"] for c in fake.calls)  # reused, not recreated


def test_ensure_ready_raises_on_create_failure():
    m = ContainerManager(runner=FakeDocker(exists=False, create_rc=1))
    with pytest.raises(DockerError, match="failed to create"):
        m.ensure_ready("r1", MOUNTS)


def test_teardown_removes():
    fake = FakeDocker(exists=True)
    ContainerManager(runner=fake).teardown("r1")
    assert fake.calls[-1] == ["docker", "rm", "-f", "functions-r1"]
