#!/usr/bin/env bash
# Pull the latest Claude Code briefing from GCS into .claude/rules/
# Run this before opening a Claude Code session to get fresh market context.
#
# Requires: gcloud auth application-default login (or ADC already configured)
# Usage: ./scripts/sync_briefing.sh
set -euo pipefail

ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

# Read bucket from .env if not set in environment
if [[ -z "${BRIEFING_GCS_BUCKET:-}" ]]; then
  ENV_FILE="$ROOT/.env"
  if [[ -f "$ENV_FILE" ]]; then
    BRIEFING_GCS_BUCKET="$(grep '^BRIEFING_GCS_BUCKET=' "$ENV_FILE" | cut -d= -f2 | tr -d '"' || true)"
  fi
fi

if [[ -z "${BRIEFING_GCS_BUCKET:-}" ]]; then
  echo "Error: BRIEFING_GCS_BUCKET is not set. Add it to .env or export it." >&2
  exit 1
fi

OBJECT=".claude/rules/market-intelligence.md"
DEST="$ROOT/$OBJECT"

gsutil cp "gs://$BRIEFING_GCS_BUCKET/$OBJECT" "$DEST"
echo "Briefing synced → $DEST"
