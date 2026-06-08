# be_007: Structured I/O injection & output mapping

**Status:** DONE  · _built 2026-06-08 (engine I/O + wiring)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 2

## Context

Steps pass structured data, not just shared memory. A step reads its declared `inputs`
and writes `outputs`; the orchestrator maps one step's outputs to the next step's inputs
per the pipeline's `with:` wiring. This is the data plane that complements the shared
session.

## Goal

Injection of resolved inputs into a step (as `$PIPELINE_INPUTS` / env per the contract),
collection of `$PIPELINE_OUTPUTS`, validation against the manifest, and mapping into the
next step's inputs via the pipeline wiring expressions.

## Approach

**Recommendation:** the engine resolves `${{ steps.X.outputs.Y }}` wiring (from
`shared_003`), writes inputs before a step, reads + validates outputs after, and stores
them for downstream resolution.

**Reasoning:** Keeps adapters dumb — they just read/write known files; the engine does
the wiring.

## Acceptance Criteria

- [ ] Inputs injected per contract before each step
- [ ] Outputs collected + validated after each step
- [ ] `with:` wiring expressions resolve outputs → next inputs
- [ ] Missing/invalid outputs handled per the sealed policy
- [ ] Test: output of step A flows into input of step B

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: shared_003, be_001
- Blocks: be_009
