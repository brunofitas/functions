# Module: infra_  — Runtime & packaging

## Purpose

The container runtime that pipelines execute in, and the distribution pipeline that
ships the app.

## Responsibilities

- **Base image** — built on `brunofitas/claude-docker` + the runtime agent; the shared
  image all pipelines run off.
- **Container lifecycle manager** — create / recreate-on-missing / warm-up / readiness /
  reuse; dependency-cache volume; optional `docker commit` snapshot.
- **Distribution** — cross-platform installers (macOS / Linux / Windows) via GitHub
  Releases, built by a GitHub Actions pipeline.

## Public interface (consumed by be_)

- Container control surface: ensure-ready(pipeline_id), exec(step), mount volumes
  (`/lib`, `/work`, session store), teardown.

## Internal dependencies

- `shared_` (manifest dependency declarations); integrates with `be_` engine.

## Stories

- `infra_001` — **DESIGN** — Container runtime & dependency provisioning
- `infra_002` — Base image + container lifecycle manager
- `infra_003` — Cross-platform installers (GitHub Releases / Actions)
