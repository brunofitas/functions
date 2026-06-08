# functions_be

The orchestrator — the trusted local daemon. Owns the execution engine (fixed-root,
shared Claude session), the runtime adapters, function resolution + library cache,
env/secrets injection, the event bus, lifecycle (pause/wait/END), and the loopback API.

Depends on `functions_shared` and the `infra_` container runtime. See `docs/modules/be.md`.
