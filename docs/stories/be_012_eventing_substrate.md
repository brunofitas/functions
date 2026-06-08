# be_012: Eventing / streaming substrate

**Status:** DONE
**Mode:** DESIGN
**Module:** be_
**Created:** 2026-06-08
**Layer:** 1

> **SEALED 2026-06-08** → `docs/decisions/d_be_002_eventing_substrate.md`. asyncio-native
> (async generators + `anyio` bus + `aiostream` operators); `Event` tagged union;
> pause = run-gate backpressure; END = sentinel poison pill. No RxPY.

## Context

Everything in the orchestrator is a stream: stream-json tokens, the event bus, pause as
backpressure, END as completion, fan-out to console + logs. The substrate choice
(asyncio-native vs. classic RxPY) shapes the engine, API, and lifecycle — a decision
that touches 3+ stories, so it's a Design Gate.

## Goal

A sealed decision on the reactive substrate: the stream/event primitives, how the event
bus does pub/sub + backpressure + fan-out, how pause maps to backpressure and END to
completion, and the operator set the engine/runner rely on.

## Approach

_DESIGN — filled during the Design Gate (`design: be_012`)._

**Leading direction:** asyncio-native — async generators for per-step streams, `anyio`
memory object streams for the event bus (backpressure + fan-out), `aiostream` for
Rx-style operators — avoiding RxPY's impedance mismatch with asyncio. Weigh vs. classic
`reactivex`.

## Acceptance Criteria

- [ ] Stream/event primitives chosen
- [ ] Event-bus pub/sub + backpressure + fan-out approach decided
- [ ] pause→backpressure and END→completion semantics defined
- [ ] Operator/dependency set chosen
- [ ] Sealed decision record in `docs/decisions/d_be_002_eventing_substrate.md`

## Output

- `docs/decisions/d_be_002_eventing_substrate.md` (SEALED)

## Dependencies

Within module:
- Requires: shared_002 (sealed)
- Blocks: be_001, be_011, be_013
