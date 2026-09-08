#!/usr/bin/env python3
"""Smoke tests for the config merge / repair logic. Run: python3 -m unittest discover tests"""
import os, subprocess, sys, tempfile, tomllib, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import install_global as ig  # noqa: E402
import repair_config as rc  # noqa: E402

USER_CONFIG = '''approval_policy = "never"
sandbox_mode = "danger-full-access"

[projects."/Users/test/repo"]
trust_level = "trusted"

[mcp_servers.foo]
command = "foo"
'''

# What the old installer produced when it accidentally nested user keys in [agents].
BROKEN_CONFIG = '''[agents]
enabled = true
max_concurrent_threads_per_session = 4
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
# --- End Smart Router managed block ---

approval_policy = "never"
sandbox_mode = "danger-full-access"

[projects."/Users/test/repo"]
trust_level = "trusted"

[mcp_servers.foo]
command = "foo"
'''


def assert_smart_router_merge(tc, doc):
    tc.assertEqual(doc["approval_policy"], "never")
    tc.assertEqual(doc["sandbox_mode"], "danger-full-access")
    tc.assertNotIn("approval_policy", doc["agents"])
    tc.assertNotIn("sandbox_mode", doc["agents"])
    tc.assertIs(doc["agents"]["enabled"], True)
    tc.assertEqual(doc["agents"]["max_concurrent_threads_per_session"], 4)
    tc.assertEqual(doc["agents"]["default_subagent_model"], "gpt-5.6-luna")
    tc.assertEqual(doc["agents"]["default_subagent_reasoning_effort"], "medium")
    expected_roles = {
        "explorer": "agents/explorer.toml",
        "researcher": "agents/researcher.toml",
        "tester": "agents/tester.toml",
        "fast_worker": "agents/fast_worker.toml",
        "worker": "agents/worker.toml",
        "expert": "agents/expert.toml",
        "reviewer": "agents/reviewer.toml",
        "deep_reviewer": "agents/deep_reviewer.toml",
    }
    for role, config_file in expected_roles.items():
        tc.assertEqual(doc["agents"][role], {"config_file": config_file})
    tc.assertEqual(doc["projects"]["/Users/test/repo"]["trust_level"], "trusted")
    tc.assertEqual(doc["mcp_servers"]["foo"]["command"], "foo")


class MergeConfigTest(unittest.TestCase):
    def test_top_level_keys_stay_before_tables(self):
        merged = ig.merge_and_validate(USER_CONFIG)
        doc = tomllib.loads(merged)
        assert_smart_router_merge(self, doc)
        self.assertNotIn("model", doc)
        # textual layout: every top-level key precedes the first table header
        first_table = merged.index("[")
        for key in ("approval_policy", "sandbox_mode"):
            self.assertLess(merged.index(key), first_table, key)

    def test_preserves_user_selected_root_model(self):
        existing = 'model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n\n' + USER_CONFIG
        doc = tomllib.loads(ig.merge_and_validate(existing))
        self.assertEqual(doc["model"], "gpt-5.6-sol")
        self.assertEqual(doc["model_reasoning_effort"], "high")
        assert_smart_router_merge(self, doc)

    def test_requested_default_model_replaces_only_default_settings(self):
        existing = 'model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n\n' + USER_CONFIG
        doc = tomllib.loads(ig.merge_and_validate(existing, "gpt-5.6-terra", "medium"))
        self.assertEqual(doc["model"], "gpt-5.6-terra")
        self.assertEqual(doc["model_reasoning_effort"], "medium")
        assert_smart_router_merge(self, doc)

    def test_empty_config(self):
        doc = tomllib.loads(ig.merge_and_validate(""))
        self.assertIs(doc["agents"]["enabled"], True)
        self.assertNotIn("model", doc)

    def test_idempotent(self):
        once = ig.merge_and_validate(USER_CONFIG)
        twice = ig.merge_and_validate(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("[agents]"), 1)
        self.assertEqual(once.count(ig.MANAGED_START), 1)

    def test_replaces_existing_model_and_agents_keeps_provider_and_subtables(self):
        existing = '''model = "gpt-4"
model_reasoning_effort = "high"
approval_policy = "on-request"
model_provider = "custom"

[model_providers.custom]
name = "Custom"
base_url = "http://localhost:1234/v1"

[agents]
enabled = false
max_concurrent_threads_per_session = 1

[agents.roles.helper]
model = "x"
'''
        merged = ig.merge_and_validate(existing)
        doc = tomllib.loads(merged)
        self.assertEqual(doc["model"], "gpt-4")
        self.assertEqual(doc["model_reasoning_effort"], "high")
        self.assertEqual(doc["approval_policy"], "on-request")
        self.assertEqual(doc["model_provider"], "custom")
        self.assertEqual(doc["model_providers"]["custom"]["base_url"], "http://localhost:1234/v1")
        self.assertIs(doc["agents"]["enabled"], True)
        self.assertEqual(doc["agents"]["max_concurrent_threads_per_session"], 4)
        self.assertEqual(doc["agents"]["roles"]["helper"]["model"], "x")

    def test_validation_rejects_leaked_top_level_key(self):
        with self.assertRaises(ValueError):
            ig.validate_merged(USER_CONFIG, BROKEN_CONFIG)


