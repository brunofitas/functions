# infra_005: Ship self-contained (bundle Python + deps)

**Status:** DONE  · _2026-06-08 — PyInstaller freeze verified; electron-builder config wired_
**Mode:** BUILD
**Module:** infra_
**Created:** 2026-06-08
**Layer:** 5

## Context
The desktop app must run with no system Python. Freeze the orchestrator (FastAPI +
uvicorn + our modules + deps) into a standalone binary and bundle it inside the Electron
app, so users just install and launch.

## Goal
A PyInstaller binary `functions-orchestrator` that serves the API/Studio with no system
Python; Electron spawns it in packaged mode; electron-builder bundles it as a resource.

## Approach
PyInstaller `--onedir` with `--collect-all uvicorn/functions_be/functions_shared`;
entry `infra/packaging/orchestrator_entry.py`. electron-builder `extraResources` ships
the binary + `gui/` (index.html + studio.js) + `examples/`. `electron/main.cjs` runs the
frozen binary when `app.isPackaged` (with `--gui-dir`), else the venv in dev.

## Acceptance Criteria
- [x] Frozen binary runs the API self-contained (verified: `/health` ok, `/functions` lists examples — no system Python)
- [x] `--gui-dir` lets the orchestrator serve a relocated GUI (packaged builds)
- [x] electron-builder config bundles the binary + gui + examples as resources
- [x] main.cjs spawns the frozen binary in packaged mode
- [ ] Full packaged .dmg/.exe/.AppImage produced (runs in CI — infra_006)

## Output
- `infra/packaging/orchestrator_entry.py`, `src/functions_fe/electron-builder.yml`
- `functions_be/__main__.py` (`--gui-dir`), `electron/main.cjs` (packaged path)

## Notes
Frozen cold-start ≈ 8s; Electron's health-wait (20s budget) covers it. PyInstaller is
platform-specific → the build runs per-OS in CI.
