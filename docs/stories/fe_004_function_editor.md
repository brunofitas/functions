# fe_004: Function creator/editor + make test runner

**Status:** DONE  · _built 2026-06-08 (FunctionCreator: per-runtime scaffold + test cmd)_
**Mode:** BUILD
**Module:** fe_
**Created:** 2026-06-08
**Layer:** 4

## Context

To grow the library, users need to author functions, not just consume them. A guided
creator/editor lowers the barrier and enforces the standard structure.

## Goal

A creator that scaffolds a new function (manifest with `runtime`, entrypoint, README,
i18n) from a template, an editor for its manifest/entrypoint with contract validation,
and a button to run the function's test (`make test` / per-runtime) and show results.

## Approach

**Recommendation:** templates per runtime (bash/python/claude/custom); validate manifest
against `shared_003`; run tests via the orchestrator and stream results into the console.

**Reasoning:** Reuses the contract lib + run console; authoring stays consistent with the
runtime model.

## Acceptance Criteria

- [ ] Scaffold a new function per runtime template
- [ ] Edit manifest + entrypoint with live contract validation
- [ ] Run the function's test and display results
- [ ] Saved function is immediately listable/runnable

## Output

_Filled after implementation._

## Dependencies

Cross-module:
- Requires: shared_003, be_011
