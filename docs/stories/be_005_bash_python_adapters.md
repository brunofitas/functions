# be_005: Deterministic adapters — bash + python

**Status:** DONE  · _built 2026-06-08 (Bash/Python adapters)_
**Mode:** BUILD
**Module:** be_
**Created:** 2026-06-08
**Layer:** 2

## Context

The non-LLM runtimes that make pipelines cheap and deterministic. They run a function's
entrypoint as a subprocess in the container, sharing workspace/env/secrets/I/O but no
Claude memory.

## Goal

Two adapters implementing the sealed adapter interface: `bash` (runs `run.sh`, apt deps)
and `python` (runs `main.py`, pip deps). Both provision declared deps, execute with
injected inputs/env, stream stdout/stderr as events, and collect declared outputs.

## Approach

**Recommendation:** a shared `SubprocessAdapter` base (capabilities `is_llm=False`,
`memory=none`); `bash`/`python` differ only in entrypoint + dependency kind. Stream via
async subprocess (per `be_012`).

**Reasoning:** Most of the behaviour is shared; the split is just entrypoint + deps.

## Acceptance Criteria

- [ ] `bash` adapter runs `run.sh`, installs apt deps, streams output, collects outputs
- [ ] `python` adapter runs `main.py`, installs pip deps, same contract
- [ ] Inputs/env injected per the contract; outputs validated
- [ ] `is_llm=False`, no session usage
- [ ] Tests: a bash and a python function each run and return outputs

## Output

_Filled after implementation._

## Dependencies

Within module:
- Requires: be_004, be_003
- Blocks: be_009
