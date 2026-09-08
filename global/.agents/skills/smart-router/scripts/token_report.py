#!/usr/bin/env python3
"""Print the current Smart Router turn's token snapshot from Codex session logs.

The report is intentionally a snapshot: the final reply that contains it has not
been generated yet, so its own final-model call cannot be included.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


SETTING_RE = re.compile(r"^\s*token_usage_report\s*=\s*(true|false)\s*(?:#.*)?$", re.I)


def is_enabled(cwd: Path, codex_home: Path) -> bool:
    """Return the closest project setting, then the global setting, defaulting on."""
    for path in (cwd / ".codex" / "smart-router.toml", codex_home / "smart-router.toml"):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                match = SETTING_RE.match(line)
                if match:
                    return match.group(1).lower() == "true"
        except FileNotFoundError:
            continue
    return True


def records(session_root: Path):
    for path in session_root.rglob("rollout-*.jsonl"):
        try:
            with path.open(encoding="utf-8") as handle:
                yield path, [json.loads(line) for line in handle if line.strip()]
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue


def context_for(items: list[dict], root_turn_id: str) -> dict | None:
    for item in items:
        if item.get("type") != "turn_context":
            continue
        payload = item.get("payload", {})
        if payload.get("root_turn_id") == root_turn_id:
            return payload
    return None


def newest_root_turn(session_root: Path, cwd: Path) -> str | None:
    choices = []
    for path, items in records(session_root):
        for item in items:
            if item.get("type") != "turn_context":
                continue
            payload = item.get("payload", {})
            if payload.get("cwd") == str(cwd) and payload.get("root_turn_id"):
                choices.append((path.stat().st_mtime_ns, payload["root_turn_id"]))
    return max(choices)[1] if choices else None


def label(context: dict, session_id: str) -> str:
    task_path = context.get("task_path")
    if not task_path:
        return "root"
    return str(task_path).rsplit("/", 1)[-1] or session_id[:8]


def report(session_root: Path, root_turn_id: str) -> list[dict]:
    totals: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for _path, items in records(session_root):
        context = context_for(items, root_turn_id)
        if context is None:
            continue
        name = label(context, "")
        model = str(context.get("model") or "unknown")
        for item in items:
            if item.get("type") != "token_usage_record":
                continue
            payload = item.get("payload", {})
            if payload.get("root_turn_id") != root_turn_id:
                continue
            key = (name, model, str(payload.get("session_id") or "unknown"))
            for field, value in payload.get("usage", {}).items():
                if isinstance(value, int):
                    totals[key][field] += value
    rows = []
    for (name, model, _session_id), usage in totals.items():
        rows.append({"agent": name, "model": model, **usage})
    return sorted(rows, key=lambda row: (row["agent"] != "root", row["agent"], row["model"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-turn-id", help="root turn ID to report; defaults to the newest turn in this directory")
    parser.add_argument("--cwd", default=os.getcwd(), help="task working directory used for automatic discovery")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"), help="Codex state directory")
    args = parser.parse_args()
    cwd = Path(args.cwd).resolve()
    codex_home = Path(args.codex_home).expanduser().resolve()
    if not is_enabled(cwd, codex_home):
        return 0
    root_turn_id = args.root_turn_id or newest_root_turn(codex_home / "sessions", cwd)
    if not root_turn_id:
        print("Token usage snapshot unavailable: no Codex turn was found for this directory.", file=sys.stderr)
        return 1
    rows = report(codex_home / "sessions", root_turn_id)
    if not rows:
        print("Token usage snapshot unavailable: no completed model calls were recorded yet.", file=sys.stderr)
        return 1
    print("#### Token usage snapshot")
    print()
    print("| Agent | Model | Input | Cached input | Output | Total |")
    print("| --- | --- | ---: | ---: | ---: | ---: |")
    for row in rows:
        print("| {agent} | {model} | {input_tokens:,} | {cached_input_tokens:,} | {output_tokens:,} | {total_tokens:,} |".format(
            agent=row["agent"], model=row["model"], input_tokens=row.get("input_tokens", 0),
            cached_input_tokens=row.get("cached_input_tokens", 0), output_tokens=row.get("output_tokens", 0),
            total_tokens=row.get("total_tokens", 0)))
    print()
    print("Snapshot is taken before the final reply, so it excludes that reply's own model call. Cached input is included in input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
