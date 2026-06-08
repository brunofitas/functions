# be_013: Lifecycle — pause/wait + streaming END

**Status:** DONE  · _built 2026-06-08 (RunControl pause/resume/cancel + END, wired to API)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 4

## Context

Pipelines aren't always fire-and-forget. They can pause and wait (for a human or a
condition), and a streaming pipeline runs until an `END` signal propagates downstream so
functions shut down gracefully (drain, not kill). This is the control plane over the
runner.

## Goal

Lifecycle control on a running pipeline: pause/resume; wait satisfied manually (via the
API) or by a condition over prior outputs/events; streaming mode that keeps the pipeline
live and re-triggerable; and an `END` signal that propagates so each step that listens
shuts down cleanly.

## Approach

**Recommendation:** model lifecycle on the sealed `be_012` substrate — pause as
backpressure, END as completion propagated to `listens:[end]` functions; conditions
evaluated against collected outputs/events.

**Reasoning:** Falls out naturally if the substrate is chosen well.

## Acceptance Criteria

- [ ] Pause/resume on a live run
- [ ] Wait satisfied manually and by a condition expression
- [ ] Streaming mode: pipeline stays live, re-triggerable with new context
- [ ] `END` propagates downstream; listeners drain and stop cleanly
- [ ] Test: a streaming pipeline drains on END without abrupt kill

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: be_009, be_011, be_012 (sealed)

Cross-module:
- Blocks: fe_001 (pause/end controls), infra_003
