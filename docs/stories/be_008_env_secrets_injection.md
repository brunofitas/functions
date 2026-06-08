# be_008: Environment bus & secrets injection

**Status:** DONE  · _built 2026-06-08 (functions_be.env, masking verified)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 2

## Context

Implements the model sealed in `be_002`: inject secrets/env into each step, let a step
export env downstream (the mutable bus), and mask secrets everywhere. This is what makes
the AWS-login-then-reuse pattern work safely.

## Goal

A runtime env/secrets layer: resolves the effective environment for a step
(per-step > global > bus), injects secrets into the container (env/files), captures a
step's exported env into the bus, and masks secret values in all logs/streams.

## Approach

**Recommendation:** an `EnvBus` the engine threads through steps; secrets fetched from the
configured store at step boundaries; a masking filter on all emitted events.

**Reasoning:** Centralizes the security-sensitive logic in one auditable place.

## Acceptance Criteria

- [ ] Effective env computed with correct precedence
- [ ] Secrets injected per the sealed mechanism; never persisted to cache/defs
- [ ] Step `export` updates the bus per the sealed scoping rules
- [ ] Secret values masked in logs and the streamed console
- [ ] Test: AWS-style export from step A is visible to step B; secret never appears in logs

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: be_002 (sealed), be_001
- Blocks: be_009
