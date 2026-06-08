# infra_002: Base image + container lifecycle manager

**Status:** DONE  · _built 2026-06-08 (Dockerfile + ContainerManager, tested)_
**Mode:** BUILD
**Module:** infra_
**Created:** 2026-06-08
**Layer:** 4

## Context

Implements the sealed `infra_001` decision. The engine uses basic `docker exec` in M0;
this story builds the real base image and the lifecycle manager that makes containers
warm, reusable, and fast to recreate.

## Goal

A built base image (on `claude-docker` + runtime agent) and a lifecycle manager:
`ensure_ready(pipeline_id)` (create or reuse, provision, signal ready), `exec(step)`,
volume mounting (`/lib`, `/work`, session store), dependency-cache reuse, optional
commit-snapshot, and teardown.

## Approach

**Recommendation:** a `ContainerManager` the engine calls instead of raw docker;
implements states create → provisioning → ready → running; persists the dep cache on a
named volume; commits a snapshot when configured.

**Reasoning:** Hardens the M0 basic-exec path into the robust warm-reuse model.

## Acceptance Criteria

- [ ] Base image builds and runs Claude (plan auth) inside the container
- [ ] `ensure_ready` creates-or-reuses and reaches a ready state
- [ ] Volumes mounted; session store persists across recreate
- [ ] Dependency-cache reuse demonstrated (fast recreate)
- [ ] Optional commit-snapshot path works
- [ ] Replaces the engine's basic docker-exec usage

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: infra_001 (sealed)

Cross-module:
- Requires: be_001 (engine to integrate with)
