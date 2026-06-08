# Module: fe_  (`functions_fe`) — Studio (GUI)

## Purpose

The desktop front end. Presents pipelines, functions, runs, and settings. **Holds no
secrets** — it talks to the orchestrator over the loopback API with a local token.

## Responsibilities

- **Run console** — live per-step streaming, status, run/pause/end controls.
- **Function & pipeline browser** — searchable/filterable list of local + installable
  functions.
- **Pipeline editor** — drag-and-drop wiring of functions; map outputs→inputs.
- **Function creator/editor** — scaffold a function, edit manifest/entrypoint, run
  `make test`.
- **Settings** — global environment, secrets, and folders/workspaces.

## Public interface

- The desktop app itself (packaged by `infra_`). Consumes the `be_` API only.

## Internal dependencies

- `be_` (API), `shared_` (types for editor validation).

## Stories

- `fe_001` — Run console (live streaming)
- `fe_002` — Function & pipeline browser
- `fe_003` — Drag-and-drop pipeline editor
- `fe_004` — Function creator/editor + `make test` runner
- `fe_005` — Settings (env / secrets / folders)
