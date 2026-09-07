#!/usr/bin/env python3
"""Repair a ~/.codex/config.toml that was broken by an older Smart Router installer.

Older versions of install_global.py wrote the `[agents]` table *before* the
user's original top-level keys, so keys such as `approval_policy` and
`sandbox_mode` ended up inside `[agents]` and Codex failed with:

    invalid configuration: invalid type: string "never",
    expected struct AgentRoleToml in `agents`

This script:
  1. backs up the current (broken) config as config.toml.broken-<stamp>
  2. looks for the newest pre-install backup config.toml.bak-* that is clean
     (valid TOML and not touched by Smart Router)
  3. restores the user's original config from that backup
  4. re-applies the Smart Router settings with the fixed merge logic
"""
from pathlib import Path
import argparse, datetime, re, shutil, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_global import (  # noqa: E402
    MANAGED_AGENTS, MANAGED_START, SECTION_RE, merge_and_validate, parse_toml, root_model_for,
)

# Only backups written by the installer itself (config.toml.bak-YYYYMMDD-HHMMSS).
BACKUP_RE = re.compile(r"^config\.toml\.bak-(\d{8}-\d{6})$")


def is_clean_backup(text: str) -> bool:
    """A clean backup is valid TOML that was never written by Smart Router."""
    if MANAGED_START in text:
        return False
    try:
        doc = parse_toml(text)
    except Exception:
        return False
    agents = doc.get("agents")
    if isinstance(agents, dict):
        # Any scalar under [agents] that Smart Router manages means it was written by us.
        if any(k in agents for k in MANAGED_AGENTS):
            return False
    return True


def find_clean_backup(cfg: Path):
    candidates = [p for p in cfg.parent.iterdir() if BACKUP_RE.match(p.name)]
    candidates.sort(key=lambda p: BACKUP_RE.match(p.name).group(1), reverse=True)
    for cand in candidates:
        try:
            text = cand.read_text(encoding="utf-8")
        except OSError:
            continue
        if is_clean_backup(text):
            return cand
    return None


def hoist_misplaced_agents_keys(text: str) -> str:
    """Fallback when no clean backup exists: move non-managed scalar keys that
    sit inside a bare `[agents]` table back to the top level."""
    top, rest, hoisted = [], [], []
    section = None
    for line in text.splitlines():
        m = SECTION_RE.match(line)
        if m:
            section = m.group(1).strip()
            rest.append(line)
            continue
        if section is None:
            top.append(line)
        elif section == "agents":
            km = re.match(r"^\s*([A-Za-z0-9_\-\"']+)\s*=", line)
            if km and km.group(1).strip("\"'") not in MANAGED_AGENTS:
                hoisted.append(line)
            else:
                rest.append(line)
        else:
            rest.append(line)
    if not hoisted:
        return text
    return "\n".join(top + hoisted + [""] + rest) + "\n"


def detect_root(text: str) -> str:
    m = re.search(r'^\s*model\s*=\s*"([^"]+)"', text, re.M)
    if m and m.group(1) == "gpt-5.6-sol":
        return "sol"
    return "astra"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", choices=["astra", "sol", "auto"], default="auto",
                   help="root model; 'auto' keeps whatever the current config uses (default)")
    p.add_argument("--home", default=str(Path.home()))
    p.add_argument("--backup", help="explicit clean backup to restore from (skips auto detection)")
    p.add_argument("--dry-run", action="store_true", help="print the repaired config instead of writing it")
    args = p.parse_args()

    home = Path(args.home).expanduser().resolve()
    cfg = home / ".codex" / "config.toml"
    if not cfg.exists():
        print(f"ERROR: {cfg} does not exist; nothing to repair", file=sys.stderr)
        return 1

    current = cfg.read_text(encoding="utf-8")
    root = detect_root(current) if args.root == "auto" else args.root
    root_model = root_model_for(root)

    if args.backup:
        source = Path(args.backup).expanduser().resolve()
        if not source.exists():
            print(f"ERROR: backup {source} does not exist", file=sys.stderr)
            return 1
    else:
        source = find_clean_backup(cfg)

    if source is not None:
        base = source.read_text(encoding="utf-8")
        print(f"Restoring user config from clean backup: {source}")
    else:
        print("WARNING: no clean pre-install backup found; hoisting misplaced keys out of [agents] instead",
              file=sys.stderr)
        base = hoist_misplaced_agents_keys(current)

    try:
        merged = merge_and_validate(base, root_model)
    except Exception as e:
        print(f"ERROR: repaired config failed validation, nothing written: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        sys.stdout.write(merged)
        return 0

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    broken = cfg.with_name(cfg.name + f".broken-{stamp}")
    shutil.copy2(cfg, broken)
    cfg.write_text(merged, encoding="utf-8")

    print(f"Backed up broken config to: {broken}")
    print(f"Repaired config written to: {cfg}")
    print(f"Root model: {root_model}")
    print("Restart Codex after repairing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
