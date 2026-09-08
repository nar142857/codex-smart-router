"""Focused tests for the installed Smart Router token usage reporter."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "global" / ".agents" / "skills" / "smart-router" / "scripts" / "token_report.py"
SPEC = importlib.util.spec_from_file_location("token_report", REPORT_PATH)
token_report = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(token_report)


def rollout(path: Path, meta: dict, root_turn_id: str, model: str, usage: dict) -> None:
    """Write the smallest valid rollout fixture for one root or child session."""
    records = [
        {"type": "session_meta", "payload": meta},
        {"type": "turn_context", "payload": {"root_turn_id": root_turn_id, "model": model}},
        {"type": "token_usage_record", "payload": {
            "root_turn_id": root_turn_id,
            "session_id": "root-session",
            "usage": usage,
        }},
    ]
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


class TokenReportTest(unittest.TestCase):
    def test_reports_real_subagent_identity_and_estimates(self):
        with tempfile.TemporaryDirectory() as tmp:
            sessions = Path(tmp)
            root_turn_id = "turn-1"
            rollout(sessions / "rollout-root.jsonl", {"id": "root-session"}, root_turn_id,
                    "gpt-5.6-terra", {"input_tokens": 1_000_000, "cached_input_tokens": 500_000,
                                        "output_tokens": 100_000, "total_tokens": 1_100_000})
            rollout(sessions / "rollout-child.jsonl", {
                "id": "child-session", "agent_role": "explorer", "agent_nickname": "Ampere",
                "agent_path": "/root/token_log_analysis",
            }, root_turn_id, "gpt-5.6-luna", {
                "input_tokens": 100_000, "cached_input_tokens": 50_000,
                "output_tokens": 10_000, "total_tokens": 110_000,
            })
            rows = token_report.report(sessions, root_turn_id)

        self.assertEqual([row["agent"] for row in rows], ["root", "token_log_analysis · explorer (Ampere)"])
        root = rows[0]
        self.assertEqual(root["cache_hit_rate"], 0.5)
        self.assertAlmostEqual(root["estimated_usd"], 2.3)
        self.assertAlmostEqual(root["estimated_credits"], 57.5)
        self.assertNotEqual(rows[0]["agent"], rows[1]["agent"])

    def test_unknown_model_is_explicitly_unpriced(self):
        result = token_report.estimate({"input_tokens": 10, "cached_input_tokens": 4, "output_tokens": 2}, "unknown")
        self.assertEqual(result, {"cache_hit_rate": 0.4})

    def test_quota_budget_reads_project_before_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            project = Path(tmp) / "project"
            (home / ".codex").mkdir(parents=True)
            (project / ".codex").mkdir(parents=True)
            (home / ".codex" / "smart-router.toml").write_text("quota_budget_credits = 100\n", encoding="utf-8")
            (project / ".codex" / "smart-router.toml").write_text("quota_budget_credits = 25\n", encoding="utf-8")
            self.assertEqual(token_report.quota_budget(project, home / ".codex"), 25.0)

if __name__ == "__main__":
    unittest.main()