class InstallerEndToEndTest(unittest.TestCase):
    def test_install_preserves_user_config(self):
        with tempfile.TemporaryDirectory() as home:
            codex = Path(home) / ".codex"
            codex.mkdir()
            (codex / "config.toml").write_text(USER_CONFIG, encoding="utf-8")
            subprocess.run([sys.executable, str(ROOT / "scripts" / "install_global.py"),
                            "--home", home], check=True, capture_output=True)
            doc = tomllib.loads((codex / "config.toml").read_text(encoding="utf-8"))
            assert_smart_router_merge(self, doc)
            self.assertTrue(list(codex.glob("config.toml.bak-*")))
            self.assertIn("token_usage_report = true", (codex / "smart-router.toml").read_text(encoding="utf-8"))

    def test_installer_keeps_skill_backups_outside_the_scanned_skills_directory(self):
        with tempfile.TemporaryDirectory() as home:
            skills = Path(home) / ".agents" / "skills" / "smart-router"
            skills.mkdir(parents=True)
            (skills / "SKILL.md").write_text("old skill", encoding="utf-8")
            subprocess.run([sys.executable, str(ROOT / "scripts" / "install_global.py"),
                            "--home", home], check=True, capture_output=True)
            self.assertTrue((skills / "SKILL.md").is_file())
            self.assertFalse(list(skills.parent.glob("smart-router.bak-*")))
            self.assertTrue(list((skills.parent.parent / "skills-backups").glob("smart-router.bak-*")))

    def test_install_can_set_an_optional_default_model(self):
        with tempfile.TemporaryDirectory() as home:
            codex = Path(home) / ".codex"
            codex.mkdir()
            (codex / "config.toml").write_text(USER_CONFIG, encoding="utf-8")
            subprocess.run([sys.executable, str(ROOT / "scripts" / "install_global.py"),
                            "--home", home, "--default-model", "gpt-5.6-terra"],
                           check=True, capture_output=True)
            doc = tomllib.loads((codex / "config.toml").read_text(encoding="utf-8"))
            self.assertEqual(doc["model"], "gpt-5.6-terra")
            self.assertEqual(doc["model_reasoning_effort"], "medium")
            assert_smart_router_merge(self, doc)


