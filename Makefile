# functions — root orchestration for the whole monorepo.
#
#   make setup      shared root .venv + all Python modules (editable) + dev deps; fe deps
#   make test       run EVERYTHING with coverage gates (Python ≥85%, frontend ≥85%)
#   make lint       ruff (Python) + tsc typecheck (frontend)
#   make app        RUN the native desktop app (Electron) ← what you want to "see it"
#   make studio     RUN the web Studio (orchestrator serves the GUI in your browser)
#   make build      build Python wheels + frontend bundle
#   make deploy     build only — does NOT launch the app; CI produces installers
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

# RUN the native desktop app (Electron spawns the orchestrator + opens a window).
app:
	cd $(FE) && npm run app

# RUN the web Studio: orchestrator serves the GUI; then open http://127.0.0.1:8799
studio:
	$(PY) -m functions_be --base-dir examples --gui

deploy: build
	@echo "NOTE: 'deploy' only BUILDS — it does not launch the app."
	@echo "      To SEE the app run:  make app   (desktop)   or   make studio   (browser)"
	@echo "      Cross-platform installers are produced by CI on merge to main (infra_006)."

clean:
	rm -rf $(VENV) dist dist-app .pytest_cache .ruff_cache .coverage htmlcov
	find src -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(FE)/node_modules $(FE)/dist $(FE)/coverage

.PHONY: setup test test-py test-fe coverage lint build app studio deploy clean
