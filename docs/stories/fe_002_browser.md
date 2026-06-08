# fe_002: Function & pipeline browser

**Status:** DONE  · _built 2026-06-08 (FunctionBrowser: load + search/filter)_
**Mode:** BUILD
**Module:** fe_
**Created:** 2026-06-08
**Layer:** 3

## Context

Users need to find functions — local and installable — to run and to drag into the
editor. The browser is the sidebar that the editor (`fe_003`) drags from.

## Goal

A searchable, filterable list of functions and pipelines by namespace/name/runtime,
showing local + installed items, with an "install from GitHub/disk/URL" action and a
detail view (README, manifest summary).

## Approach

**Recommendation:** read the resolver/library index via the API (`be_010`); filter
client-side; install triggers the resolver.

**Reasoning:** Thin view over the orchestrator's index; no logic duplicated.

## Acceptance Criteria

- [ ] Lists local + installed functions/pipelines
- [ ] Search + filter by namespace/name/runtime
- [ ] Install from GitHub/disk/URL
- [ ] Detail view (README + manifest summary)

## Output

_Filled after implementation._

## Dependencies

Cross-module:
- Requires: be_010, be_011
- Blocks: fe_003
