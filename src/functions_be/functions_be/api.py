"""Loopback HTTP + WebSocket API (be_011).

Bound to loopback; authenticated by a local bearer token. `POST /run` registers a run;
the WebSocket `/events/{run_id}` executes it and streams Events live. Running inside the
WS handler keeps execution on the connection's own event loop (robust under uvicorn and
tests). The container is a host LocalContainer for now (warm-container mgr is infra_002).
"""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket
from pydantic import BaseModel

from functions_shared import PipelineManifest

from . import auth
from .container import LocalContainer
from .control import RunControl
from .events import Event
from .resolver import LibraryIndex
from .runner import run_pipeline


class RunRequest(BaseModel):
    pipeline: dict
    base_dir: Optional[str] = None


class _Run:
    def __init__(self, run_id: str, pipeline: PipelineManifest, base_dir: str):
        self.run_id = run_id
        self.pipeline = pipeline
        self.base_dir = base_dir
        self.status = "pending"
        self.control = RunControl()


class RunManager:
    def __init__(self, base_dir: str | Path = ".", container_manager: Optional[object] = None):
        self.base_dir = str(base_dir)
        self.runs: dict[str, _Run] = {}
        self.container_manager = container_manager  # ContainerManager → run in Docker
        # one shared dependency cache reused across runs (per d_infra_001)
        self._cache_dir = tempfile.mkdtemp(prefix="fn-cache-") if container_manager else None

    def start(self, pipeline: PipelineManifest, base_dir: Optional[str] = None) -> _Run:
        run = _Run(uuid.uuid4().hex[:8], pipeline, base_dir or self.base_dir)
        self.runs[run.run_id] = run
        return run

    async def stream(self, run_id: str) -> AsyncIterator[Event]:
        run = self.runs[run_id]
        run.status = "running"
        workspace = Path(tempfile.mkdtemp(prefix=f"fn-{run_id}-"))
        docker = self.container_manager is not None
        if docker:
            from .manager import Mounts

            mounts = Mounts(workspace=str(workspace), lib=run.base_dir, cache=self._cache_dir)
            container = self.container_manager.ensure_ready(run_id, mounts)
        else:
            container = LocalContainer(workspace)
        try:
            async for event in run_pipeline(
                run.pipeline,
                base_dir=run.base_dir,
                container=container,
                run_id=run_id,
                control=run.control,
            ):
                yield event
            run.status = "ended" if run.control.cancelled else "done"
        except Exception as exc:  # noqa: BLE001 — surface as an error event
            run.status = "error"
            yield Event("error", run_id, payload={"message": str(exc)})
        finally:
            # fresh-per-run: always tear the container down + clean the run workspace
            if docker:
                self.container_manager.teardown(run_id)
            shutil.rmtree(workspace, ignore_errors=True)


def _serialize(event: Event) -> dict:
    return {
        "kind": event.kind,
        "run_id": event.run_id,
        "step_id": event.step_id,
        "seq": event.seq,
        "payload": event.payload,
    }


def create_app(
    *,
    token: str,
    index: Optional[LibraryIndex] = None,
    manager: Optional[RunManager] = None,
    base_dir: str = ".",
) -> FastAPI:
    app = FastAPI(title="functions")
    index = index or LibraryIndex()
    manager = manager or RunManager(base_dir)

    async def require_token(
        authorization: str = Header(None), x_functions_token: str = Header(None)
    ) -> None:
        provided = x_functions_token
        if not provided and authorization and authorization.lower().startswith("bearer "):
            provided = authorization.split(" ", 1)[1]
        if not auth.verify(provided, token):
            raise HTTPException(status_code=401, detail="invalid or missing token")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/functions")
    async def functions(_: None = Depends(require_token)):
        return {
            "functions": [
                {"ref_id": e.ref_id, "runtime": e.runtime, "dir": str(e.dir)}
                for e in index.search()
            ]
        }

    @app.post("/run")
    async def start_run(body: RunRequest, _: None = Depends(require_token)):
        pipeline = PipelineManifest.model_validate(body.pipeline)
        run = manager.start(pipeline, body.base_dir)
        return {"run_id": run.run_id}

    def _run_or_404(run_id: str) -> _Run:
        run = manager.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="unknown run")
        return run

    @app.post("/runs/{run_id}/pause")
    async def pause_run(run_id: str, _: None = Depends(require_token)):
        _run_or_404(run_id).control.pause()
        return {"status": "paused"}

    @app.post("/runs/{run_id}/resume")
    async def resume_run(run_id: str, _: None = Depends(require_token)):
        _run_or_404(run_id).control.resume()
        return {"status": "running"}

    @app.post("/runs/{run_id}/end")
    async def end_run(run_id: str, _: None = Depends(require_token)):
        _run_or_404(run_id).control.cancel()
        return {"status": "ending"}

    @app.websocket("/events/{run_id}")
    async def events(ws: WebSocket, run_id: str):
        if not auth.verify(ws.query_params.get("token"), token):
            await ws.close(code=4401)
            return
        if run_id not in manager.runs:
            await ws.close(code=4404)
            return
        await ws.accept()
        async for event in manager.stream(run_id):
            await ws.send_json(_serialize(event))
        await ws.close()

    app.state.token = token
    app.state.manager = manager
    app.state.index = index
    return app
