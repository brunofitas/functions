# fe_001: Run console (live streaming)

**Status:** DONE  · _built 2026-06-08 (RunConsole view-model, WS streaming, controls)_
**Mode:** BUILD
**Module:** fe_
**Created:** 2026-06-08
**Layer:** 2

## Context

The first GUI surface and the one with the clearest value: watch a pipeline run live,
per step, with controls. It's the visual successor to the prototype's SSE console.

## Goal

A console view that connects to the orchestrator (loopback + token), shows the pipeline's
steps with live status (running/done/error), streams each step's output, and offers run /
pause / resume / end controls.

## Approach

**Recommendation:** subscribe to the `be_011` WS event stream; render steps as a
node strip + per-step output panes (mirrors the prototype UI); wire controls to the API.

**Reasoning:** Highest-value, lowest-risk GUI surface; reuses proven UX.

## Acceptance Criteria

- [ ] Connects with the local token; rejects on missing token
- [ ] Live per-step status + streamed output
- [ ] Run / pause / resume / end controls work against the API
- [ ] Handles errors and END/drain cleanly

## Output

_Filled after implementation._

## Dependencies

Cross-module:
- Requires: be_011, be_013
