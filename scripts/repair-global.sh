#!/usr/bin/env bash
# Repair a ~/.codex/config.toml broken by an older Smart Router installer.
# See HOTFIX.md. Usage: ./repair-global.sh [terra|sol|auto]
set -euo pipefail
ROOT="${1:-auto}"
if [[ "$ROOT" != "terra" && "$ROOT" != "sol" && "$ROOT" != "auto" ]]; then
  echo "Usage: ./repair-global.sh [terra|sol|auto]"
  exit 2
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/repair_config.py" --root "$ROOT" "${@:2}"
elif command -v python >/dev/null 2>&1; then
  python "$SCRIPT_DIR/repair_config.py" --root "$ROOT" "${@:2}"
else
  echo "Python 3 is required for the config repair."
  exit 1
fi
