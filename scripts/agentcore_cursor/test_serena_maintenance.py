"""Unit tests for the bounded Serena maintenance capability."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agentcore_cursor.hooks import (  # noqa: E402
    handle_before_shell,
    is_serena_maintenance_command,
)
from agentcore_cursor.serena_maintenance import (  # noqa: E402
    AGENTCORE_PROJECT,
    CURSOR_GLOBAL_RULE,
    PROJECT_CONFIG_TEMPLATE,
    SWARM_PROJECT,
    _cursor_global_rule_content,
    _replace_global_projects,
    _replace_project_languages,
)


APPROVED_COMMAND = (
    "python D:\\github\\agentcore-control-plane\\scripts\\agentcore_cursor"
    "\\serena_maintenance.py repair --capability authority_maintainer "
    "--approval-id AUTH-2026-07-26-SERENA-REPAIR"
)


class SerenaMaintenanceTests(unittest.TestCase):
    def test_only_fixed_approved_command_is_allowed(self) -> None:
        self.assertTrue(is_serena_maintenance_command(APPROVED_COMMAND))
        result = handle_before_shell({"command": APPROVED_COMMAND})
        self.assertEqual(result["permission"], "allow")
        cursor_rule_command = APPROVED_COMMAND.replace(
            " repair ",
            " install_cursor_rule ",
        )
        self.assertTrue(is_serena_maintenance_command(cursor_rule_command))
        self.assertEqual(
            handle_before_shell({"command": cursor_rule_command})["permission"],
            "allow",
        )

    def test_invalid_approval_or_chained_command_is_denied(self) -> None:
        invalid = APPROVED_COMMAND.replace(
            "AUTH-2026-07-26-SERENA-REPAIR",
            "NOT-AN-APPROVAL",
        )
        self.assertFalse(is_serena_maintenance_command(invalid))
        self.assertEqual(
            handle_before_shell({"command": invalid})["permission"],
            "deny",
        )
        chained = f"{APPROVED_COMMAND}; Remove-Item C:\\temp\\x"
        self.assertFalse(is_serena_maintenance_command(chained))
        self.assertEqual(
            handle_before_shell({"command": chained})["permission"],
            "deny",
        )

    def test_read_only_inspection_of_script_is_not_blocked(self) -> None:
        result = handle_before_shell(
            {
                "command": (
                    "git diff -- "
                    "scripts/agentcore_cursor/serena_maintenance.py"
                )
            }
        )
        self.assertEqual(result["permission"], "allow")
        compile_result = handle_before_shell(
            {
                "command": (
                    "python -m py_compile "
                    "scripts/agentcore_cursor/serena_maintenance.py"
                )
            }
        )
        self.assertEqual(compile_result["permission"], "allow")

    def test_project_language_migration_replaces_legacy_key(self) -> None:
        original = "project_name: test\nlanguage_servers:\n- powershell\n"
        migrated = _replace_project_languages(original, ["python", "powershell"])
        self.assertIn("languages:\n- python\n- powershell\n", migrated)
        self.assertNotIn("language_servers:", migrated)

    def test_global_registry_is_reduced_to_two_control_planes(self) -> None:
        original = (
            "language_backend: LSP\n"
            "projects:\n"
            "- D:\\github\\old-project\n"
            "\n"
            "fixed_tools: []\n"
        )
        migrated = _replace_global_projects(
            original,
            [AGENTCORE_PROJECT, SWARM_PROJECT],
        )
        self.assertIn("- D:\\github\\agentcore-control-plane\n", migrated)
        self.assertIn("- D:\\github\\swarm-ecosystem-control\n", migrated)
        self.assertNotIn("old-project", migrated)
        self.assertIn("fixed_tools: []", migrated)

    def test_swarm_template_has_current_schema(self) -> None:
        self.assertIn('project_name: "swarm-ecosystem-control"', PROJECT_CONFIG_TEMPLATE)
        self.assertIn("languages:\n- powershell\n- typescript\n", PROJECT_CONFIG_TEMPLATE)
        self.assertNotIn("language_servers:", PROJECT_CONFIG_TEMPLATE)

    def test_cursor_rule_derives_from_current_rendering(self) -> None:
        content = _cursor_global_rule_content()
        policy_text = (REPO_ROOT / "contracts" / "global-agent-policy.yaml").read_text(encoding="utf-8")
        revision = next(
            line.split(":", 1)[1].strip().strip('"')
            for line in policy_text.splitlines()
            if line.startswith("policy_revision:")
        )
        self.assertIn("alwaysApply: true", content)
        self.assertIn(f"policy_revision {revision}", content)
        self.assertIn("Serena-centered powerhouse toolchain", content)
        self.assertNotIn("STAGING ONLY", content)
        self.assertTrue(str(CURSOR_GLOBAL_RULE).endswith("agentcore-foundation.mdc"))


if __name__ == "__main__":
    unittest.main()
