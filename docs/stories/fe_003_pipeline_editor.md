# fe_003: Drag-and-drop pipeline editor

**Status:** DONE  · _built 2026-06-08 (PipelineEditor: add/reorder/wire/validate/manifest)_
**Mode:** BUILD
**Module:** fe_
**Created:** 2026-06-08
**Layer:** 3

## Context

The headline GUI feature: build a pipeline visually by dragging functions from the
browser and wiring outputs to inputs. v1 is linear chains (DAGs deferred), which keeps
the editor simple and honest about the execution model.

## Goal

An editor where you drag functions from the sidebar into an ordered chain, set each
step's `with:` inputs (wired from prior outputs or literals/secrets), and save a valid
pipeline manifest that the orchestrator can run.

## Approach

**Recommendation:** a linear step list (not a free-form graph) reflecting sequential
execution; input wiring via dropdowns of upstream outputs; validate against the contract
(`shared_003`) before save.

**Reasoning:** Matches the sealed sequential model; avoids implying DAG support we don't
have yet.

## Acceptance Criteria

- [ ] Drag functions from the browser into an ordered chain
- [ ] Wire each step's inputs from upstream outputs / literals / secrets
- [ ] Live validation against the contract
- [ ] Saves a runnable pipeline manifest

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: fe_002

Cross-module:
- Requires: shared_003
