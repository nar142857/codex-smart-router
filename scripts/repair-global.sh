#!/usr/bin/env bash
# Repair a ~/.codex/config.toml broken by an older Smart Router installer.
# See HOTFIX.md. Usage: ./repair-global.sh [--home <path>] [--backup <path>] [--dry-run]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/repair_config.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$SCRIPT_DIR/repair_config.py" "$@"
else
  echo "Python 3 is required for the config repair."
  exit 1
fi
