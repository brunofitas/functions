# functions

> Open-source, local desktop app that chains units of work — **functions** — into
> **pipelines**, running them on Docker. A function has a pluggable runtime (`bash`,
> `python`, `claude`, …); a pipeline is itself a function. You only pay the Claude plan
> on the steps that need an LLM.

**Status:** early development (scaffold). Built with the
[ai-sprint](https://github.com/brunofitas/ai-sprint) workflow — see `docs/`.

## Layout

```
src/
  functions_shared/   contract: manifest schema, runtime-adapter interface, types
  functions_be/       orchestrator: engine, adapters, resolver, lifecycle, API
  functions_fe/        studio GUI (TypeScript)
infra/                container runtime + packaging
docs/                 VISION, intake, architecture, STATUS, stories, decisions
```

## Develop

```bash
make setup   # venv + install all modules (editable) + dev deps
make test    # run all tests
make lint    # lint / typecheck
```

## Design

- Vision: [`docs/VISION.md`](docs/VISION.md) · Requirements: [`docs/intake.md`](docs/intake.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md) · Backlog: [`docs/STATUS.md`](docs/STATUS.md)
- Sealed decisions: [`docs/decisions/`](docs/decisions/)

## License

MIT © Bruno Fitas
