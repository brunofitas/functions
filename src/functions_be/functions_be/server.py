"""App launcher — orchestrator API + (optionally) the Studio GUI, on loopback.

`python -m functions_be --base-dir examples --gui` runs the whole local app: the API
plus the bundled Studio served at /, with the local token injected into the page.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from . import auth
from .api import RunManager, create_app
from .resolver import LibraryIndex


def build_app(
    base_dir: str = ".", gui_dir: Optional[str] = None, token: Optional[str] = None
) -> tuple[FastAPI, str]:
    token = token or auth.ensure_token()
    app = create_app(
        token=token,
        index=LibraryIndex(base_dir),
        manager=RunManager(base_dir),
        base_dir=base_dir,
    )
    if gui_dir:
        gui = Path(gui_dir)

        @app.get("/", response_class=HTMLResponse)
        async def index() -> str:
            return (gui / "index.html").read_text().replace("__TOKEN__", token)

        @app.get("/studio.js")
        async def studio_js() -> FileResponse:
            return FileResponse(gui / "dist" / "studio.js", media_type="application/javascript")

    return app, token


def serve(
    host: str = "127.0.0.1", port: int = 8799, base_dir: str = ".", gui_dir: Optional[str] = None
) -> None:  # pragma: no cover — runs the server
    import uvicorn

    app, token = build_app(base_dir, gui_dir)
    where = "Studio" if gui_dir else "API"
    print(f"functions {where} → http://{host}:{port}   (token {token[:8]}…)")
    uvicorn.run(app, host=host, port=port, log_level="warning")
