# shared_001: Project scaffold (monorepo, packaging, CI bootstrap)

**Status:** DONE
**Mode:** BUILD
**Module:** shared_
**Created:** 2026-06-08
**Layer:** 0

> **DONE 2026-06-08** — `src/` monorepo scaffolded; `make setup/test/lint` green
> (2 smoke tests pass, ruff clean, fe typecheck clean); CI workflow + MIT license +
> README in place; git initialized locally (not committed yet).

## Context

`functions` is a multi-module project (`shared_`, `be_`, `fe_`, `infra_`). Before any
feature work, the repo needs a structure everything else lands in: the monorepo layout,
per-module packaging, and a CI skeleton (the same GitHub Actions that will later build
release installers). This is the foundation every other story depends on.

## Goal

A `brunofitas/functions` repo with: a monorepo layout (`functions_shared`,
`functions_be`, `functions_fe` packages + an `infra/` area), each module independently
installable, a root README, license (MIT), and a GitHub Actions workflow that lints +
tests all modules on push.

## Approach

**Recommendation:** Python (asyncio) packages for `shared_`/`be_` with `pyproject.toml`
per module; TypeScript app for `fe_`. Root `Makefile` orchestrates `setup`/`test`/`lint`.
CI runs the matrix on macOS/Linux/Windows.

**Reasoning:** Matches the prototype and the eventing direction; per-module packaging
keeps boundaries clean and enables the later installer pipeline (`infra_003`).

## Acceptance Criteria

- [ ] Monorepo layout with `functions_shared`, `functions_be`, `functions_fe`, `infra/`
- [ ] Each Python module has its own `pyproject.toml` and installs independently
- [ ] Root `Makefile`: `setup`, `test`, `lint`
- [ ] GitHub Actions workflow lints + tests all modules on push (3 OSes)
- [ ] MIT `LICENSE`, root `README.md`

## Output

- `src/functions_shared/` — `pyproject.toml`, `functions_shared/__init__.py`, `tests/`, `README.md`
- `src/functions_be/` — `pyproject.toml`, `functions_be/__init__.py`, `tests/`, `README.md`
- `src/functions_fe/` — `package.json`, `tsconfig.json`, `src/index.ts`, `README.md`
- `infra/README.md`
- `.github/workflows/ci.yml` (Python matrix on 3 OSes + fe typecheck)
- `Makefile` (`setup`/`test`/`lint`), `README.md`, `LICENSE` (MIT), `.gitignore`

## Dependencies

Within module:
- Blocks: shared_002, shared_003

Cross-module:
- Blocks: all (the scaffold everything lands in)

## Notes

VISION.md and intake.md move into the new repo under `docs/`. Keep the `.bk/` prototype
as reference until the engine slice supersedes it.
