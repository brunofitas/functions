# Intake — functions  ·  repo `brunofitas/functions`

> Distilled from `docs/VISION.md` and the prototype in `.bk/`. Facts only;
> assumptions are flagged in §7. Architecture choices are deferred to ARCHITECT /
> Design Gates and are **not** decided here.

## 1. What are we building?

**functions** — an **open-source, cross-platform desktop application** (macOS / Linux /
Windows, distributed via GitHub Releases) that chains units of work called
**functions** into **pipelines**, running them locally on Docker.

The single abstraction is the *function*: a self-contained unit of work that declares
Inputs, Environment, Storage, Secrets, Events, Outputs, and a **`runtime`**. Each
runtime is a pluggable **adapter** (provision deps → execute → stream → collect
outputs) declaring its capabilities — notably `is_llm` (costs tokens, non-deterministic)
and how/if it carries cross-step memory. **v1 ships three runtimes:**

- **`bash`** — runs `run.sh` as a subprocess (apt deps); deterministic, free.
- **`python`** — runs `main.py` (pip deps); deterministic, free.
- **`claude`** — runs inside a Claude Code session (CLI over `docker exec`); LLM, gets
  shared memory across steps via session resume; consumes the Claude plan.

Further runtimes (`openai`, Node, …) are added later as new adapters with no core
changes. The `Makefile` (`run`/`test`) becomes the **`custom`** escape-hatch runtime.
Deterministic runtimes share the workspace, env, secrets, and structured I/O but no LLM
memory; LLM runtimes additionally carry memory (Claude via session, OpenAI via
orchestrator-threaded history).

A *pipeline* is itself a function whose body orchestrates other functions — so
pipelines compose recursively. A local **orchestrator** runs a pipeline's steps over
one shared workspace, threading environment, secrets, and structured inputs/outputs,
and (for `claude` steps) one shared Claude session so step B inherits step A's memory.

## 2. What problem does it solve?

Chaining Claude Code today means hand-rolled shell scripts: manually managing session
IDs, threading context, juggling `--add-dir`, and re-solving secrets/env every run.
That doesn't scale past a toy chain and isn't shareable.

**functions** makes such workflows **composable, shareable, and reproducible** —
installable units with namespaces and versions, an orchestrator that owns session
continuity / secrets / environment / lifecycle, and (mixing LLM and deterministic
runtimes) so you only pay for the LLM where you actually need judgment. Target users:
developers who automate multi-step work with Claude Code and want to package, reuse,
and share those workflows. Distributed as a personal, local tool — not a service.

## 3. Constraints

- **Execution backend:** built on the Claude Code CLI (`claude -p`, session resume,
  `--add-dir`, `--permission-mode`, `--output-format stream-json`) for `claude`-kind
  steps; `plain` steps run their `Makefile` directly.
- **Claude auth & cost (v1):** uses the **Claude CLI subscription plan** (OAuth login;
  token from the host keychain via claude-docker) — **not** an API key. Cost is bounded
  by the plan, not metered API billing. **API-key auth is a later addition**, not v1.
- **Platforms & distribution:** runs on macOS, Linux, Windows; shipped as **installers
  via GitHub Releases**, built by a **GitHub Actions** pipeline.
- **Quality gate:** a single shared root `.venv`; **every module — including the
  frontend — must hold ≥85% test coverage**, enforced in CI (build fails below). All
  functionality (incl. API calls, with network mocked) must be tested. A root `Makefile`
  builds, tests, and deploys all modules.
- **Hard technical fact (proven):** Claude sessions are stored **per directory** — a
  session created in `A/` cannot be resumed from `B/`. Every step therefore runs from
  **one fixed root**, targeting each function folder via `--add-dir`. Requirement, not
  an option.
- **Local trust boundary:** the orchestrator (local process) owns secrets and
  filesystem; the GUI never holds secrets. The orchestrator binds to **loopback only**
  and authenticates the GUI with a locally-generated token (a pre-shared secret signs a
  short-lived token; the secret never goes on the wire) — a standard local-app pattern
  (cf. Jupyter), **not** an enterprise auth system.
