#!/usr/bin/env bash
# Bootstrap a temporary GitHub archive, install globally, then remove the archive.
set -euo pipefail

REPO="${CODEX_SMART_ROUTER_REPO:-nar142857/codex-smart-router}"
REF="${CODEX_SMART_ROUTER_REF:-main}"
INSTALL_ARGS=()

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --ref)
      [[ "$#" -ge 2 ]] || { echo "--ref requires a branch, tag, or commit" >&2; exit 2; }
      REF="$2"
      shift 2
      ;;
    --repo)
      [[ "$#" -ge 2 ]] || { echo "--repo requires owner/name" >&2; exit 2; }
      REPO="$2"
      shift 2
      ;;
    --default-model|--default-reasoning-effort)
      [[ "$#" -ge 2 ]] || { echo "$1 requires a value" >&2; exit 2; }
      INSTALL_ARGS+=("$1" "$2")
      shift 2
      ;;
    -h|--help)
      echo "Usage: install-remote.sh [--ref branch|tag|commit] [--repo owner/name] [--default-model model] [--default-reasoning-effort effort]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

[[ "$REPO" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]] || { echo "Invalid repository: $REPO" >&2; exit 2; }
[[ "$REF" =~ ^[A-Za-z0-9._/-]+$ ]] || { echo "Invalid ref: $REF" >&2; exit 2; }
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v tar >/dev/null || { echo "tar is required" >&2; exit 1; }

TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/codex-smart-router.XXXXXX")"
trap 'rm -rf "$TEMP_DIR"' EXIT
ARCHIVE="$TEMP_DIR/router.tar.gz"

echo "Downloading Codex Smart Router ($REPO@$REF)..."
curl --fail --location --silent --show-error \
  "https://github.com/$REPO/archive/$REF.tar.gz" -o "$ARCHIVE"
tar -xzf "$ARCHIVE" -C "$TEMP_DIR"
BUNDLE_DIR="$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d -print -quit)"
[[ -n "$BUNDLE_DIR" && -f "$BUNDLE_DIR/scripts/install-global.sh" ]] || {
  echo "Downloaded archive does not contain the installer" >&2
  exit 1
}

bash "$BUNDLE_DIR/scripts/install-global.sh" "${INSTALL_ARGS[@]}"
echo "Temporary installer files removed. Restart Codex to load the new global routing rules."
