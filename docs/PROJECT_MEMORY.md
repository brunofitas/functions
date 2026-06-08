# Project Memory — functions

> In-repo memory so context travels with the code. (Claude Code's own memory is keyed
> by absolute path and does **not** follow a folder rename — this file is the source of
> truth.) Maintained alongside the ai-sprint docs in this folder.

## What this is

**functions** — an open-source, local desktop app that chains units of work (**functions**)
into **pipelines** and runs them on Docker. A function has a pluggable **runtime**
(`bash`, `python`, `claude`, `custom`); a pipeline *is* a function (recursive). LLM steps
share one Claude session, so memory carries across functions — the core differentiator.
Auth uses the **Claude CLI subscription plan** (no API key in v1); `plain` runtimes cost
nothing. Built with the [ai-sprint](https://github.com/brunofitas/ai-sprint) workflow.

## Current state (2026-06-08)

- **25/25 ai-sprint stories DONE** (4 design gates sealed; engine + adapters + resolver +
  API + lifecycle + GUI view-models + infra). Verified end-to-end **in real Docker**,
  including a two-step `claude` pipeline sharing one session (`remember`→`recall` → "BANANA").
- **Tests:** 96 Python (≈96% cov) + 20 frontend (≈99% cov); ruff + tsc clean; ≥85% gate enforced.
- **Runs locally:** `python -m functions_be --base-dir examples --gui [--docker|--claude]` →
  Studio at http://127.0.0.1:8799.
- **Local commits (unpushed):** scaffold → engine → Docker exec + `/lib` bugfix → live
  claude → Studio app → Docker-from-GUI → container-teardown fix.

### Honest gaps (the "missing stories" — backlog NOT yet updated)
- GUI is a **demo shell**: only the function list + run console are rendered. The
  `editor`/`creator`/`settings` view-models are tested but **not wired into screens**.
- **No API endpoints** for install / settings-persistence / function-test (capabilities
  exist; routes don't) — so `fe_002`/`fe_004`/`fe_005` aren't usable end-to-end.
- **No combined base image** (python+node+claude): Docker mode uses `python:3.12-slim`
  (no claude); `--claude` uses `claude-docker` (no python3) → can't mix in Docker.
- Deferred optimizations: warm-container / `docker commit` snapshot; stream-json de-dup
  (claude answers print twice); native installers + an actual release.
- **Deferred by design** (intake §5/§7): `openai` runtime, API-key auth, DAG/parallel,
  hosted marketplace/publishing, enterprise auth, cross-container memory.

## Sealed decisions (see `docs/decisions/`)

- **d_001 contract** — single YAML manifest `kind: function|pipeline`; runtime-adapter
  interface (`provision`/`execute`/`collect` + caps `is_llm`/`memory`); ref grammar
  (pinned registry/github/url, unpinned `./`/abs); I/O = JSON files `$FN_INPUTS`/
  `$FN_OUTPUTS` + `$INPUT_*` env mirror; **outputs ALWAYS strict**; `exports` opt-in.
- **d_be_002 eventing** — asyncio-native (async generators + `anyio` + `aiostream`), no
  RxPY; `Event` tagged union; pause = run-gate backpressure; END = sentinel.
- **d_be_001 secrets** — encrypted local vault (age/sops) → env injection,
  **least-privilege** (only declared), masked; precedence per-step > global > bus.
- **d_infra_001 container** — shared base on claude-docker; runtime provisioning from
  pinned deps; **fresh-per-run container + shared dep-cache**; CLI over `docker exec`;
  recreate-on-missing; snapshot deferred.

## Architecture

`shared_` (`functions_shared`) contract spine → `be_` (`functions_be`) orchestrator
(engine, adapters, resolver/library, env/secrets, lifecycle, loopback API + WS + token) →
`fe_` (`functions_fe`) TypeScript Studio (view-models + API client + thin DOM). `infra/`
= base Dockerfile + ContainerManager + GitHub-Releases CI. No dependency cycles.

## Hard-won gotchas (DON'T re-learn these)

1. **Claude sessions are per-directory.** A session created in `A/` can't resume from
   `B/`. Run every step from one fixed root (`/work`); reach functions via `--add-dir`.
2. **Never bind-mount the function library at `/lib`** — it shadows the container's libc
   + dynamic loader (`exec sleep: no such file or directory`). Use `/srv/functions`.
3. **Tear down per-run containers in a `finally`** — else they leak (one per run, forever).
4. **`--session-id` needs a real UUID**; "session"/"claude" are rejected.
5. **Don't mount host `~/.claude` for the `claude` runtime** — the container keeps its own
   session store; the `CLAUDE_CODE_OAUTH_TOKEN` env is enough for headless `claude -p`.
6. **Run the pipeline inside the WS handler**, not a detached `asyncio.create_task`
   (orphaned by TestClient's per-request loop).
7. **Coerce `version`/`apiVersion` to str** — YAML parses `1.0` as a float.
8. **Docker container path mapping**: the engine addresses files workspace-relative; the
   `Container` maps host writes ↔ in-container paths (functions copied to `/work/.fn`).
9. **claude-docker image**: `claude-docker:latest`, `ENTRYPOINT claude-wrapper` → override
   with `--entrypoint sleep`; token from macOS Keychain
   (`security find-generic-password -s "Claude Code-credentials" -w` → `.claudeAiOauth.accessToken`).

## Run / develop

```bash
make setup                                          # shared root .venv + modules + fe deps
(cd src/functions_fe && npm run build)              # esbuild bundle the Studio
make test    # 96 py + 20 fe, ≥85% gate
make lint    # ruff + tsc
python -m functions_be --base-dir examples --gui            # host runtime
python -m functions_be --base-dir examples --gui --docker   # runs in Docker (python:3.12-slim)
python -m functions_be --base-dir examples --gui --claude   # claude-docker + keychain token
```

## Next (proposed new stories)

`fe_006` wire editor/creator/settings screens · `be_014` install/settings/test API
endpoints · `infra_004` combined python+node+claude image · `infra_005` warm-container/
snapshot · `be_015` stream-json de-dup · `infra_006` native installers + first release.
Recommended order to make the GUI usable: `be_014` → `fe_006`.
