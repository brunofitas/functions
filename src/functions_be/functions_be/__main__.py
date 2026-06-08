"""`python -m functions_be` — launch the orchestrator (and optionally the Studio GUI)."""

from __future__ import annotations

import argparse
from pathlib import Path

from .server import serve


def main() -> None:  # pragma: no cover — CLI entrypoint
    p = argparse.ArgumentParser(prog="functions_be", description="Run the functions orchestrator.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8799)
    p.add_argument("--base-dir", default=".", help="where function refs resolve from")
    p.add_argument("--gui", action="store_true", help="also serve the Studio GUI at /")
    args = p.parse_args()
    # src/functions_be/functions_be/__main__.py → parents[2] == src/
    gui_dir = str(Path(__file__).resolve().parents[2] / "functions_fe") if args.gui else None
    serve(args.host, args.port, args.base_dir, gui_dir)


if __name__ == "__main__":
    main()
