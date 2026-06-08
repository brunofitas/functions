# Architecture — functions

> System overview for `brunofitas/functions`. Derived from `docs/intake.md` and
> `docs/VISION.md`. Module boundaries and cross-module interfaces are defined here;
> the four open decisions are sealed in `docs/decisions/` via Design Gates before the
> stories that depend on them are built.

## 1. System overview

**functions** is an open-source, local desktop app that runs **pipelines** — ordered
chains of **functions** — on Docker. A function is a self-contained unit of work with a
pluggable **runtime** (`bash`, `python`, `claude`, … `custom`). A pipeline is itself a
function, so composition is recursive.

```
┌─ host ───────────────────────────────────────────────────────────┐
│  fe_ Studio (GUI)  ──loopback HTTP/WS + local token──▶ be_ Orchestrator
│                                                            │       │
│                                                  drives    │ docker│
│                                                  Claude    ▼ exec  │
│   OS keychain ─OAuth(plan)─▶                ┌─ container (per pipeline) ─┐
│                                             │  /lib   (functions)  vol   │
│   shared_ contract  ◀── used by be_ & fe_   │  /work  (workspace)  vol   │
│   infra_ base image + lifecycle ───────────▶│  ~/.claude (sessions) vol  │
│                                             │  runtime adapters run steps│
│                                             └────────────────────────────┘
└────────────────────────────────────────────────────────────────────┘
```

**Data flow per step:** the orchestrator selects the runtime adapter for the step,
provisions its declared (pinned) deps into the warm container, injects inputs + env +
secrets, executes the entrypoint (`run.sh` / `main.py` / Claude session), streams
output, and collects declared outputs — mapping them to the next step's inputs. Memory
threads only through LLM runtimes (Claude via session `--resume`).

## 2. Modules

| Module | Prefix | Package | Responsibility |
|--------|--------|---------|----------------|
| Shared contracts | `shared_` | `functions_shared` | Manifest schema, I/O + events contract, runtime-adapter interface, shared types. The spine both other modules build on. |
| Orchestrator | `be_` | `functions_be` | Execution engine (fixed root, shared session), runtime adapters, function loader + resolver/library, env/secrets/I/O, event bus, lifecycle (pause/wait/END), loopback API + local-token auth. |
| Studio (GUI) | `fe_` | `functions_fe` | Run console, function/pipeline browser, drag-and-drop editor, creator/editor, settings. Holds no secrets. |
| Runtime / packaging | `infra_` | — | Base Docker image (on `claude-docker`) + container lifecycle manager; cross-platform installers via GitHub Releases / Actions. |

### Cross-module dependency direction

```
shared_  ◀── be_  ◀── fe_
   ▲         ▲
   └──── infra_ (base image + container runtime used by be_)
```

`shared_` depends on nothing internal. `be_` depends on `shared_` + `infra_`. `fe_`
depends on `be_`'s API + `shared_`'s types. No cycles.

## 3. Execution model (sealed direction: sequential, shared-session)

- One pipeline run → one long-lived **container** (per pipeline / run), addressed by ID;
  recreate-on-missing.
- All steps run from **one fixed root** inside the container (the proven per-directory
  session constraint); each function reached via `--add-dir`.
- Steps run **sequentially**; LLM steps share one Claude session (`--session-id` then
  `--resume`). Fan-out/fan-in DAGs are deferred.
- Outputs of step N map to inputs of step N+1 per the pipeline manifest's `with:` wiring.

## 4. Runtime adapters

Each `runtime` is an adapter implementing one interface:

```
provision(function) -> install declared deps into the container (idempotent, cached)
execute(step, inputs, env) -> stream events  (onNext / onError / onComplete=END)
collect() -> validated outputs (per manifest)
capabilities: { is_llm, memory: none|session|history, entrypoint, dep_kinds }
```

v1 adapters: `bash` (run.sh), `python` (main.py), `claude` (CLI over `docker exec`,
session resume). `custom` = the `Makefile` escape hatch. New runtimes (`openai`, Node)
are added as adapters with no core changes.

## 5. Container runtime (decision: `infra_001`)

Long-lived reusable container off a shared base; runtime dependency provisioning from
pinned manifest deps; dep-cache volume; optional `docker commit` snapshot for fast
restart. The engine uses basic `docker exec` in M0; `infra_002` hardens it (warm-up,
ready protocol, reuse, cache, snapshot).

## 6. Layering & milestones

- **Layer 0** — project scaffold.
- **Layer 1** — foundations + the 4 Design Gates (contract, secrets, eventing, container).
- **Layer 2** — contract library, engine, adapters, I/O, env/secrets.
- **Layer 3** — pipeline runner, resolver/library.
- **Layer 4** — API + streaming + auth, lifecycle, GUI, container hardening.
- **Layer 5** — cross-platform installers.

**M0 thin vertical slice** (no GUI): scaffold → seal contract → contract lib → engine →
adapters (bash/python/claude) → I/O + env/secrets → pipeline runner, running a linear
mixed-runtime pipeline in Docker, CLI-driven. The "does this delight me?" milestone.

## 7. Design Gates (sealed before dependents build)

| Decision | Story | Blocks |
|----------|-------|--------|
| Function/pipeline contract + adapter interface | `shared_002` | contract lib, secrets, eventing, container, engine |
| Secret scoping & environment bus | `be_002` | env/secrets injection, settings |
| Eventing / streaming substrate (asyncio leading) | `be_012` | engine, API, lifecycle |
| Container runtime & dependency provisioning | `infra_001` | sandbox posture, engine, claude adapter, resolver, lifecycle mgr |

See `docs/STATUS.md` for the live backlog and `docs/stories/` for details.
