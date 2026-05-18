#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! "$PYTHON_BIN" -m pytest --version >/dev/null 2>&1; then
  if [ ! -x ".venv/bin/python" ]; then
    "$PYTHON_BIN" -m venv .venv
  fi

  PYTHON_BIN=".venv/bin/python"
  "$PYTHON_BIN" -m pip install --upgrade pip >/dev/null
  "$PYTHON_BIN" -m pip install -r requirements-dev.txt >/dev/null
fi

"$PYTHON_BIN" -m pytest "$@"
