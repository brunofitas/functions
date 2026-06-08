# infra_001: Container runtime & dependency provisioning

**Status:** DONE
**Mode:** DESIGN
**Module:** infra_
**Created:** 2026-06-08
**Layer:** 1

> **SEALED 2026-06-08** → `docs/decisions/d_infra_001_container_runtime.md`. Shared base
> on claude-docker; runtime provisioning from pinned deps; **fresh-per-run** container +
> shared **dep-cache volume**; CLI over `docker exec`; recreate-on-missing. Snapshot
> deferred as opt-in.

## Context

Pipelines run in Docker, and the runtime model is the project's meatiest decision:
one long-lived reusable container per pipeline, provisioned at runtime (not built per
combination), so we avoid image/disk explosion. Multiple viable approaches (runtime
provisioning vs. build-time artifact composition vs. Nix) → a Design Gate.

## Goal

A sealed decision covering: the shared base image; container identity & lifecycle
(create / recreate-on-missing / warm-up / readiness / reuse); how Claude provisions
declared (pinned) deps at runtime; the dependency-cache volume; the optional
`docker commit` snapshot for fast restart; volume layout (`/lib`, `/work`, session
store); and the Claude control channel (CLI over `docker exec` vs. Agent SDK).

## Approach

_DESIGN — filled during the Design Gate (`design: infra_001`)._

**Leading direction:** long-lived container per pipeline; Claude installs from the
manifest's pinned deps; dep-cache named volume so recreate→reinstall is cache hits;
optional commit-snapshot; CLI over `docker exec` as the control channel.

## Acceptance Criteria

- [ ] Base image strategy decided (on `brunofitas/claude-docker`)
- [ ] Container identity + lifecycle states defined (create/recreate/warm/ready/reuse)
- [ ] Runtime provisioning + dependency-cache approach decided
- [ ] Snapshot (commit) policy decided
- [ ] Volume layout + session-store persistence defined
- [ ] Control channel decided
- [ ] Sealed decision record in `docs/decisions/d_infra_001_container_runtime.md`

## Output

- `docs/decisions/d_infra_001_container_runtime.md` (SEALED)

## Dependencies

Within module:
- Requires: shared_002 (sealed)
- Blocks: infra_002

Cross-module:
- Blocks: be_001, be_003, be_006, be_010
