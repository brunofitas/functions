# shared_004: Quality gates + build/deploy tooling

**Status:** DONE
**Mode:** BUILD
**Module:** shared_
**Created:** 2026-06-08
**Layer:** 0

> **DONE 2026-06-08** — shared root `.venv`; ≥85% coverage gate enforced on every module
> (Python via `pytest.ini --cov-fail-under=85`, frontend via Vitest v8 thresholds);
> real frontend test suite (Vitest); root Makefile with `setup/test/build/deploy/lint/
> coverage/clean`; CI runs the gates. `make test` + `make build` verified green.

## Context

The maintainer set a project-wide quality bar before further BUILD: a single shared
root virtualenv, ≥85% test coverage on **every** module (including the frontend, with
all functionality — API calls etc. — tested), and one root Makefile to build, test, and
deploy everything. Cheaper to enforce now than to retrofit.

## Goal

A shared `.venv` at the repo root; an enforced ≥85% coverage gate per module that fails
the build below threshold; a real frontend test framework (mocked network calls so the
suite is hermetic); and a root Makefile with `setup`, `test`, `build`, `deploy`, `lint`,
`coverage`, `clean` covering all modules; CI enforcing the same gates.

## Approach

**Recommendation:** `pytest-cov` with `--cov-fail-under=85` in root `pytest.ini` for the
Python modules (shared `.venv`); **Vitest + @vitest/coverage-v8** with 85% thresholds for
`functions_fe`; root `Makefile` orchestrating both plus `build` (wheels + tsc) and
`deploy` (stub → installers come from `infra_003` CI). CI mirrors the gates.

**Reasoning:** Standard, language-appropriate tooling; gates live in config so local and
CI behave identically.

## Acceptance Criteria

- [x] Single shared `.venv` at repo root drives both Python modules
- [x] Python coverage gate ≥85% enforced (`pytest.ini`), fails below
- [x] Frontend test framework (Vitest) with ≥85% coverage thresholds enforced
- [x] Root Makefile: `setup`, `test`, `build`, `deploy`, `lint`, `coverage`, `clean`
- [x] CI runs lint + gated tests (Python ×3 OSes + frontend)
- [x] `make test` and `make build` verified green

## Output

- `pytest.ini` (coverage gate), `src/functions_fe/vitest.config.ts`,
  `src/functions_fe/src/index.test.ts`, updated `package.json` (Vitest)
- `Makefile` (build/deploy/test/lint/coverage/clean), `.github/workflows/ci.yml`
- dev-dep additions: `pytest-cov` (both Python modules)

## Dependencies

Within module:
- Requires: shared_001

## Notes

`deploy` is a stub that builds artifacts; cross-platform installers are produced by
`infra_003` via GitHub Actions on tag. The 85% bar applies to all future modules/stories.
