#!/usr/bin/env bash
set -euo pipefail
TARGET="."
if [[ "$#" -gt 0 && "$1" != --* ]]; then
  TARGET="$1"
  shift
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$(cd "$TARGET" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  echo "Python 3 is required for the safe merge installer."
  exit 1
fi
"$PYTHON" "$SCRIPT_DIR/install_global.py" --codex-dir "$TARGET/.codex" --skills-dir "$TARGET/.agents/skills" --agents-md "$TARGET/AGENTS.md" "$@"
