#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Running seed..."
PYTHONPATH=/app python scripts/seed.py

echo "Starting server..."
exec "$@"
