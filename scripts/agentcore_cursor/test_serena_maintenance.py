"""Unit tests for the bounded Serena maintenance capability."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agentcore_cursor.hooks import (  # noqa: E402
    handle_before_shell,
    is_serena_maintenance_command,
)
from agentcore_cursor import serena_maintenance as maintenance  # noqa: E402
from agentcore_cursor.serena_maintenance import (  # noqa: E402
    AGENTCORE_PROJECT,
    CURSOR_GLOBAL_RULE,
    PROJECT_CONFIG_TEMPLATE,
    SWARM_PROJECT,
    _cursor_global_rule_content,
    _replace_global_projects,
    _replace_project_languages,
)
from render_ide_rules import render  # noqa: E402


APPROVED_COMMAND = (
    "python D:\\github\\agentcore-control-plane\\scripts\\agentcore_cursor"
    "\\serena_maintenance.py repair --capability authority_maintainer "
    "--approval-id AUTH-2026-07-26-SERENA-REPAIR"
)
NFA_SECTION = (
    "\n## NFA Platform documentation integrity rule\n\n"
    "Keep this local customization intact.\n"
    "\n## Another appended local section\n"
    "Its content must survive too.\n"
)
SYNTHETIC_POLICY = {
    "policy_revision": "2099-01-01-current",
    "mandatory_rules": [{"title": "Foundation", "rule": "Current foundation content."}],
    "forbidden_routes": [],
}
SYNTHETIC_PROFILE = {"ide_id": "cursor", "display_name": "Cursor"}
GENERATED_RULE = render(SYNTHETIC_PROFILE, SYNTHETIC_POLICY)


def _write_cursor_sources(root: Path) -> tuple[Path, Path, Path]:
    source = root / "GLOBAL_RULES.md"
    policy = root / "global-agent-policy.yaml"
    profile = root / "IDE_PROFILE.yaml"
    source.write_text(GENERATED_RULE, encoding="utf-8")
    policy.write_text(yaml.safe_dump(SYNTHETIC_POLICY), encoding="utf-8")
    profile.write_text(yaml.safe_dump(SYNTHETIC_PROFILE), encoding="utf-8")
    return source, policy, profile


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
        generated = (REPO_ROOT / "ide-profiles" / "cursor" / "GLOBAL_RULES.md").read_text(encoding="utf-8")
        self.assertIn("alwaysApply: true", content)
        self.assertIn("description: Current AgentCore foundation policy for Cursor.", content)
        self.assertNotIn("Serena-centered", content.split("---", 2)[1])
        self.assertTrue(content.endswith(generated))
        self.assertNotIn("STAGING ONLY", content)
        self.assertTrue(str(CURSOR_GLOBAL_RULE).endswith("agentcore-foundation.mdc"))

    def test_validator_requires_exact_current_generated_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
            ):
                expected = maintenance._cursor_global_rule_content()
                target.write_text(expected, encoding="utf-8")
                maintenance._validate_cursor_global_rule(target)
                target.write_text(expected + NFA_SECTION, encoding="utf-8")
                maintenance._validate_cursor_global_rule(target)
                target.write_text(expected.replace("Current foundation", "Altered foundation"), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "current active Cursor foundation rule"):
                    maintenance._validate_cursor_global_rule(target)

    def test_install_preserves_nfa_appendix_and_backs_up_original(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            backups = root / "backups"
            original = (
                "---\ndescription: Old foundation\nalwaysApply: true\n---\n\n"
                "> **DERIVED FILE.** Generated from policy_revision 2026-07-26.\n"
                "\n## Mandatory rules\n\nOld foundation content.\n"
                + NFA_SECTION
            )
            target.write_text(original, encoding="utf-8")
            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", backups),
            ):
                self.assertTrue(maintenance.install_cursor_rule(approval_id="AUTH-TEST", dry_run=True)["changed"])
                self.assertEqual(target.read_text(encoding="utf-8"), original)
                result = maintenance.install_cursor_rule(approval_id="AUTH-TEST")
                expected = maintenance._cursor_global_rule_content() + NFA_SECTION
                self.assertEqual(target.read_text(encoding="utf-8"), expected)
                backup = Path(result["backup_dir"]) / "agentcore-foundation.mdc.before"
                self.assertEqual(backup.read_text(encoding="utf-8"), original)
                self.assertFalse(maintenance.install_cursor_rule(approval_id="AUTH-TEST", dry_run=True)["changed"])

    def test_stale_rendering_blocks_install_before_backup_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            backups = root / "backups"
            newer_policy = {**SYNTHETIC_POLICY, "policy_revision": "2099-01-02-newer"}
            policy.write_text(yaml.safe_dump(newer_policy), encoding="utf-8")
            original = "Existing Cursor rule.\n" + NFA_SECTION
            target.write_text(original, encoding="utf-8")
            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", backups),
            ):
                for dry_run in (True, False):
                    with self.assertRaisesRegex(ValueError, "policy revision"):
                        maintenance.install_cursor_rule(approval_id="AUTH-TEST", dry_run=dry_run)
                self.assertEqual(target.read_text(encoding="utf-8"), original)
                self.assertFalse(backups.exists())

    def test_same_revision_with_stale_body_blocks_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            backups = root / "backups"
            source.write_text(
                GENERATED_RULE.replace("Current foundation content.", "Stale foundation content."),
                encoding="utf-8",
            )
            original = "Existing Cursor rule.\n" + NFA_SECTION
            target.write_text(original, encoding="utf-8")
            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", backups),
            ):
                for dry_run in (True, False):
                    with self.assertRaisesRegex(ValueError, "stale"):
                        maintenance.install_cursor_rule(approval_id="AUTH-TEST", dry_run=dry_run)
                self.assertEqual(target.read_text(encoding="utf-8"), original)
                self.assertFalse(backups.exists())

    def test_partial_backup_failure_never_restores_partial_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            original = ("Existing Cursor rule.\n" + NFA_SECTION).encode("utf-8")
            target.write_bytes(original)

            def interrupted_copy(_source: Path, backup: Path) -> None:
                backup.write_bytes(original[:8])
                raise OSError("copy interrupted")

            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", root / "backups"),
                patch.object(maintenance.shutil, "copy2", side_effect=interrupted_copy),
            ):
                with self.assertRaisesRegex(OSError, "copy interrupted"):
                    maintenance.install_cursor_rule(approval_id="AUTH-TEST")
            self.assertEqual(target.read_bytes(), original)

    def test_truncated_backup_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            original = ("Existing Cursor rule.\n" + NFA_SECTION).encode("utf-8")
            target.write_bytes(original)

            def truncated_copy(_source: Path, backup: Path) -> Path:
                backup.write_bytes(original[:8])
                return backup

            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", root / "backups"),
                patch.object(maintenance.shutil, "copy2", side_effect=truncated_copy),
            ):
                with self.assertRaisesRegex(RuntimeError, "backup is incomplete"):
                    maintenance.install_cursor_rule(approval_id="AUTH-TEST")
            self.assertEqual(target.read_bytes(), original)

    def test_target_change_after_backup_aborts_without_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            original = ("Existing Cursor rule.\n" + NFA_SECTION).encode("utf-8")
            changed = b"Third-party Cursor edit.\n"
            target.write_bytes(original)
            real_copy = maintenance.shutil.copy2

            def copy_then_change(source_path: Path, backup: Path) -> None:
                real_copy(source_path, backup)
                target.write_bytes(changed)

            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", root / "backups"),
                patch.object(maintenance.shutil, "copy2", side_effect=copy_then_change),
            ):
                with self.assertRaisesRegex(RuntimeError, "changed"):
                    maintenance.install_cursor_rule(approval_id="AUTH-TEST")
            self.assertEqual(target.read_bytes(), changed)

    def test_post_write_third_party_change_is_not_rolled_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            target.write_text("Existing Cursor rule.\n" + NFA_SECTION, encoding="utf-8")
            changed = b"Third-party Cursor edit after install.\n"

            def change_then_fail(_path: Path, _appendix: str) -> None:
                target.write_bytes(changed)
                raise ValueError("validation failed")

            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", root / "backups"),
                patch.object(maintenance, "_validate_cursor_global_rule", side_effect=change_then_fail),
            ):
                with self.assertRaisesRegex(ValueError, "validation failed"):
                    maintenance.install_cursor_rule(approval_id="AUTH-TEST")
            self.assertEqual(target.read_bytes(), changed)

    def test_validation_failure_restores_verified_original_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, policy, profile = _write_cursor_sources(root)
            target = root / "agentcore-foundation.mdc"
            original = ("Existing Cursor rule.\n" + NFA_SECTION).replace("\n", "\r\n").encode("utf-8")
            target.write_bytes(original)
            with (
                patch.object(maintenance, "CURSOR_GENERATED_RULE", source),
                patch.object(maintenance, "GLOBAL_AGENT_POLICY", policy),
                patch.object(maintenance, "CURSOR_IDE_PROFILE", profile),
                patch.object(maintenance, "CURSOR_GLOBAL_RULE", target),
                patch.object(maintenance, "BACKUP_ROOT", root / "backups"),
                patch.object(
                    maintenance,
                    "_validate_cursor_global_rule",
                    side_effect=ValueError("validation failed"),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "validation failed"):
                    maintenance.install_cursor_rule(approval_id="AUTH-TEST")
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
