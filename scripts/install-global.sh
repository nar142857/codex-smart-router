#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-astra}"
if [[ "$ROOT" != "astra" && "$ROOT" != "sol" ]]; then
  echo "Usage: ./install-global.sh [astra|sol]"
  exit 2
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/install_global.py" --root "$ROOT"
elif command -v python >/dev/null 2>&1; then
  python "$SCRIPT_DIR/install_global.py" --root "$ROOT"
else
  echo "Python 3 is required for the safe merge installer."
  exit 1
fi
