# claude-pipelines — Vision

> Compose Claude Code into reusable **functions**, wire them into **pipelines**, and
> run them from a desktop app that owns your filesystem, secrets, and a shared
> Claude session — so step B inherits everything step A did.

---

## 1. Why

Today, chaining Claude Code means hand-rolling shell scripts: managing session
IDs, threading context, juggling `--add-dir`, and re-solving secrets/env every
time. We proved the mechanics work (see [§9 Proven foundation](#9-proven-foundation)),
but the ergonomics don't scale past a toy chain.

**claude-pipelines** turns that mechanic into a product: a library of composable,
shareable units of Claude work, a visual editor to wire them together, and an
orchestrator that handles session continuity, secrets, environment, and lifecycle
so you don't have to.

The north star: *npm/Docker-Hub for Claude workflows* — installable units, a
marketplace, semantic versioning — with a **Zapier/n8n-style** visual editor on top,
but where every node is a Claude Code session sharing one workspace and one memory.

---

## 2. The core idea: everything is a function

A **Function** is the atomic, self-contained unit of Claude work. It declares what
it needs and what it produces, and it runs via a standard entrypoint.

A **Pipeline** is just a function whose body orchestrates *other* functions. It has
the same manifest shape (inputs, outputs, secrets, env), which means **pipelines
compose pipelines** — recursively, without a special case. There is one abstraction,
not two.

```
Function  ──declares──▶  Requirements { Secrets, Environment, Inputs }
          ──produces──▶  Outputs
          ──persists──▶  Storage
          ──signals───▶  Events  (emit / listen)
          ──runs via──▶  Makefile: run, test

Pipeline = Function whose `run` wires N functions together and controls flow.
```

### Function on disk

```
<namespace>/<name>/
├── function.yaml      # the manifest / schema (contract)
├── Makefile           # `make run`, `make test`  (standard entrypoints)
├── README.md          # human docs (rendered in the GUI)
├── i18n/              # en.json, pt.json, …  (labels, descriptions, errors)
│   └── en.json
└── src/               # implementation: prompts, scripts, assets
    └── prompt.md
```

The `Makefile` is the runtime contract — the orchestrator never needs to know the
language inside. `make run` executes the step; `make test` validates it in isolation.

### The manifest (`function.yaml`)

```yaml
apiVersion: claude-pipelines/v1
kind: function                 # or: pipeline
namespace: aws
name: login
version: 0.1.0
description: Authenticate to AWS; export session credentials to the shared env.

requirements:
  secrets:                     # injected at runtime, never stored in the def
    - { name: AWS_ACCESS_KEY_ID }
    - { name: AWS_SECRET_ACCESS_KEY }
  environment:                 # config with optional defaults
    - { name: AWS_REGION, default: eu-west-1 }
  inputs:                      # structured, wired from upstream outputs
    - { name: role_arn, type: string, required: false }

outputs:
  - { name: account_id,        type: string }
  - { name: session_expires_at, type: string }

storage:                       # declared persistent scratch (survives a run)
  - { path: .cache/aws }

events:
  emits:   [ready, error]
  listens: [end]               # graceful shutdown on the pipeline "end" signal

i18n: ./i18n
```

---

## 3. The pipeline model

A pipeline wires functions by reference and maps data between them.

```yaml
apiVersion: claude-pipelines/v1
kind: pipeline
namespace: acme
name: deploy-flow
version: 1.0.0

steps:
  - id: login
    use: aws/login@0.1.0                         # ① registry / marketplace ref
    with:
      role_arn: ${{ secrets.DEPLOY_ROLE }}

  - id: build
    use: ./functions/build                       # ② pipeline-relative disk ref

  - id: deploy
    use: github:brunofitas/fn-deploy@main        # ③ public GitHub ref
    with:
      artifact:   ${{ steps.build.outputs.artifact }}
      account_id: ${{ steps.login.outputs.account_id }}   # data flows forward

flow:
  mode: standalone            # standalone | streaming  (see §6)
  end:  { signal: END }
```

### Reference resolution (`use:`)

| Form | Example | Source |
|------|---------|--------|
| Registry | `aws/login@0.1.0` | marketplace / installed library |
| Pipeline-relative | `./functions/build` | disk, relative to the pipeline |
| Absolute | `/Users/me/fns/lint` | disk, anywhere |
| GitHub | `github:owner/repo/subdir@ref` | public repo |
| URL | `https://…/fn.tar.gz` | archive |

On first use, a referenced function is **installed** into the local library cache
`.lib/cache/<namespace>/<name>@<version>/` (so runs are reproducible and offline).
Dragging a marketplace function into the editor installs it the same way.

---

## 4. Shared context — the thing that makes this special

The whole point: **functions are not isolated subprocesses; they share state.** Four
shared channels, from implicit to explicit:

1. **Claude session (memory).** Every step runs inside *one* resumed Claude session,
   so step B *remembers* step A's reasoning, not just its output. This is the
   superpower ordinary script-chaining can't give you.
   > ⚠️ **Hard constraint (proven):** Claude sessions are stored **per directory**.
   > A session created in `A/` cannot be resumed from `B/`. Therefore the orchestrator
   > runs **every step from one fixed root** and points each step at its function
   > folder via `--add-dir` + a prompt header. This is non-negotiable architecture.

2. **Workspace (filesystem).** All functions see the same working directory / repo.
   This is how *"function A logs into AWS, function B uses that login"* works: `aws
   login` writes `~/.aws/…` and exports env in the shared HOME/workspace, so B simply
   finds it there. Side effects persist because the environment is shared, not copied.

3. **Environment bus (mutable).** A function can **export** env vars downstream
   (e.g. `AWS_PROFILE`, a fetched token). The orchestrator merges per-step env over
   global env over the running bus.

4. **Structured I/O.** Declared `inputs`/`outputs` move as JSON: each step reads
   `$PIPELINE_INPUTS` (a JSON file/var) and writes `$PIPELINE_OUTPUTS`; the
   orchestrator maps outputs→inputs per the pipeline's `with:` wiring.

Plus **Secrets** (injected from a vault/env-file at run time, never written into
function defs or the cache) and **Storage** (declared persistent scratch).

---

## 5. Sources, registry & marketplace

- **Namespacing:** every function is `namespace/name` — globally unique, filterable,
  searchable. Versioned (`@semver`).
- **Local-first:** functions live on disk or on GitHub; when installed/dragged they
  are cached under `.lib/cache/` so the pipeline is self-contained and reproducible.
- **Marketplace:** browse/search published functions; "Install from GitHub" or
  "Install from disk". Local functions and marketplace functions appear together in
  the editor sidebar.

---

## 6. Execution & lifecycle

The pipeline **controls the flow**. Two run modes:

- **Standalone:** run once, top to bottom, then stop.
- **Streaming:** the pipeline stays alive and can be triggered repeatedly with
  different context (a long-lived agent loop / server). Functions may be long-lived
  processes rather than one-shot calls.

**The `END` signal (graceful shutdown).** A streaming pipeline can run "forever."
To stop, the pipeline emits an `END` event that **propagates downstream**; each
function that `listens: [end]` flushes, publishes its final output, and shuts down
cleanly (a poison-pill / drain pattern). No abrupt kills.

**Control:** run, **pause**, resume, and **wait** — where a wait is satisfied either
**manually** (human approves in the GUI) or by a **condition** (an expression over
prior outputs/events). Pause/resume operate on the live session, not by restarting.

---

## 7. GUI surfaces

A desktop app (macOS / Linux / Windows) with these primary surfaces:

1. **Pipeline editor** — canvas with **drag-and-drop** from a sidebar of *local* and
   *marketplace* functions; wire outputs→inputs; set per-step `with:` values; choose
   run mode; insert waits/conditions.
2. **Function creator / editor** — scaffold a new function (manifest + Makefile +
   README + i18n), edit prompts/schema, run `make test` in isolation.
3. **Function & pipeline browser** — searchable, filterable list by namespace; the
   marketplace plus installed/local items.
4. **Run console** — live streaming output per step (the prototype already does
   this), step status (running/done/error), pause/resume/end controls, session id.
5. **Settings** — global **environment**, **secrets** (vault), and **folders /
   workspaces**.

---

## 8. Architecture

Split into a **headless orchestrator** (trusted, local, owns the dangerous bits) and
a **GUI** (presentation), talking over a local HTTP/WebSocket API.

```
┌────────────────────────────────────────────────────────────┐
│  GUI  (PWA  ·  or wrapped as a native desktop shell)         │
│  pipeline editor · function editor · marketplace · console   │
└───────────────▲──────────────────────────────────────────────┘
                │  HTTP + WebSocket (localhost)
┌───────────────┴──────────────────────────────────────────────┐
│  Orchestrator / host agent  (the trusted daemon)              │
│  • resolves & installs functions  → .lib/cache               │
│  • injects secrets / env / inputs                             │
│  • runs steps from ONE fixed root, shared Claude session      │
│  • maps outputs→inputs · event bus · pause/wait/END           │
│  • streams stdout (stream-json) to the GUI                    │
└───────────────┬───────────────┬───────────────┬──────────────┘
        filesystem        OS keychain        claude CLI
        (workspace)      (secrets/OAuth)    (sessions)
```

- **PWA + host agent.** The GUI *can* be a Progressive Web App that talks to a local
  orchestrator process which owns filesystem, secrets, and Claude sessions. The
  browser never touches secrets directly; it only sees what the orchestrator streams.
  (A native shell — Tauri/Electron — is an optional wrapper for install/notarization
  and a real `.app` window; same orchestrator underneath.)

- **Docker.** The orchestrator can run containerized on top of
  [`claude-docker`](https://github.com/brunofitas/claude-docker) (it already mounts
  the workspace and pulls the OAuth token from the host keychain). The **function
  library is a mounted volume**, so functions are added dynamically to a running
  container without rebuilds. Secrets arrive via env/secret files; no ports needed
  except the orchestrator's local API.

- **Engine internals (from the prototype):** `claude -p` headless,
  `--output-format stream-json --verbose` for live tokens, one `--session-id` then
  `--resume` across steps, `--add-dir <function>` per step, `--permission-mode`
  (`acceptEdits` interactive / `bypassPermissions` unattended).

---

## 9. Proven foundation

A working prototype (`../`) already demonstrates the load-bearing mechanics:

- ✅ Chain N folders, each with a `prompt.md` + `Makefile`, via one local web app.
- ✅ **Shared session carries memory** across folders (A picks a theme → B writes
  using it → C continues the *same* story).
- ✅ Live streaming of each step to the browser over SSE.
- ✅ Discovered & worked around the **per-directory session** constraint (run all
  steps from a fixed root + `--add-dir`).

claude-pipelines is the productization of that prototype.

---

## 10. Security model (first-class, not an afterthought)

- Secrets are **never** stored in function defs, manifests, or the library cache.
  They're injected at run time from the OS keychain / a vault / env-files and are
  masked in logs and the streamed console.
- Installed functions are **third-party code**. They must run under an explicit
  permission mode and, ideally, inside the Docker sandbox. The marketplace needs
  provenance (signed/pinned versions) before it's trusted by default.
- The GUI (especially as a PWA) holds **no** secrets; the orchestrator is the only
  trust boundary.

---

## 11. Roadmap (phased)

1. **M0 — Engine.** Formalize the prototype: function manifest + resolver, shared
   session, structured I/O, env/secrets injection. CLI-driven, no fancy GUI.
2. **M1 — Orchestrator API.** HTTP/WS daemon: run/pause/resume/end, streaming,
   event bus, install-from-disk/GitHub.
3. **M2 — GUI.** Run console → function browser → drag-and-drop pipeline editor →
   settings (env/secrets/folders).
4. **M3 — Function authoring.** Creator/editor, `make test` harness, i18n.
5. **M4 — Marketplace.** Publish, search, versioning, provenance.
6. **M5 — Streaming & Docker.** Long-lived pipelines, `END` propagation, containerized
   orchestrator with dynamic library volume.

---

## 12. Open questions

- **Inter-step session vs. parallelism:** a single shared session is inherently
  sequential. How do we support *parallel* branches (fan-out/fan-in) that still share
  the workspace? (Forked sessions per branch, merged how?)
- **Output contract enforcement:** do we validate `outputs` against the manifest
  schema, and fail the step if a function lies about what it produced?
- **Versioning across the chain:** how do pipeline-relative refs interact with pinned
  registry versions in the cache?
- **Secret scoping:** per-function least-privilege vs. the convenience of a shared env
  bus (the AWS-login example deliberately leaks credentials downstream).
- **Streaming semantics:** exactly-once vs. at-least-once when a streaming pipeline is
  re-triggered with new context mid-flight.
