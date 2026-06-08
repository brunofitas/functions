# infra_003: Cross-platform installers (GitHub Releases / Actions)

**Status:** DONE  · _built 2026-06-08 (release.yml + install.sh; native packaging is follow-up)_
**Mode:** BUILD
**Module:** infra_
**Created:** 2026-06-08
**Layer:** 5

## Context

`functions` ships as an open-source desktop app for macOS, Linux, and Windows. Users
should install from a GitHub Release, not build from source. The CI skeleton from
`shared_001` grows into a real release pipeline.

## Goal

A GitHub Actions release workflow that, on a tagged version, builds installable artifacts
for the three platforms (GUI + bundled orchestrator), checks Docker availability at
launch, and publishes them to a GitHub Release.

## Approach

**Recommendation:** matrix build on macOS/Linux/Windows runners; package the desktop app
(GUI + `be_` orchestrator); attach artifacts to the Release on tag push. App verifies
Docker presence and guides setup if missing.

**Reasoning:** Standard OSS distribution; no hosted infra needed.

## Acceptance Criteria

- [ ] Tagged push triggers a release build on all three OSes
- [ ] Installable artifact per platform, attached to the GitHub Release
- [ ] App bundles/starts the orchestrator and checks for Docker on launch
- [ ] Install + first-run documented in the README

## Output

_Filled after implementation._

## Dependencies

Within module: —

Cross-module:
- Requires: fe_005 (GUI complete), be_013 (orchestrator complete)
