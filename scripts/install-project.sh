#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-.}"
ROOT="${2:-astra}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TARGET/.codex/agents" "$TARGET/.agents/skills"
[[ -f "$TARGET/.codex/config.toml" ]] && cp "$TARGET/.codex/config.toml" "$TARGET/.codex/config.toml.bak-$STAMP"
[[ -f "$TARGET/AGENTS.md" ]] && cp "$TARGET/AGENTS.md" "$TARGET/AGENTS.md.bak-$STAMP"
cp "$BUNDLE_DIR"/global/.codex/agents/*.toml "$TARGET/.codex/agents/"
rm -rf "$TARGET/.agents/skills/smart-router"
cp -R "$BUNDLE_DIR/global/.agents/skills/smart-router" "$TARGET/.agents/skills/"
if [[ "$ROOT" == "sol" ]]; then
  cp "$BUNDLE_DIR/fallbacks/config-root-sol.toml" "$TARGET/.codex/config.toml"
else
  cp "$BUNDLE_DIR/global/.codex/config.toml" "$TARGET/.codex/config.toml"
fi
if [[ ! -f "$TARGET/AGENTS.md" ]]; then
  cp "$BUNDLE_DIR/project-template/AGENTS.md" "$TARGET/AGENTS.md"
else
  cat >> "$TARGET/AGENTS.md" <<'BLOCK'

<!-- SMART-ROUTER:PROJECT -->
## Smart Router
Use `$smart-router` for non-trivial engineering tasks.
Prefer Luna for exploration/research/tests, Terra for normal implementation, Sol for hard work/review, and Astra primarily for orchestration/high-risk review.
Do not mechanically spawn all roles for small tasks.
BLOCK
fi
echo "Installed project-scoped Smart Router into: $TARGET"
echo "Restart/reopen the project in Codex."
