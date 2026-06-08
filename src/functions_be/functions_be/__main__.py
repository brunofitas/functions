"""`python -m functions_be` — launch the orchestrator (and optionally the Studio GUI)."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .manager import ContainerManager
from .server import serve


def _claude_oauth_token() -> str | None:  # pragma: no cover — reads the OS keychain
    import os

    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
            capture_output=True,
            text=True,
        ).stdout
        return json.loads(out)["claudeAiOauth"]["accessToken"]
    except Exception:
        return None


def main() -> None:  # pragma: no cover — CLI entrypoint
    p = argparse.ArgumentParser(prog="functions_be", description="Run the functions orchestrator.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8799)
    p.add_argument("--base-dir", default=".", help="where function refs resolve from")
    p.add_argument("--gui", action="store_true", help="also serve the Studio GUI at /")
    p.add_argument("--gui-dir", default=None, help="GUI dir (index.html + dist/studio.js); for packaged builds")
    p.add_argument("--docker", action="store_true", help="run pipelines inside Docker containers")
    p.add_argument("--image", default="python:3.12-slim", help="base image for --docker runs")
    p.add_argument("--claude", action="store_true", help="use claude-docker image + inject token")
    args = p.parse_args()

    gui_dir = None
    if args.gui:
        # explicit --gui-dir (packaged) wins; else the in-repo dev path
        gui_dir = args.gui_dir or str(Path(__file__).resolve().parents[2] / "functions_fe")

    container_manager = None
    if args.docker or args.claude:
        if args.claude:
            token = _claude_oauth_token()
            container_manager = ContainerManager(
                image="claude-docker:latest",
                entrypoint="sleep",
                env={"CLAUDE_CODE_OAUTH_TOKEN": token} if token else {},
            )
        else:
            container_manager = ContainerManager(image=args.image)

    serve(args.host, args.port, args.base_dir, gui_dir, container_manager)


if __name__ == "__main__":
    main()