class RemoteBootstrapTest(unittest.TestCase):
    def test_bootstrap_scripts_download_to_temp_and_invoke_global_installer(self):
        shell = (ROOT / "scripts" / "install-remote.sh").read_text(encoding="utf-8")
        powershell = (ROOT / "scripts" / "install-remote.ps1").read_text(encoding="utf-8")
        self.assertIn("mktemp -d", shell)
        self.assertIn("https://github.com/$REPO/archive/$REF.tar.gz", shell)
        self.assertIn('bash "$BUNDLE_DIR/scripts/install-global.sh"', shell)
        self.assertIn("trap 'rm -rf", shell)
        self.assertIn("--default-model|--default-reasoning-effort", shell)
        self.assertNotIn("git clone", shell)
        self.assertIn("https://github.com/$Repo/archive/$Ref.zip", powershell)
        self.assertIn("install-global.ps1", powershell)
        self.assertIn("Remove-Item -Path $TempDir -Recurse -Force", powershell)
        self.assertIn("[string]$DefaultModel", powershell)
        self.assertNotIn("git clone", powershell)

    def test_project_scoped_install_preserves_existing_config_and_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            codex = project / ".codex"
            codex.mkdir()
            (codex / "config.toml").write_text(USER_CONFIG, encoding="utf-8")
            (project / "AGENTS.md").write_text("# Existing project instructions\n", encoding="utf-8")
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "install_global.py"),
                "--codex-dir", str(codex), "--skills-dir", str(project / ".agents" / "skills"),
                "--agents-md", str(project / "AGENTS.md"),
            ], check=True, capture_output=True)
            doc = tomllib.loads((codex / "config.toml").read_text(encoding="utf-8"))
            assert_smart_router_merge(self, doc)
            instructions = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# Existing project instructions", instructions)
            self.assertIn("Root/orchestrator: use the model selected for the current Codex conversation.", instructions)
            self.assertTrue((project / ".agents" / "skills" / "smart-router" / "SKILL.md").is_file())
            self.assertTrue((project / ".agents" / "skills" / "smart-router" / "scripts" / "token_report.py").is_file())
            self.assertIn("token_usage_report = true", (codex / "smart-router.toml").read_text(encoding="utf-8"))
            self.assertTrue(list(codex.glob("config.toml.bak-*")))


class RepairTest(unittest.TestCase):
    def _home_with_broken_config(self, tmp, with_backup=True):
        codex = Path(tmp) / ".codex"
        codex.mkdir()
        if with_backup:
            (codex / "config.toml.bak-20260101-000000").write_text(USER_CONFIG, encoding="utf-8")
            # a later, already-broken backup must not be picked
            (codex / "config.toml.bak-20260102-000000").write_text(BROKEN_CONFIG, encoding="utf-8")
        (codex / "config.toml").write_text(BROKEN_CONFIG, encoding="utf-8")
        return codex

    def test_broken_config_is_detected(self):
        self.assertFalse(rc.is_clean_backup(BROKEN_CONFIG))
        self.assertTrue(rc.is_clean_backup(USER_CONFIG))

    def test_repair_restores_from_clean_backup(self):
        with tempfile.TemporaryDirectory() as home:
            codex = self._home_with_broken_config(home)
            res = subprocess.run([sys.executable, str(ROOT / "scripts" / "repair_config.py"), "--home", home],
                                 check=True, capture_output=True, text=True)
            self.assertIn("config.toml.bak-20260101-000000", res.stdout)
            doc = tomllib.loads((codex / "config.toml").read_text(encoding="utf-8"))
            assert_smart_router_merge(self, doc)
            self.assertNotIn("model", doc)
            self.assertTrue(list(codex.glob("config.toml.broken-*")))

    def test_repair_without_backup_hoists_keys(self):
        with tempfile.TemporaryDirectory() as home:
            codex = self._home_with_broken_config(home, with_backup=False)
            subprocess.run([sys.executable, str(ROOT / "scripts" / "repair_config.py"), "--home", home],
                           check=True, capture_output=True, text=True)
            doc = tomllib.loads((codex / "config.toml").read_text(encoding="utf-8"))
            assert_smart_router_merge(self, doc)

    def test_repair_shell_wrapper(self):
        with tempfile.TemporaryDirectory() as home:
            codex = self._home_with_broken_config(home)
            subprocess.run(["bash", str(ROOT / "scripts" / "repair-global.sh"), "--home", home],
                           check=True, capture_output=True, text=True)
            doc = tomllib.loads((codex / "config.toml").read_text(encoding="utf-8"))
            assert_smart_router_merge(self, doc)
            self.assertNotIn("model", doc)


if __name__ == "__main__":
    unittest.main()
