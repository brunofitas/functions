# be_004: Function loader + runtime-adapter registry

**Status:** DONE  · _built 2026-06-08 (functions_be.adapters/loader)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 2

## Context

The engine needs to turn a function directory into something runnable. That means loading
its manifest (via the contract library) and selecting the right runtime adapter by the
declared `runtime`. The registry is what makes runtimes pluggable.

## Goal

A loader that reads a function from a local path (manifest + entrypoint) and a registry
that maps `runtime` → adapter instance, including the `custom` (Makefile) adapter, with a
clear extension point for future runtimes.

## Approach

**Recommendation:** `load_function(path)` → validated model (uses `shared_003`); a
registry keyed by `runtime` string; adapters register via entry points / a decorator so
adding one is a one-file change.

**Reasoning:** Keeps the core closed to modification, open to extension (new adapters).

## Acceptance Criteria

- [ ] `load_function(path)` returns a validated function model
- [ ] Registry resolves `runtime` → adapter, errors clearly on unknown runtime
- [ ] `custom`/Makefile adapter registered
- [ ] Adding a new adapter requires no core changes (documented extension point)

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: shared_003, be_001
- Blocks: be_005, be_006

Cross-module: —
