#!/usr/bin/env bash
set -euo pipefail

PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [[ -z "${PORT:-}" ]]; then
  echo "PORT is not set"
  exit 1
fi

echo "Starting gunicorn on :$PORT"
uv run --active gunicorn -w 2 -b "0.0.0.0:${PORT}" wsgi:app &
PIDS+=("$!")

echo "Starting celery worker+beat"
uv run --active celery -A worker.celery worker -l info -B &
PIDS+=("$!")

wait -n
exit $?

