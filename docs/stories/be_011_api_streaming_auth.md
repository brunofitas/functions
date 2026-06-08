# be_011: Loopback API + streaming + local-token auth

**Status:** DONE  · _built 2026-06-08 (FastAPI loopback + WS stream + token, tested)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 4

## Context

The GUI needs a way to drive the orchestrator and watch runs live. For a local OSS tool
this is a loopback-only HTTP/WS API authenticated with a locally-generated token — the
Jupyter pattern — not an enterprise auth system.

## Goal

An HTTP + WebSocket API, bound to loopback, authenticated by a local token (a pre-shared
secret signs a short-lived token; the secret never goes on the wire), exposing: run /
pause / resume / end a pipeline, list functions/pipelines, install, and a live event
stream of run output.

## Approach

**Recommendation:** FastAPI + WebSocket; token generated on first run, stored
`chmod 600`, read by the local GUI; events bridged from the engine's stream
(`be_012` substrate).

**Reasoning:** Reuses the prototype's FastAPI/SSE foundation; loopback + token is the
standard, sufficient local posture.

## Acceptance Criteria

- [ ] HTTP + WS API bound to loopback only
- [ ] Local-token auth; secret never transmitted; token rejected if absent/invalid
- [ ] Endpoints: run/pause/resume/end, list, install
- [ ] Live event stream of run output over WS
- [ ] Test: unauthenticated request rejected; authenticated run streams

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: be_009, be_012 (sealed)
- Blocks: be_013

Cross-module:
- Blocks: fe_001, fe_002, fe_004, fe_005
