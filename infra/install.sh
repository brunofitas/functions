#!/usr/bin/env sh
# functions — local installer (infra_003).
# Installs the orchestrator (Python) from a release tarball's wheels, or from source.
# Requires Docker (the runtime sandbox) and a Claude CLI login (subscription plan).
set -e

echo "Installing functions…"

if ls ./dist/*.whl >/dev/null 2>&1; then
  python3 -m pip install --user ./dist/functions_shared-*.whl ./dist/functions_be-*.whl
else
  echo "No release wheels found — installing from source."
  python3 -m pip install --user ./src/functions_shared ./src/functions_be
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "WARNING: Docker not found. functions runs pipelines inside Docker — install it:"
  echo "  https://docs.docker.com/get-docker/"
fi

echo "Done. Ensure you are logged in to the Claude CLI (subscription plan)."
echo "See README.md to launch the orchestrator + Studio."
