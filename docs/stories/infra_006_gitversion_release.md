# infra_006: GitVersion auto-tag + multi-OS release

**Status:** IN_PROGRESS  · _config written; runs/validates on push to main_
**Mode:** BUILD
**Module:** infra_
**Created:** 2026-06-08
**Layer:** 5

## Context
Releases should be automatic: merge to main → compute SemVer (start 0.0.1, default patch
bump) → tag → build self-contained apps for mac/linux/windows → publish a GitHub Release.

## Goal
`GitVersion.yml` + a `release` workflow that, on push to main, tags `vX.Y.Z` and builds +
publishes per-OS installers (Electron + bundled PyInstaller orchestrator) to a Release.

## Approach
`gittools/actions` (GitVersion 6.x) computes `majorMinorPatch`; a `version` job tags;
a matrix `build` job freezes the orchestrator (PyInstaller), bundles the Studio, and runs
`electron-builder --publish always` with the version injected via `-c.extraMetadata`.

## Acceptance Criteria
- [x] `GitVersion.yml`: next-version 0.0.1, default Patch, +semver major/minor/patch strings
- [x] Workflow: push main → GitVersion → tag vX.Y.Z → matrix build → publish Release
- [ ] **Verified on GitHub** (requires the repo pushed to brunofitas/functions)

## Output
- `GitVersion.yml`, `.github/workflows/release.yml`

## Notes
Validation requires pushing to GitHub (outward-facing) — pending the maintainer's go.
First merge to main publishes **v0.0.1**.
