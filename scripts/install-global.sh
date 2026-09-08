#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/install_global.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$SCRIPT_DIR/install_global.py" "$@"
else
  echo "Python 3 is required for the safe merge installer."
  exit 1
fi
