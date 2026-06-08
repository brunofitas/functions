# d_be_002: Eventing / streaming substrate

**Status:** SEALED
**Date:** 2026-06-08
**Story:** be_012
**Scope:** be_ (consumed by engine, runner, API, lifecycle)

## Context

Everything in the orchestrator is a stream: `stream-json` tokens from Claude, per-step
output, the event bus, pause (backpressure), END (completion), and fan-out to the
console + logs + API. The substrate choice shapes the engine (`be_001`), API (`be_011`),
and lifecycle (`be_013`). Classic RxPY (`reactivex`) is push-based and predates
async/await, creating an impedance mismatch with the asyncio world everything else lives
in (subprocess streams, WebSockets, `docker exec`).

## Decision

**asyncio-native.** No RxPY.

- **Per-step output** = an **async generator** (`AsyncIterator[Event]`) — exactly the
  prototype's proven `async for` over `claude … --output-format stream-json`.
- **Event bus** = **`anyio` memory object streams** (`create_memory_object_stream`):
  bounded buffers give **backpressure** for free; cloning the receiver gives **fan-out**
  (multicast) to console / logs / API subscribers.
- **Operators** (when needed: `merge`, `map`, `filter`, `combine`) = **`aiostream`**,
  which provides Rx-style operators *over* async generators — the expressiveness of Rx
  without leaving asyncio.

### The `Event` type (the wire shape across the whole system)

```python
@dataclass(frozen=True)
class Event:
    kind: Literal[
        "run_start", "step_start", "text", "tool",
        "status", "error", "step_end", "run_end", "end",
    ]
    run_id: str
    step_id: str | None = None      # None for run-level events
    seq: int = 0                     # monotonic per run (ordering / resume)
    payload: dict | None = None      # text chunk, tool name, status, error, outputs…
    ts: str | None = None            # ISO-8601, stamped by the emitter
```

Mapping to reactive semantics: `text`/`tool`/`status` ≙ **onNext**; `error` ≙
**onError** (terminates the step's stream); `end` ≙ **onCompleted** (poison pill, see
below). `seq` makes streams ordered and replayable.

### Backpressure / pause

- Streams are **bounded** (default buffer, larger for high-volume token streams).
- **Pause** = an `anyio.Event` "run gate" the engine awaits at step boundaries; while
  closed, the producer naturally blocks on the bounded bus → genuine backpressure, not a
  busy-loop. Resume opens the gate.

### END propagation (graceful shutdown)

- `end` is a sentinel `Event` published downstream. Functions that `listens: [end]`
  receive it, drain, and stop; the bus closes its send side afterward, so subscribers see
  clean completion. No abrupt kills.

### Delivery

- In-process, single-consumer-per-logical-stream with multicast fan-out → **at-least-once
  is not a concern in v1** (single process, ordered by `seq`). Exactly-once semantics for
  re-triggered *streaming* pipelines are deferred to `be_013`/streaming work.

## Options considered

- **asyncio-native (chosen)** — async generators + anyio + aiostream. Native to the
  runtime; minimal deps; proven in the prototype.
- **RxPY / `reactivex`** — rich operator catalogue, but push-based/async impedance
  mismatch; bridging cost on every subprocess/WS boundary. Rejected.
- **A broker (Redis/NATS)** — overkill for a single-process local tool. Rejected.

## Consequences

- `be_001` engine yields `AsyncIterator[Event]`; the runner merges step streams via
  `aiostream`; `be_011` bridges the bus to a WebSocket; `be_013` implements pause via the
  run gate and END via the sentinel.
- Dependencies added to `functions_be`: `anyio`, `aiostream`.
- The `Event` schema is the single contract for all streaming surfaces (CLI, API, GUI).

## Affected stories

Constrains/unblocks toward: `be_001`, `be_011`, `be_013`.
