# be_001: Sequential shared-session execution engine

**Status:** DONE  · _built 2026-06-08 (functions_be.engine), 98% cov_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 1

## Context

The heart of the orchestrator and the thing the prototype proved: run steps from one
fixed root so a Claude session created for step A resumes for step B. This story builds
the reusable engine skeleton the adapters, I/O, and runner plug into.

## Goal

An engine that, given an ordered list of steps and a container handle, runs them
sequentially from a fixed root, maintains one shared Claude session id across LLM steps
(`--session-id` then `--resume`), exposes each step's output as an event stream, and
surfaces per-step status (start / output / done / error). Mixed-runtime aware (delegates
execution to adapters).

## Approach

**Recommendation:** asyncio core (per the sealed `be_012` substrate); the engine owns the
session id, the fixed root, and the step loop, and calls `adapter.execute()` for each
step. Container interaction via basic `docker exec` in M0 (hardened later by `infra_002`).

**Reasoning:** Mirrors the proven prototype, generalized behind the adapter interface.

## Acceptance Criteria

- [ ] Runs an ordered step list from one fixed root
- [ ] One shared Claude session resumed across LLM steps
- [ ] Per-step events: start / output(stream) / done / error
- [ ] Delegates execution to the runtime adapter for each step
- [ ] Unit/integration test: a 3-step mixed-runtime chain shares memory across LLM steps

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: be_012 (sealed), shared_003
- Blocks: be_004, be_007, be_008, be_009

Cross-module:
- Requires: infra_001 (sealed) — container/control-channel decision; shared_003
