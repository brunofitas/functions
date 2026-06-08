# functions — root orchestration for the whole monorepo.
#
#   make setup      shared root .venv + all Python modules (editable) + dev deps; fe deps
#   make test       run EVERYTHING with coverage gates (Python ≥85%, frontend ≥85%)
#   make lint       ruff (Python) + tsc typecheck (frontend)
#   make build      build Python wheels + frontend bundle
#   make deploy     build, then produce release artifacts (installers via infra_003 CI)
#   make coverage   tests + coverage reports (alias of test)
#   make clean      remove venv, caches, build output
#
# One shared .venv at the repo root drives both Python modules. Coverage minimum is
# enforced (see pytest.ini and src/functions_fe/vitest.config.ts) — builds fail below 85%.

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip
FE   := src/functions_fe
HAVE_NPM := $(shell command -v npm 2>/dev/null)

setup:
	python3 -m venv $(VENV)
	$(PIP) install -q -U pip build
	$(PIP) install -q -e "src/functions_shared[dev]"   # shared first (be depends on it)
	$(PIP) install -q -e "src/functions_be[dev]"
ifneq ($(HAVE_NPM),)
	cd $(FE) && npm install --silent
else
	@echo "note: npm not found — skipping frontend deps"
endif
	@echo "✓ setup complete"

test: test-py test-fe
test-py:
	$(VENV)/bin/pytest    # config + coverage gate in pytest.ini (≥85%)
test-fe:
ifneq ($(HAVE_NPM),)
	cd $(FE) && npm test  # vitest run --coverage (≥85% gate)
else
	@echo "note: npm not found — skipping frontend tests"
endif

coverage: test

lint:
	$(VENV)/bin/ruff check src/functions_shared src/functions_be
ifneq ($(HAVE_NPM),)
	cd $(FE) && npm run typecheck
endif

build:
	rm -rf dist && mkdir -p dist
	$(PY) -m build -o dist src/functions_shared
	$(PY) -m build -o dist src/functions_be
ifneq ($(HAVE_NPM),)
	cd $(FE) && npm run build
endif
	@echo "✓ build artifacts in dist/ and $(FE)/dist/"

deploy: build
	@echo "deploy: cross-platform installers are produced by GitHub Actions on a tag"
	@echo "        (story infra_003). Local 'build' artifacts are the inputs."

clean:
	rm -rf $(VENV) dist .pytest_cache .ruff_cache .coverage htmlcov
	find src -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(FE)/node_modules $(FE)/dist $(FE)/coverage

.PHONY: setup test test-py test-fe coverage lint build deploy clean
