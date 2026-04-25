#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDS=""

require_cmd() {
  local cmd="$1"
  local hint="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: '$cmd' is not installed. $hint"
    exit 1
  fi
}

track_pid() {
  local pid="$1"
  PIDS="$PIDS $pid"
}

start_if_not_running() {
  local process_name="$1"
  local cmd_name="$2"
  local start_cmd="$3"
  local hint="$4"

  if pgrep -x "$process_name" >/dev/null 2>&1; then
    echo "$process_name is already running."
    return
  fi

  require_cmd "$cmd_name" "$hint"
  eval "$start_cmd" &
  track_pid "$!"
  echo "Started $process_name."
}

cleanup() {
  echo ""
  echo "Stopping services..."
  for pid in $PIDS; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "=== Starting HMS services ==="
echo "API: http://127.0.0.1:5000"
echo "Mailpit UI: http://127.0.0.1:8025"
echo "Redis: localhost:6379"

require_cmd "uv" "Install from https://docs.astral.sh/uv/getting-started/installation/"

# Infrastructure services
start_if_not_running "redis-server" "redis-server" "redis-server" "Install Redis (macOS: brew install redis)"
start_if_not_running "mailpit" "mailpit" "mailpit" "Install Mailpit (macOS: brew install mailpit)"

# Backend API
cd "$ROOT_DIR/server"
uv run python app.py &
track_pid "$!"
sleep 2

# Celery worker + beat
uv run celery -A worker.celery worker -l info -B &
track_pid "$!"

# Frontend dev server
cd "$ROOT_DIR/frontend"
if command -v bun >/dev/null 2>&1; then
  bun run dev
else
  bun run dev
fi