# be_009: Pipeline runner (sequential chain)

**Status:** DONE  · _built 2026-06-08 (functions_be.runner, e2e verified)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 3

## Context

The piece that ties the engine, adapters, I/O, and env together into a runnable
pipeline. Reads a pipeline manifest, resolves its steps to functions, and runs them in
order — the deliverable that makes the M0 thin slice real.

## Goal

`run_pipeline(manifest, container)` that loads each step's function (local), runs it
through the engine + its adapter in sequence, threads I/O and env, and emits a unified
event stream + final result. Mixed runtimes in one chain.

## Approach

**Recommendation:** compose the existing parts — loader (`be_004`) → adapter (`be_005`/
`be_006`) → I/O (`be_007`) → env (`be_008`) — under the engine's sequential loop. Local
function refs only here; remote resolution is additive (`be_010`).

**Reasoning:** Keeps the runner a thin orchestration over tested components; remote
install stays decoupled so the slice ships on local functions.

## Acceptance Criteria

- [ ] Runs a pipeline manifest's steps in order
- [ ] Mixed-runtime chain (bash + python + claude) works end to end
- [ ] I/O wiring + env bus threaded across steps
- [ ] Unified event stream + final result
- [ ] Integration test = the M0 slice (the "delight" demo)

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: be_005, be_006, be_007, be_008
- Blocks: be_011, be_013