- **Secrets sourcing:** read from a local secrets store and/or env files; injected at
  run time, masked in logs, never persisted into function defs or the library cache.
- **Standard function structure:** each function ships a manifest declaring its
  contract (incl. its **`runtime`** and dependencies), a runtime-specific entrypoint
  (`run.sh` / `main.py` / `prompt.md`, or a `Makefile` for the `custom` runtime), a
  `README.md`, and an `i18n/` folder. `make test` is the fallback test convention.
- **Reference sources:** functions resolvable from disk (absolute and pipeline-relative
  `./`), public GitHub repos, and URLs; installed/cached locally on first use.
- **Containerized execution (primary sandbox):** Claude runs **inside Docker** (building
  on `brunofitas/claude-docker`). A pipeline runs as **one long-lived, reusable
  container** addressed by ID: created from a shared base image if absent, **provisioned
  at runtime** (not at build), and **reused across many calls** while warm. The function
  library and workspace are **mounted volumes**; the session store and fixed root live
  on **persistent volumes** so memory carries across calls within the container.
  Container identity is scoped to a pipeline (or pipeline-run); cross-container memory
  sharing is **not** a v1 goal.
- **Runtime dependency provisioning:** dependencies are installed **into the running
  container at load time** (background warm-up until **ready**), driven by Claude **from
  each function's declared, pinned manifest** (Claude executes; the manifest is the
  source of truth) so runs stay reproducible. A persisted dep-cache volume makes
  recreate→reinstall mostly cache hits; an optional `docker commit` **snapshot** yields a
  fast-restart image produced at runtime. Because Docker `FROM` is single-inheritance, a
  function "extending" another (aws → claude-docker; a pipeline needing aws + gcp) is
  realized by **installing declared dependency sets into the shared container**, not by
  chaining `FROM` — avoiding image/disk explosion.
- **Claude control channel:** the orchestrator drives Claude via the Claude Code CLI over
  `docker exec` (proven in the prototype); the Claude Agent SDK is a later alternative.

## 4. Scope

**Classification:** open-source product, delivered in milestones. **v1 is a thin
vertical slice** (engine + contract + a few real functions + CLI run, in Docker) that
proves the shared-session value end-to-end before the GUI/marketplace are built.

Full intended capabilities:

- **Function model** — atomic unit with a pluggable **`runtime`** (v1: `bash`,
  `python`, `claude`; `custom` via Makefile) declaring Inputs, Environment, Storage,
  Secrets, Events, Outputs, Dependencies; standard on-disk structure (manifest,
  entrypoint, `README.md`, `i18n/`).
- **Pipeline model** — pipelines compose functions; pipelines are themselves functions
  (recursive); pipelines control the flow. **v1 = linear/sequential chains**;
  fan-out/fan-in DAGs are deferred (see §7).
- **Shared context across steps** — (a) shared Claude **session** for `claude` steps
  (memory carries forward), (b) shared **workspace/filesystem** (A logs into AWS, B
  reuses it), (c) mutable **environment bus**, (d) structured **inputs→outputs** wiring.
- **Function resolution & library** — disk (abs + `./`), public GitHub, URL; install to
  a local library cache; namespaced `namespace/function`, searchable, filterable.
- **Execution & lifecycle** — run, **pause**, resume, **wait** (manual or condition);
  standalone and **streaming** (long-lived, re-triggerable) modes; an **END signal**
  that propagates downstream for graceful shutdown.
- **GUI (later milestone)** — drag-and-drop **pipeline editor**; **function
  creator/editor** + searchable list; **settings** (env / secrets / folders); a **run
  console** with live per-step streaming and run/pause/end controls; a **marketplace
  browser** for installable functions.
- **Distribution** — GitHub Releases installers for the three platforms via CI.

## 5. Out of Scope

- **Enterprise** — multi-tenant hosting, user accounts, team permissions, per-client
  secrets, token rotation/revocation, audit logging, mTLS/SSO. Explicitly dropped.
