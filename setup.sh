#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== HMS setup ==="

# Backend deps (uv + .venv)
cd "$ROOT_DIR/server"
if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed. Install uv first."
  exit 1
fi
uv sync

# Frontend deps (bun preferred, npm fallback)
cd "$ROOT_DIR/frontend"
if command -v bun >/dev/null 2>&1; then
  bun install
else
  bun install
fi

echo "Setup complete."