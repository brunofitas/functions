# shared_003: Contract library (schema / parser / validation)

**Status:** DONE
**Mode:** BUILD
**Module:** shared_
**Created:** 2026-06-08
**Layer:** 2

> **DONE 2026-06-08** — `functions_shared` implements the sealed contract: Pydantic
> manifest models, `parse_ref` (5 forms), strict `validate_outputs`, JSON/env I/O
> helpers, `${{ }}` resolver, YAML loader. 44 tests, **100% coverage**, ruff clean.

## Context

Once the contract is sealed (`shared_002`), it needs a concrete, importable
implementation that both `be_` and `fe_` use so manifests are parsed and validated
identically on both sides.

## Goal

`functions_shared` exposes typed models + functions to: load and validate a function or
pipeline manifest, parse reference strings, and validate a step's outputs against its
declared `outputs`. Round-trips the example manifests from the sealed decision.

## Approach

**Recommendation:** Pydantic models mirroring the sealed schema; a `parse_ref()` for the
reference grammar; `validate_outputs()` returning structured errors. Pure, no I/O.

**Reasoning:** A single source of truth prevents drift between orchestrator and GUI.

## Acceptance Criteria

- [ ] Typed models for function + pipeline manifests
- [ ] `load_manifest(path)` validates and raises structured errors
- [ ] `parse_ref(str)` handles all five reference forms
- [ ] `validate_outputs(manifest, produced)` per the sealed policy
- [ ] Unit tests cover the sealed example manifests

## Output

- `functions_shared/{models,refs,validation,io,expr,loader}.py` + `__init__.py`
- `tests/test_{models,refs,validation,io,expr,loader}.py`
- `pyproject.toml` (added `pyyaml`)

## Dependencies

Within module:
- Requires: shared_002 (sealed), shared_001
- Blocks: —

Cross-module:
- Blocks: be_004, be_007, be_001, be_010, fe_003, fe_004
