# be_003: Function sandbox & permission posture

**Status:** DONE  · _built 2026-06-08 (functions_be.sandbox)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 1

## Context

Functions are third-party code that runs with file/secret access. Unattended runs need a
non-interactive permission mode (`bypassPermissions`), but that must be bounded by the
Docker sandbox. Formal provenance/signing is deferred to the marketplace milestone; this
story sets the v1 posture.

## Goal

A defined, implemented permission posture: claude steps run with a non-interactive mode
inside the container; the container is the trust boundary (no host filesystem beyond
mounted volumes); a clear, documented statement of what an installed function can and
cannot reach.

## Approach

**Recommendation:** run claude steps with `--permission-mode bypassPermissions` *only
inside* the container, with `/work` + `/lib` as the only writable mounts and secrets
scoped per `be_002`. Document the trust model in the README.

**Reasoning:** Pragmatic for a personal OSS tool; the sandbox bounds the blast radius
without a full provenance system.

## Acceptance Criteria

- [ ] Non-interactive permission mode wired for in-container claude steps
- [ ] Container mounts limited to `/work`, `/lib`, session store
- [ ] Documented trust model (what a function can/can't reach)
- [ ] Provenance explicitly noted as deferred

## Output

_Filled after implementation._

## Dependencies

Within module:
- Blocks: be_005, be_006

Cross-module:
- Requires: infra_001 (sealed)