- **API-key auth** — v1 uses the Claude CLI plan; API-key support is deferred.
- **Runtimes beyond `bash`/`python`/`claude`** — the adapter interface is designed for
  more (`openai`, Node, …) but they're **deferred**; `openai` in particular waits on
  API-key/secret support.
- **DAG / parallel branches** — v1 is sequential chains; deferred (§7).
- **A hosted registry / publishing flow / paid marketplace** — install-from-GitHub/disk/
  URL only; publishing and a hosted index are deferred.
- **Cross-container memory sharing**, mobile clients.

## 6. Potential Modules

| Module | Prefix | Description |
|--------|--------|-------------|
| Shared contracts | `shared_` | Function/pipeline manifest schema, the inputs/outputs/events contract, function **kind**, shared types, authoring scaffold. |
| Orchestrator | `be_` | Local daemon: function resolution & install + library cache, shared-session execution from a fixed root, container lifecycle, env/secrets/input injection, output mapping, event bus, run/pause/wait/END, streaming, loopback API + local-token auth. |
| Studio (GUI) | `fe_` | Front end: pipeline editor, function creator/editor, marketplace browser, settings, live run console. |
| Runtime / packaging | `infra_` | Base Docker image (on `claude-docker`) + container runtime; cross-platform installers via GitHub Releases / Actions. |

> *Four modules (registry folded into `be_`). Boundaries are a starting proposal for
> ARCHITECT, not sealed.*

## 7. Assumptions

Flagged (not buried). Each needs confirmation or a Design Gate.

1. **Claude-only backend; CLI plan auth.** Execution is the Claude Code CLI on the
   subscription plan; no provider abstraction and no API key in v1.
2. **Local, single-user, open-source tool.** No enterprise/multi-tenant concerns;
   loopback-only API with a simple local token.
3. **Marketplace = install from GitHub/disk/URL.** No hosted registry or publishing in
   v1; the GUI marketplace browser is a later milestone.
4. **Stack (working choice):** Python + asyncio for the orchestrator (per the prototype
   and the eventing direction); TypeScript for the GUI. Confirmable in ARCHITECT.
5. **Linear-first execution.** v1 runs sequential chains (matches the proven
   shared-session model); fan-out/fan-in DAGs are a deliberate later decision.
6. **Pluggable runtimes via adapters.** v1 = `bash`, `python`, `claude` (+ `custom`
   Makefile). LLM-ness is a runtime *capability* (drives cost, determinism, memory), not
   a special case; deterministic runtimes cost nothing. New runtimes = new adapters.
7. **`bypassPermissions` for unattended runs**, with functions running inside the Docker
   sandbox; formal provenance/trust is deferred to the marketplace milestone.

---

### Open decisions deferred to Design Gates

Lean set — the genuinely hard, multi-approach calls that gate BUILD:

- **Function & pipeline contract** — manifest schema (incl. `runtime`, dependencies),
  the inputs/outputs/events shape, the **runtime-adapter interface** (provision /
  execute / stream / collect; capabilities like `is_llm` and memory model), and whether
  `outputs` are validated against the manifest. → `shared_002`.
- **Container runtime & dependency provisioning** — warm reusable container, runtime
  Claude-driven install from pinned deps, recreate-on-missing, readiness/warm-up,
  dep-cache volume vs. `docker commit` snapshot. → `infra_001`.
- **Eventing/streaming substrate** — asyncio-native (async generators + anyio /
  aiostream, the leading choice) vs. RxPY; backbone for `stream-json`, the event bus,
  pause/END. → `be_012`.
- **Secret scoping** — per-function least privilege vs. the shared env bus that
  deliberately leaks credentials downstream (the AWS-login example). → `be_002`.

**Resolved / deferred (no longer gates):**

- *Execution model* — resolved to **sequential, shared-session** (proven); DAG/parallel
  deferred. So `be_001` becomes a BUILD story, not a gate.
- *Host↔GUI auth* — resolved to **loopback + local token** (no enterprise); `be_013` is
  a BUILD story.
- *Provenance/marketplace trust* — deferred to the marketplace milestone (`be_003`
  becomes a lightweight security note, not a v1 gate).
- *Streaming exactly-once semantics* — revisit when streaming mode is built.
