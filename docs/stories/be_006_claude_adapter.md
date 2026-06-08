# be_006: claude adapter (CLI over docker exec, session resume)

**Status:** DONE  · _built 2026-06-08 (ClaudeAdapter, session-sharing verified)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 2

## Context

The LLM runtime — and the one that carries shared memory across steps. It runs a
function's `prompt.md` inside a Claude Code session in the container, resuming the
pipeline's shared session so step B inherits step A's reasoning (the proven mechanic).

## Goal

A `claude` adapter implementing the interface with `is_llm=True`, `memory=session`: it
invokes the Claude Code CLI over `docker exec` (`claude -p`, `--output-format
stream-json`, `--add-dir <function>`, `--session-id`/`--resume` supplied by the engine),
streams events, and collects outputs.

## Approach

**Recommendation:** thin wrapper around `docker exec claude -p …`, parsing stream-json
into adapter events (text / tool / result). The engine owns the session id; the adapter
just uses it.

**Reasoning:** Directly productizes the validated prototype path.

## Acceptance Criteria

- [ ] Runs a claude function via CLI over `docker exec`, streaming stream-json
- [ ] Honors the engine-supplied session id (create vs resume)
- [ ] `--add-dir` targets the function folder; runs from the fixed root
- [ ] Capabilities `is_llm=True`, `memory=session`
- [ ] Test: two claude steps share memory in one pipeline

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: be_004, be_003
- Blocks: be_009

Cross-module:
- Requires: infra_001 (sealed) — control channel
