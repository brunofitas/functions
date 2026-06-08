# d_001: Function/pipeline contract + runtime-adapter interface

**Status:** SEALED
**Date:** 2026-06-08
**Story:** shared_002
**Scope:** project-wide (the spine `be_`, `fe_`, and all functions build against)

## Context

`functions` needs one contract that the orchestrator, the GUI, and every authored
function agree on, without coupling them. It must support pluggable runtimes, structured
data flow between steps, recursive composition (a pipeline is a function), and remote
sources — while staying minimal and additive so new runtimes never force a contract
change. Two genuine forks (output validation strictness; I/O transport) were decided by
the maintainer in the Design Gate.

## Decision

### 1. Manifest — single YAML file, `kind: function | pipeline`

```yaml
apiVersion: functions/v1
kind: function                  # or: pipeline
namespace: aws
name: login
version: 0.1.0                  # semver
description: Authenticate to AWS; export session credentials downstream.
runtime: claude                 # bash | python | claude | custom
entrypoint: prompt.md           # optional; defaults per runtime (run.sh/main.py/prompt.md; custom→Makefile)
dependencies:
  system: [awscli]              # apt   (bash / custom)
  python: [boto3==1.34.*]       # pip   (python / custom) — PINNED
requirements:
  secrets:      [{ name: AWS_ACCESS_KEY_ID }, { name: AWS_SECRET_ACCESS_KEY }]
  environment:  [{ name: AWS_REGION, default: eu-west-1 }]
  inputs:       [{ name: role_arn, type: string, required: false, default: null }]
outputs:        [{ name: account_id, type: string }]
exports:        [AWS_PROFILE]   # env exported to later steps — OPT-IN (see be_002)
storage:        [{ path: .cache/aws }]
events:         { emits: [ready, error], listens: [end] }
i18n: ./i18n
```

Pipeline manifest (same envelope; `kind: pipeline`):

```yaml
apiVersion: functions/v1
kind: pipeline
namespace: acme
name: deploy
version: 1.0.0
requirements: { secrets: [...], environment: [...], inputs: [...] }   # pipelines ARE functions
outputs: [...]
steps:
  - id: login
    use: aws/login@0.1.0
    with: { role_arn: "${{ secrets.DEPLOY_ROLE }}" }
  - id: audit
    use: ./functions/s3-audit
    with: { account_id: "${{ steps.login.outputs.account_id }}" }
flow:
  mode: standalone              # standalone | streaming
  end:  { signal: END }
```

`input` types: `string | number | boolean | object | array`. Wiring expressions
`${{ … }}` may reference `steps.<id>.outputs.<name>`, `secrets.<NAME>`, `env.<NAME>`,
and `inputs.<name>` (the pipeline's own inputs).

### 2. Reference grammar (`use:`)

| Form | Example | Pinned? |
|------|---------|---------|
| registry/library | `aws/login@0.1.0` | yes |
| pipeline-relative | `./functions/s3-audit` | no (dev) |
| absolute | `/abs/path/fn` | no |
| GitHub | `github:owner/repo/subdir@ref` | yes (by ref) |
| URL archive | `https://….tar.gz` | yes (by URL) |

Registry/GitHub/URL refs are reproducible; `./` and `/abs` are unpinned for local dev.

### 3. Runtime-adapter interface

```python
@dataclass
class Capabilities:
    is_llm: bool                       # costs tokens, non-deterministic
    memory: Literal["none","session","history"]
    default_entrypoint: str            # e.g. "main.py"
    dep_kinds: list[str]               # e.g. ["python"], ["system"]

class RuntimeAdapter(Protocol):
    runtime: str
    capabilities: Capabilities
    async def provision(self, fn: Function, container: Container) -> None   # idempotent deps
    def     execute(self, step: Step, ctx: RunContext) -> AsyncIterator[Event]
    async def collect(self, ctx: RunContext) -> dict                        # validated outputs
```

`Event` = `{ kind: "text"|"tool"|"status"|"error"|"end", ... }`. `onComplete` ≙ `end`.
The engine reads `capabilities` to decide cost accounting and whether the step joins the
shared Claude session (`memory == "session"`). New runtimes register by providing an
adapter; **no core changes**.

### 4. I/O transport — JSON files + env mirror  *(decided: "JSON files + env mirror")*

- Orchestrator writes resolved inputs as JSON to a path in **`$FN_INPUTS`** (read-only),
  and mirrors each scalar input as **`$INPUT_<NAME>`** for ergonomic bash use.
- The function writes its outputs as JSON to **`$FN_OUTPUTS`**.
- Nested/typed data travels via the JSON files; the env mirror is convenience only.

```bash
# bash
ROLE="$INPUT_ROLE_ARN"
jq -n --arg id "$ACCT" '{account_id:$id}' > "$FN_OUTPUTS"
```
```python
# python
import json, os
inp = json.load(open(os.environ["FN_INPUTS"]))
json.dump({"account_id": acct}, open(os.environ["FN_OUTPUTS"], "w"))
```

### 5. Output validation — ALWAYS STRICT  *(decided: "Always strict")*

After each step, produced outputs are validated against the manifest's `outputs`. A
**missing or type-mismatched** declared output **fails the step** — no per-function
opt-out. Rationale: downstream `${{ steps.X.outputs.Y }}` wiring must be trustworthy;
silent contract drift is the failure mode we most want to prevent.

### 6. Other sealed points

- **Single manifest, recursive:** a pipeline is a function (`kind: pipeline`); pipelines
  compose pipelines with no special case.
- **`exports` is opt-in:** env only leaks downstream when a function declares it — the
  least-privilege default that `be_002` builds on.
- **Manifest format = YAML** (over TOML/JSON): comments + the GH-Actions idiom.

## Options considered

- **Output validation:** *always strict* (chosen) vs. strict-with-per-function-override
  vs. lenient/warn. Chose always-strict for reliability; the cost is slightly stricter
  authoring, accepted.
- **I/O transport:** *JSON files + env mirror* (chosen) vs. env-only (rejected:
  string/flat only) vs. JSON-files-only (rejected: `jq` boilerplate for every bash input).
- **Manifest format:** YAML (chosen) vs. TOML vs. JSON.
- **One vs. two manifest kinds:** one envelope with `kind:` (chosen) for recursive
  composition.

## Consequences

- `shared_003` implements exactly this (models, `parse_ref`, strict `validate_outputs`,
  the `$FN_INPUTS`/`$FN_OUTPUTS`/`$INPUT_*` convention).
- Adapters (`be_004`–`be_006`) implement the interface; the engine (`be_001`) reads
  `capabilities`.
- `be_002` refines `secrets`/`exports` scoping; `be_012` defines the concrete `Event`
  stream type; `infra_001` consumes `dependencies` for provisioning.
- Authoring is slightly stricter (must produce declared outputs), and bash functions
  read `$INPUT_*` / write `$FN_OUTPUTS`.

## Affected stories

Unblocks: `shared_003`, `be_002`, `be_012`, `infra_001`. Constrains: `be_001`, `be_004`–
`be_007`, `be_010`, `fe_003`, `fe_004`.
