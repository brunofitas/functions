"""PyInstaller entry — frozen, self-contained orchestrator binary (infra_005).

Built into `functions-orchestrator` so the shipped app needs no system Python.
"""
from functions_be.__main__ import main

if __name__ == "__main__":
    main()
