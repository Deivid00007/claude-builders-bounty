#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
  exec python3 "$ROOT/generate-changelog/scripts/generate_changelog.py" "$@"
elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
  exec python "$ROOT/generate-changelog/scripts/generate_changelog.py" "$@"
elif command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
  exec py -3 "$ROOT/generate-changelog/scripts/generate_changelog.py" "$@"
else
  echo "error: Python 3.11+ is required to generate the changelog" >&2
  exit 1
fi
