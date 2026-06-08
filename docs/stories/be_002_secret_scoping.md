# be_002: Secret scoping & environment bus

**Status:** DONE
**Mode:** DESIGN
**Module:** be_
**Created:** 2026-06-08
**Layer:** 1

> **SEALED 2026-06-08** → `docs/decisions/d_be_001_secret_scoping.md`. Encrypted local
> vault (age/sops) → env injection, **least-privilege** (only declared secrets), masked
> everywhere; opt-in `exports`; precedence per-step > global > bus.

## Context

Functions declare `secrets` and an `environment`; a step can export env downstream (the
mutable bus) — that's how "function A logs into AWS, function B reuses it" works. But the
env bus *deliberately leaks* credentials downstream, which collides with least-privilege.
Security-sensitive with multiple viable models → a Design Gate.

## Goal

A sealed decision on: how secrets are sourced (store / env files), injected (env vs files
in the container), masked in logs/streams, and scoped (per-function least privilege vs.
shared bus); how a step exports env to later steps; and the precedence order
(per-step > global > running bus).

## Approach

_DESIGN — filled during the Design Gate (`design: be_002`)._

**Leading direction:** secrets injected as container env/files at step boundaries,
masked everywhere; an explicit `export` list per function so leakage downstream is
opt-in, not automatic; precedence per-step > global > bus.

## Acceptance Criteria

- [ ] Secret sourcing + injection mechanism decided
- [ ] Masking strategy for logs and the streamed console
- [ ] Scoping model (opt-in export vs. open bus) decided
- [ ] Env precedence order defined
- [ ] Sealed decision record in `docs/decisions/d_be_001_secret_scoping.md`

## Output

- `docs/decisions/d_be_001_secret_scoping.md` (SEALED)

## Dependencies

Within module:
- Requires: shared_002 (sealed)
- Blocks: be_008

Cross-module:
- Blocks: fe_005 (settings)
