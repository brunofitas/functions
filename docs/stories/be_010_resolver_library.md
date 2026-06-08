# be_010: Reference resolver, namespacing & library cache

**Status:** DONE  · _built 2026-06-08 (resolver/cache/index, archive fetch)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 3

## Context

Functions come from disk, public GitHub, or a URL. To be shareable/reproducible they're
installed into a local library cache and addressed by namespace. This is what turns
"point at a folder" into "install `aws/login@1.0` from GitHub".

## Goal

A resolver that takes any reference form, fetches/installs the function into
`.lib/cache/<namespace>/<name>@<version>/`, and exposes a searchable/filterable index of
installed functions. Idempotent and offline after install.

## Approach

**Recommendation:** `resolve(ref)` dispatching by the contract's reference grammar
(`shared_003`); GitHub/URL fetch → verify manifest → cache; an index over the cache for
search/filter by namespace/name/runtime.

**Reasoning:** Additive over the local loader so the M0 slice never depends on it.

## Acceptance Criteria

- [ ] Resolves all five reference forms
- [ ] Installs to the versioned library cache; idempotent
- [ ] Searchable/filterable index of installed functions
- [ ] Works offline once cached

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: shared_003
- Blocks: —

Cross-module:
- Requires: infra_001 (sealed) — cache is the mounted `/lib` volume
- Blocks: fe_002 (browser)
