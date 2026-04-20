#!/bin/bash
# Start the local dev server (requires Postgres running via brew services)
set -e

cd "$(dirname "$0")/.."

BACKEND="$(pwd)/backend"
echo "Starting API on http://localhost:8000 (docs at http://localhost:8000/docs)"
~/.local/bin/uv --project "$BACKEND" run --directory "$BACKEND" uvicorn app.main:app --reload --port 8000
