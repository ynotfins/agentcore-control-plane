from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("install_agentcore_alignment_skill.py")
SPEC = importlib.util.spec_from_file_location("alignment_installer", SCRIPT)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


@contextmanager
def temporary_root():
    with tempfile.TemporaryDirectory() as value:
        yield Path(value)


class AlignmentInstallerTests(unittest.TestCase):
    def test_approved_target_rejects_broadened_manifest_path(self):
        with temporary_root() as root, patch.dict(os.environ, {"USERPROFILE": str(root)}):
            with self.assertRaisesRegex(RuntimeError, "unapproved target"):
                installer.approved_target("cursor", r"{userprofile}\.cursor\skills")

    def test_backup_and_replace_is_hash_verified(self):
        with temporary_root() as root:
            source = root / "source"
            target = root / "skills" / "agentcore-project-lifecycle"
            backup_run = root / "backups" / "run"
            source.mkdir()
            target.mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (target / "SKILL.md").write_text("old", encoding="utf-8")
            source_hash = installer.tree_digest(source)

            installer.backup_and_replace(source, target, backup_run, "cursor", source_hash)

            self.assertEqual(installer.tree_digest(target), source_hash)
            self.assertEqual((backup_run / "cursor" / "SKILL.md").read_text(encoding="utf-8"), "old")
            self.assertFalse(list(target.parent.glob(".agentcore-project-lifecycle.*-*")))

    def test_failed_post_swap_verification_restores_prior(self):
        with temporary_root() as root:
            source = root / "source"
            target = root / "skills" / "agentcore-project-lifecycle"
            backup_run = root / "backups" / "run"
            source.mkdir()
            target.mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (target / "SKILL.md").write_text("old", encoding="utf-8")
            source_hash = installer.tree_digest(source)
            real_digest = installer.tree_digest

            def fail_new_target(path: Path) -> str:
                if path.resolve(strict=False) == target.resolve(strict=False):
                    skill = path / "SKILL.md"
                    if skill.is_file() and skill.read_text(encoding="utf-8") == "new":
                        return "forced-post-swap-mismatch"
                return real_digest(path)

            with patch.object(installer, "tree_digest", side_effect=fail_new_target):
                with self.assertRaisesRegex(RuntimeError, "installed skill digest mismatch"):
                    installer.backup_and_replace(source, target, backup_run, "cursor", source_hash)

            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "old")
            self.assertEqual((backup_run / "cursor" / "SKILL.md").read_text(encoding="utf-8"), "old")
            self.assertFalse(list(target.parent.glob(".agentcore-project-lifecycle.*-*")))

    def test_cleanup_lock_cannot_prevent_prior_restore(self):
        with temporary_root() as root:
            source = root / "source"
            target = root / "skills" / "agentcore-project-lifecycle"
            backup_run = root / "backups" / "run"
            source.mkdir()
            target.mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (target / "SKILL.md").write_text("old", encoding="utf-8")
            source_hash = installer.tree_digest(source)
            real_digest = installer.tree_digest
            real_cleanup = installer.remove_exact_staging

            def fail_new_target(path: Path) -> str:
                if path.resolve(strict=False) == target.resolve(strict=False):
                    skill = path / "SKILL.md"
                    if skill.is_file() and skill.read_text(encoding="utf-8") == "new":
                        return "forced-post-swap-mismatch"
                return real_digest(path)

            def lock_failed_cleanup(path: Path, parent: Path, marker: str) -> None:
                if marker == ".failed-":
                    raise PermissionError("forced cleanup lock")
                real_cleanup(path, parent, marker)

            with patch.object(installer, "tree_digest", side_effect=fail_new_target), patch.object(
                installer, "remove_exact_staging", side_effect=lock_failed_cleanup
            ):
                with self.assertRaisesRegex(RuntimeError, "installed skill digest mismatch"):
                    installer.backup_and_replace(source, target, backup_run, "cursor", source_hash)

            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "old")
            self.assertEqual((backup_run / "cursor" / "SKILL.md").read_text(encoding="utf-8"), "old")
            self.assertEqual(len(list(target.parent.glob(".agentcore-project-lifecycle.failed-*"))), 1)


if __name__ == "__main__":
    unittest.main()
