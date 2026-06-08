import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from conftest import make_function
from functions_be import auth, create_app
from functions_be.api import RunManager
from functions_be.resolver import LibraryIndex

TOKEN = "test-token-123"


def test_ensure_token_create_and_reuse(tmp_path):
    p = tmp_path / "token"
    tok = auth.ensure_token(p)
    assert tok and auth.ensure_token(p) == tok  # reused, not regenerated
    assert auth.verify(tok, tok) and not auth.verify("wrong", tok) and not auth.verify(None, tok)


def test_health_is_open():
    client = TestClient(create_app(token=TOKEN))
    assert client.get("/health").json() == {"status": "ok"}


def test_functions_requires_token(tmp_path):
    cache = tmp_path / "cache"
    (cache / "aws" / "login@0.1.0").mkdir(parents=True)
    (cache / "aws" / "login@0.1.0" / "function.yaml").write_text(
        "kind: function\nnamespace: aws\nname: login\nversion: 0.1.0\nruntime: claude\n"
    )
    app = create_app(token=TOKEN, index=LibraryIndex(cache))
    client = TestClient(app)
    assert client.get("/functions").status_code == 401
    resp = client.get("/functions", headers={"Authorization": f"Bearer {TOKEN}"})
    assert resp.status_code == 200
    assert resp.json()["functions"][0]["ref_id"] == "aws/login@0.1.0"


def _greet_pipeline(tmp_path):
    greet = make_function(
        tmp_path / "greet",
        runtime="bash",
        name="greet",
        entrypoint="run.sh",
        body='echo "hi $INPUT_NAME"\nprintf \'{"greeting":"hi %s"}\' "$INPUT_NAME" > "$FN_OUTPUTS"\n',
        manifest_extra={
            "outputs": [{"name": "greeting", "type": "string"}],
            "requirements": {"inputs": [{"name": "name", "type": "string"}]},
        },
    )
    return {
        "namespace": "demo",
        "name": "p",
        "steps": [{"id": "greet", "use": str(greet), "with": {"name": "ada"}}],
    }


def test_run_streams_events_over_websocket(tmp_path):
    app = create_app(token=TOKEN, manager=RunManager(str(tmp_path)))
    client = TestClient(app)
    pipeline = _greet_pipeline(tmp_path)

    resp = client.post(
        "/run",
        json={"pipeline": pipeline, "base_dir": str(tmp_path)},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    received = []
    with client.websocket_connect(f"/events/{run_id}?token={TOKEN}") as ws:
        try:
            while True:
                msg = ws.receive_json()
                received.append(msg)
                if msg["kind"] == "run_end":
                    break
        except WebSocketDisconnect:
            pass

    kinds = [m["kind"] for m in received]
    assert "run_start" in kinds and "run_end" in kinds
    step_end = next(m for m in received if m["kind"] == "step_end" and m["step_id"] == "greet")
    assert step_end["payload"]["outputs"] == {"greeting": "hi ada"}


def test_run_requires_token(tmp_path):
    client = TestClient(create_app(token=TOKEN, manager=RunManager(str(tmp_path))))
    assert client.post("/run", json={"pipeline": _greet_pipeline(tmp_path)}).status_code == 401


def test_websocket_rejects_bad_token(tmp_path):
    client = TestClient(create_app(token=TOKEN, manager=RunManager(str(tmp_path))))
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/events/whatever?token=bad") as ws:
            ws.receive_json()


def test_end_unknown_run_is_404(tmp_path):
    client = TestClient(create_app(token=TOKEN, manager=RunManager(str(tmp_path))))
    resp = client.post("/runs/nope/end", headers={"Authorization": f"Bearer {TOKEN}"})
    assert resp.status_code == 404


async def test_docker_run_tears_down_container(tmp_path):
    """Docker-backed runs must NOT leak containers — teardown after every run."""
    from conftest import FakeContainer
    from functions_shared import PipelineManifest

    class FakeManager:
        def __init__(self):
            self.created = []
            self.torn = []

        def ensure_ready(self, run_id, mounts):
            self.created.append(run_id)
            return FakeContainer(tmp_path / f"ws-{run_id}")

        def teardown(self, run_id):
            self.torn.append(run_id)

    mgr = FakeManager()
    rm = RunManager(base_dir=str(tmp_path), container_manager=mgr)
    run = rm.start(PipelineManifest.model_validate({"namespace": "n", "name": "p", "steps": []}))
    events = [e async for e in rm.stream(run.run_id)]

    assert mgr.created == [run.run_id]
    assert mgr.torn == [run.run_id]  # container torn down (no leak)
    assert any(e.kind == "run_end" for e in events)
