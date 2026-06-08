# d_be_001: Secret scoping & environment bus

**Status:** SEALED
**Date:** 2026-06-08
**Story:** be_002
**Scope:** be_ (consumed by env/secrets injection, settings, all step execution)

## Context

Functions declare `secrets`, an `environment`, and an opt-in `exports` list (sealed in
`d_001`). The env bus lets a step export env downstream — the mechanic behind "function A
logs into AWS, function B reuses it" — which deliberately leaks credentials and so must
be bounded. This gate decides storage at rest, injection, scoping, and masking.

## Decision

### 1. Storage at rest — encrypted local vault

Secrets live in a single **cross-platform encrypted vault** (`~/.functions/secrets.age`,
age/sops-style), unlocked by one master key. Identical behavior on macOS/Linux/Windows,
portable, backup-able, and headless/CI-friendly — chosen over per-OS keychains (3 code
paths, container/headless friction) and plaintext `.env` (no encryption at rest).

### 2. Injection — env vars, scoped + masked

Declared secrets are injected as **environment variables** into the step's container
(`docker exec -e NAME=…`), because that's what `aws`, `gcloud`, and most SDKs read
natively. The **container is the trust boundary**; values are **masked** in all logs and
streamed `Event`s. (Within the sandbox they're visible via `/proc`/`docker inspect` —
accepted for a local single-user tool.)

### 3. Least-privilege scoping

A function receives **only the secrets it declares** in `requirements.secrets` — never
the whole vault. Undeclared secrets are never injected.

### 4. Environment bus & precedence

- A step exports env downstream **only** via its manifest `exports` list (opt-in leak).
- Effective env for a step = **per-step `with:` > global environment > running export
  bus** (later wins on the left).
- The bus is held by the orchestrator and threaded through the sequential run; it lives
  only for the duration of the pipeline run.

### 5. Masking

A redaction filter over every emitted `Event` and log line replaces known secret values
with `••••`. Applied centrally so no surface can leak them.

## Options considered

- **Store:** encrypted vault (chosen) vs. OS keychain (rejected: 3 platforms + headless
  friction) vs. `.env` plaintext (rejected: not encrypted).
- **Injection:** env scoped+masked (chosen, tool-compatible) vs. tmpfs files + opt-in env
  (safer but more plumbing; revisit if a hardening pass is wanted) vs. all-available
  (rejected: violates least privilege).

## Consequences

- `be_008` implements the `EnvBus`, vault read, scoped env injection, and the masking
  filter.
- `fe_005` (settings) writes secrets into the vault write-only (masked on display).
- Rotation / revocation / audit are **out of scope** (enterprise, dropped in intake).
- A future "tmpfs injection" hardening option remains open without contract changes.

## Affected stories

Unblocks toward: `be_008`, `fe_005`.
