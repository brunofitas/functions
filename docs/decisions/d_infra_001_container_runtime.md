# d_infra_001: Container runtime & dependency provisioning

**Status:** SEALED
**Date:** 2026-06-08
**Story:** infra_001
**Scope:** infra_ + be_ (engine, claude adapter, resolver, lifecycle manager)

## Context

Pipelines run on Docker. The runtime model is the project's meatiest decision: avoid
building a unique image per function-combination (image/disk explosion) while still
giving each pipeline the tools it needs. Most parameters were agreed across earlier
design conversation; this record codifies them plus two sub-decisions made in the gate.

## Decision

### 1. Base image

A single shared base image built on **`brunofitas/claude-docker`** + the runtime agent.
All pipelines run off it. No per-combination image builds.

### 2. Runtime dependency provisioning

Dependencies are installed **into the running container at load time** (background
warm-up until **ready**), driven by Claude **from each function's pinned manifest
`dependencies`** (`system`/apt, `python`/pip). Claude executes; the manifest is the
source of truth → reproducible.

### 3. Container lifecycle scope — FRESH PER RUN + warm cache  *(decided)*

- Each **pipeline run** gets a **fresh container** (clean `/work`, new session), torn
  down on completion → **isolated and reproducible** runs.
- A shared **dependency-cache volume** keeps warm-up fast despite recreation.
- **Within a run**, all steps (and a streaming run's re-triggers) share that one
  container → the proven shared-session memory holds across steps. Memory does **not**
  persist across separate standalone runs.

### 4. Fast warm-up — dependency-cache volume  *(decided)*

On (re)create, always (re)install from the pinned deps, but a shared cache volume
(apt/pip downloads) makes it fast. Always in sync with the manifest. A `docker commit`
**snapshot** remains an *optional future optimization*, not the default (avoids
snapshot-vs-manifest drift).

### 5. Volumes & control channel

- Volumes: **`/lib`** (function library), **`/work`** (workspace, per-run), session
  store, and the shared **dep-cache** volume.
- Control channel: **Claude Code CLI over `docker exec`** (`claude -p`, stream-json,
  `--add-dir`, `--session-id`/`--resume`); Agent SDK deferred.
- **recreate-on-missing**: if the run's container is absent, create from base + provision.

## Options considered

- **Scope:** fresh-per-run + warm cache (chosen — reproducible/isolated) vs. persistent
  per-pipeline (warmest, but stateful/leaky and less reproducible).
- **Fast restart:** dep-cache volume (chosen — correct, simple) vs. commit-snapshot
  (fastest but drift) vs. both (deferred as opt-in).
- **Provisioning time:** runtime (chosen) vs. build-time artifact composition (`COPY
  --from`) vs. Nix (rejected for v1: build/space/learning cost).

## Consequences

- `infra_002` builds the base image + a `ContainerManager`
  (`ensure_ready(run_id)` → create / provision / ready; `exec(step)`; mount volumes;
  teardown) implementing this model. The engine (`be_001`) uses basic `docker exec` in
  M0, swapped for the manager later.
- `be_006` (claude adapter) execs through this; `be_010` library cache is the mounted
  `/lib`.
- Updates the intake's earlier "reused across subsequent runs" wording → **fresh per
  run** (subsequent standalone runs get fresh containers sharing the dep-cache).

## Affected stories

Unblocks: `be_003`. Constrains: `be_001`, `be_006`, `be_010`, `infra_002`.
