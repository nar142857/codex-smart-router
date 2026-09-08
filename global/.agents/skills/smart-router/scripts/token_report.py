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
QUOTA_BUDGET_RE = re.compile(r"^\s*quota_budget_credits\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*(?:#.*)?$", re.I)

# USD and credit rates per million tokens, verified against official OpenAI
# pricing on 2026-09-08. Cached input is included in the input count emitted by
# Codex, so cost is computed from (input - cached), cached input, and output
# separately. Unknown models remain explicitly unpriced instead of guessed.
MODEL_RATES = {
    "gpt-6-astra": {"input": 10.0, "cached": 1.0, "output": 50.0, "credits_input": 250.0,
                     "credits_cached": 25.0, "credits_output": 1250.0},
    "gpt-5.6-sol": {"input": 4.0, "cached": 0.4, "output": 20.0, "credits_input": 100.0,
                      "credits_cached": 10.0, "credits_output": 500.0},
    "gpt-5.6-terra": {"input": 2.0, "cached": 0.2, "output": 12.0, "credits_input": 50.0,
                        "credits_cached": 5.0, "credits_output": 300.0},
    "gpt-5.6-luna": {"input": 0.2, "cached": 0.02, "output": 1.2, "credits_input": 5.0,
                       "credits_cached": 0.5, "credits_output": 30.0},
}


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


def quota_budget(cwd: Path, codex_home: Path) -> float | None:
    """Read an optional user-supplied credit budget from project then global settings."""
    for path in (cwd / ".codex" / "smart-router.toml", codex_home / "smart-router.toml"):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                match = QUOTA_BUDGET_RE.match(line)
                if match:
                    return float(match.group(1))
        except FileNotFoundError:
            continue
    return None


def session_meta(items: list[dict]) -> dict:
    """Return agent identity stored once at the beginning of a rollout file."""
    for item in items:
        if item.get("type") == "session_meta" and isinstance(item.get("payload"), dict):
            return item["payload"]
    return {}


def records(session_root: Path):
    for path in session_root.rglob("rollout-*.jsonl"):
        try:
            with path.open(encoding="utf-8") as handle:
                items = [json.loads(line) for line in handle if line.strip()]
                yield path, items, session_meta(items)
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
    for path, items, _meta in records(session_root):
        for item in items:
            if item.get("type") != "turn_context":
                continue
            payload = item.get("payload", {})
            if payload.get("cwd") == str(cwd) and payload.get("root_turn_id"):
                choices.append((path.stat().st_mtime_ns, payload["root_turn_id"]))
    return max(choices)[1] if choices else None


def label(context: dict, meta: dict) -> str:
    """Prefer the immutable session role over turn_context's optional path."""
    role = meta.get("agent_role")
    if role:
        agent_path = meta.get("agent_path")
        nickname = meta.get("agent_nickname")
        task_name = str(agent_path).rsplit("/", 1)[-1] if agent_path else str(role)
        suffix = f" · {role}"
        return f"{task_name}{suffix} ({nickname})" if nickname else f"{task_name}{suffix}"
    task_path = context.get("task_path")
    if not task_path:
        return "root"
    return str(task_path).rsplit("/", 1)[-1] or "root"


def estimate(usage: dict, model: str) -> dict:
    """Calculate cache rate plus API-equivalent USD and Codex credit estimates."""
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    cached_tokens = min(int(usage.get("cached_input_tokens", 0) or 0), input_tokens)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    rate = MODEL_RATES.get(model)
    result = {"cache_hit_rate": cached_tokens / input_tokens if input_tokens else 0.0}
    if rate is None:
        return result
    uncached_tokens = input_tokens - cached_tokens
    scale = 1_000_000
    result["estimated_usd"] = (
        uncached_tokens * rate["input"] + cached_tokens * rate["cached"] + output_tokens * rate["output"]
    ) / scale
    result["estimated_credits"] = (
        uncached_tokens * rate["credits_input"] + cached_tokens * rate["credits_cached"]
        + output_tokens * rate["credits_output"]
    ) / scale
    return result


def report(session_root: Path, root_turn_id: str) -> list[dict]:
    totals: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for _path, items, meta in records(session_root):
        context = context_for(items, root_turn_id)
        if context is None:
            continue
        name = label(context, meta)
        model = str(context.get("model") or "unknown")
        for item in items:
            if item.get("type") != "token_usage_record":
                continue
            payload = item.get("payload", {})
            if payload.get("root_turn_id") != root_turn_id:
                continue
            key = (name, model, str(meta.get("id") or payload.get("session_id") or "unknown"))
            for field, value in payload.get("usage", {}).items():
                if isinstance(value, int):
                    totals[key][field] += value
    rows = []
    for (name, model, _session_id), usage in totals.items():
        rows.append({"agent": name, "model": model, **usage, **estimate(usage, model)})
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
    estimated_credits = sum(row.get("estimated_credits", 0) for row in rows)
    budget = quota_budget(cwd, codex_home)
    print("| Agent | Model | 输入 | 缓存输入 | 缓存命中率 | 输出 | 总计 | 估算 Credits | 任务占比 | 预算占比 | 估算 API 费用 |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in rows:
        credits = row.get("estimated_credits")
        quota_share = f"{credits / estimated_credits:.1%}" if credits is not None and estimated_credits else "N/A"
        budget_share = f"{credits / budget:.1%}" if credits is not None and budget else "N/A"
        cost = row.get("estimated_usd")
        print("| {agent} | {model} | {input_tokens:,} | {cached_input_tokens:,} | {cache_hit_rate:.1%} | {output_tokens:,} | {total_tokens:,} | {credits} | {quota_share} | {budget_share} | {cost} |".format(
            agent=row["agent"], model=row["model"], input_tokens=row.get("input_tokens", 0),
            cached_input_tokens=row.get("cached_input_tokens", 0), output_tokens=row.get("output_tokens", 0),
            cache_hit_rate=row["cache_hit_rate"], total_tokens=row.get("total_tokens", 0),
            credits=f"{credits:,.2f}" if credits is not None else "N/A", quota_share=quota_share, budget_share=budget_share,
            cost=f"${cost:,.4f}" if cost is not None else "N/A"))
    print()
    print("任务占比表示各 Agent 占本任务估算 Codex Credits 的比例。未配置 quota_budget_credits 时，预算占比显示 N/A；两者都不是账户实时余额。")
    print("估算 API 费用使用包内 2026-09-08 核验的 OpenAI 参考费率，仅供比较，不构成账单。快照不含最终回复本身；缓存输入已计入输入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
