# infra_004: Electron desktop shell

**Status:** DONE  · _built 2026-06-08 (electron/main.cjs spawns orchestrator, native window verified)_
**Mode:** BUILD
**Module:** infra_
**Created:** 2026-06-08
**Layer:** 5

## Context

The vision is a desktop app. So far the Studio runs in a browser against the
orchestrator. This wraps it in a native Electron window: the main process launches the
orchestrator as a child, waits for health, and loads the served Studio — one
double-clickable app instead of "run a server, open a browser".

## Goal

`npm run app` (in functions_fe) launches an Electron window titled "functions — Studio"
that: spawns `python -m functions_be --gui` (venv python, base-dir examples), waits for
`/health`, loads `http://127.0.0.1:8799`, and kills the orchestrator on quit.

## Approach

**Recommendation:** thin Electron main (`electron/main.cjs`, CommonJS) that wraps the
already-working served app (token injected server-side) — no renderer rewrite. Native
packaging (.dmg/.exe) is a later story (`infra_006`).

## Acceptance Criteria

- [ ] `npm run app` opens a native window running the Studio
- [ ] Orchestrator spawned as a child and terminated on window-close / quit
- [ ] Window waits for orchestrator health before loading (no white flash on a dead port)
- [ ] No impact on the test/coverage gate (main process is JS glue, outside src/)

## Output

- `src/functions_fe/electron/main.cjs`
- `package.json` (electron devDep, `main`, `npm run app`)

## Dependencies

Cross-module:
- Requires: be_011 (served GUI), fe_001/fe_002 (rendered surfaces)
