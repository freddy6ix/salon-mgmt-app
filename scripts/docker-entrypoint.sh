#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "Running seed..."
  PYTHONPATH=/app python scripts/seed.py || echo "WARNING: seed exited with errors (non-fatal)"
fi

if [ "${RUN_IMPORT:-false}" = "true" ]; then
  echo "Running legacy data import..."
  PYTHONPATH=/app python scripts/run_import.py || echo "WARNING: import exited with errors (non-fatal)"
fi

echo "Starting server..."
exec "$@"
