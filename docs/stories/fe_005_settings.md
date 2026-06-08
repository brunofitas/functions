# fe_005: Settings (env / secrets / folders)

**Status:** DONE  · _built 2026-06-08 (SettingsModel: env/secrets/folders, secret-safe)_
**Mode:** BUILD
**Module:** fe_
**Created:** 2026-06-08
**Layer:** 4

## Context

Global configuration the orchestrator needs: environment variables, secrets, and the
folders/workspaces functions operate on. Secrets are entered here but held by the
orchestrator — the GUI never stores them.

## Goal

A settings surface to manage global environment variables, secrets (write-only into the
orchestrator's store, masked on display), and folders/workspaces — all via the
authenticated API, per the sealed secrets model (`be_002`).

## Approach

**Recommendation:** forms that POST to the orchestrator; secret values are write-only and
shown masked; folder pickers register workspaces. No secret ever persisted in GUI state.

**Reasoning:** Keeps the GUI secret-free; the orchestrator remains the only trust
boundary.

## Acceptance Criteria

- [ ] Manage global env vars
- [ ] Add/update secrets (write-only, masked, stored by orchestrator)
- [ ] Manage folders/workspaces
- [ ] GUI holds no secret values in state or storage

## Output

_Filled after implementation._

## Dependencies

Cross-module:
- Requires: be_002 (sealed), be_011
