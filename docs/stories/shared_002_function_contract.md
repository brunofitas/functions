# shared_002: Function/pipeline contract + runtime-adapter interface

**Status:** DONE
**Mode:** DESIGN
**Module:** shared_
**Created:** 2026-06-08
**Layer:** 1

> **SEALED 2026-06-08** → `docs/decisions/d_001_function_contract.md`. Outputs =
> always-strict; I/O = JSON files + env mirror; YAML manifest, single `kind:` envelope,
> opt-in `exports`, runtime-adapter interface with capabilities.

## Context

This is the spine. Every other module agrees through this contract, so it must be sealed
before the contract library, engine, adapters, secrets, eventing, and container runtime
are built. Multiple viable schema/serialization approaches exist, and it defines a
cross-module interface — a Design Gate by ai-sprint's own triggers.

## Goal

A sealed decision defining: the function/pipeline **manifest schema** (`namespace`,
`name`, `version`, `runtime`, `dependencies`, `requirements{secrets,environment,inputs}`,
`outputs`, `storage`, `events`, `i18n`); the **inputs/outputs/events** wire format and
how they cross steps; the **runtime-adapter interface** (`provision`/`execute`/`collect`
+ capabilities `is_llm`, memory model, entrypoint, dep kinds); the reference-string
grammar; and whether `outputs` are validated against the manifest (and what happens on
mismatch).

## Approach

_DESIGN — filled during the Design Gate (`design: shared_002`)._

**Leading direction:** YAML manifest (`kind: function | pipeline`), `${{ }}` wiring
expressions, JSON for runtime I/O (`$PIPELINE_INPUTS`/`$PIPELINE_OUTPUTS`), adapters as
a Strategy interface with declared capabilities. Decide: schema format & validation
strictness, the adapter interface signature, output-enforcement policy.

## Acceptance Criteria

- [ ] Manifest schema specified with every field + types
- [ ] Inputs/outputs/events wire format + cross-step mapping defined
- [ ] Runtime-adapter interface + capability flags defined
- [ ] Reference-string grammar defined (registry / `./` / abs / `github:` / `https:`)
- [ ] Output-validation policy decided
- [ ] Sealed decision record in `docs/decisions/d_001_function_contract.md`

## Output

- `docs/decisions/d_001_function_contract.md` (SEALED)

## Dependencies

Within module:
- Requires: shared_001
- Blocks: shared_003

Cross-module:
- Blocks: be_002, be_012, infra_001, be_001, be_004, be_007, fe_003, fe_004 — all build
  against this contract.

## Notes

Keep the contract minimal and additive — new runtimes must not require contract changes.
