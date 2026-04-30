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
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
uv run --active gunicorn -w "${WEB_CONCURRENCY}" -b "0.0.0.0:${PORT}" wsgi:app &
PIDS+=("$!")

echo "Starting celery worker+beat"
CELERY_CONCURRENCY="${CELERY_CONCURRENCY:-1}"
CELERY_POOL="${CELERY_POOL:-solo}"
uv run --active celery -A worker.celery worker -l info -B --concurrency "${CELERY_CONCURRENCY}" --pool "${CELERY_POOL}" &
PIDS+=("$!")

wait -n
exit $?
