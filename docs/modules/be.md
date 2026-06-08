# Module: be_  (`functions_be`) — Orchestrator

## Purpose

The trusted local daemon. Owns execution, secrets, filesystem, and the Claude control
channel. Runs pipelines as sequential, shared-session chains inside Docker.

## Responsibilities

- **Execution engine** — fixed-root, shared Claude session, stream-json plumbing.
- **Runtime adapters** — `bash`, `python`, `claude` (+ `custom`); dispatch by `runtime`.
- **Function loading & resolution** — local loader; resolver + library cache for
  disk/GitHub/URL; namespacing, search/filter.
- **Data plane** — structured I/O injection & output mapping; mutable environment bus;
  secrets injection (masked).
- **Pipeline runner** — sequential chain from a pipeline manifest.
- **Control plane** — loopback HTTP/WS API + local-token auth; event bus; lifecycle
  (pause / wait manual+condition / streaming END).

## Public interface (consumed by fe_)

- Loopback HTTP + WebSocket API (authenticated by local token): run / pause / resume /
  end; live event stream; function & pipeline listing; install.

## Internal dependencies

- `shared_` (contract/types), `infra_` (base image + container runtime).

## Stories

- `be_001` — Sequential shared-session execution engine
- `be_002` — **DESIGN** — Secret scoping & environment bus
- `be_003` — Function sandbox & permission posture
- `be_004` — Function loader + runtime-adapter registry
- `be_005` — Deterministic adapters: `bash` + `python`
- `be_006` — `claude` adapter (CLI over `docker exec`, session resume)
- `be_007` — Structured I/O injection & output mapping
- `be_008` — Environment bus & secrets injection
- `be_009` — Pipeline runner (sequential chain)
- `be_010` — Reference resolver, namespacing & library cache
- `be_011` — Loopback API + streaming + local-token auth
- `be_012` — **DESIGN** — Eventing / streaming substrate
- `be_013` — Lifecycle: pause/wait + streaming END
