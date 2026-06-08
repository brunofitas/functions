# Module: shared_  (`functions_shared`)

## Purpose

The contract spine. Defines what a function/pipeline *is* so the orchestrator and GUI
agree without coupling. Has **zero internal dependencies**.

## Responsibilities

- Function & pipeline **manifest schema** (incl. `runtime`, dependencies, namespace,
  version).
- The **inputs / outputs / events** contract and how they serialize across steps.
- The **runtime-adapter interface** (`provision` / `execute` / `collect` + capabilities
  `is_llm`, memory model, entrypoint, dependency kinds).
- Shared types and the function authoring scaffold.

## Public interface (consumed by be_ and fe_)

- Manifest parse/validate API; typed models; reference-string grammar
  (`namespace/name@version`, `./path`, `github:…`, `https://…`).

## Internal dependencies

None.

## Stories

- `shared_001` — Project scaffold (monorepo, packaging, CI bootstrap)
- `shared_002` — **DESIGN** — Function/pipeline contract + runtime-adapter interface
- `shared_003` — Contract library (schema / parser / validation)
