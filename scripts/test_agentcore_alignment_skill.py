from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
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
    APPROVED_NAMES = [
        "agentcore-project-lifecycle",
        "langfuse",
        "nia",
        "agentcore-tool-discovery",
        "morph-source-workflows",
        "zoo-roo-code-workflows",
    ]

    @staticmethod
    def skill_record(
        name: str,
        source_root: str = "repository_skills",
        status: str = "approved",
        publication_allowed: bool | None = True,
    ) -> dict:
        record = {
            "name": name,
            "source_root": source_root,
            "source_path": name,
            "status": status,
        }
        if publication_allowed is not None:
            record["publication_allowed"] = publication_allowed
        return record

    @staticmethod
    def native_hosts() -> list[dict]:
        return [
            {
                "host": "zed",
                "delivery": "native_skill",
                "target": r"{userprofile}\.agents\skills\agentcore-project-lifecycle",
                "validation": "fresh_task_required",
            },
            {
                "host": "codex",
                "delivery": "native_skill",
                "target": r"{userprofile}\.agents\skills\agentcore-project-lifecycle",
                "validation": "fresh_task_required",
            },
        ]

    def test_publication_selection_defaults_and_enumerates_all_approved(self):
        publication = {
            "skills": [self.skill_record(name) for name in self.APPROVED_NAMES]
        }

        default = installer.select_publication_records(publication)
        all_approved = installer.select_publication_records(
            publication, all_approved=True
        )
        requested = installer.select_publication_records(
            publication,
            requested_skills=["nia", "langfuse"],
        )

        self.assertEqual([record["name"] for record in default], [self.APPROVED_NAMES[0]])
        self.assertEqual(
            [record["name"] for record in all_approved], self.APPROVED_NAMES
        )
        self.assertEqual(
            [record["name"] for record in requested], ["nia", "langfuse"]
        )

    def test_publication_selection_rejects_unauthorized_records(self):
        cases = [
            (self.skill_record("denied", status="rejected"), "denied"),
            (self.skill_record("blocked", publication_allowed=False), "blocked"),
            (self.skill_record("missing", publication_allowed=None), "missing"),
        ]
        for record, name in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(RuntimeError, "not approved for publication"):
                    installer.select_publication_records(
                        {"skills": [record]}, requested_skills=[name]
                    )

        with self.assertRaisesRegex(RuntimeError, "unknown skill"):
            installer.select_publication_records(
                {"skills": [self.skill_record("langfuse")]},
                requested_skills=["not-published"],
            )

    def test_skill_source_resolution_is_bounded_to_declared_root(self):
        with temporary_root() as root, patch.object(installer, "REPO_ROOT", root / "repo"), patch.dict(
            os.environ, {"USERPROFILE": str(root / "user")}
        ):
            repository_source = root / "repo" / ".agents" / "skills" / "langfuse"
            user_source = root / "user" / ".agents" / "skills" / "nia"
            repository_source.mkdir(parents=True)
            user_source.mkdir(parents=True)

            self.assertEqual(
                installer.resolve_skill_source(self.skill_record("langfuse")),
                repository_source.resolve(),
            )
            self.assertEqual(
                installer.resolve_skill_source(
                    self.skill_record("nia", source_root="user_skills")
                ),
                user_source.resolve(),
            )

            invalid = [
                {**self.skill_record("langfuse"), "source_path": "../langfuse"},
                {**self.skill_record("langfuse"), "source_path": "nested/langfuse"},
                {**self.skill_record("langfuse"), "source_path": "nia"},
                self.skill_record("langfuse", source_root="other"),
            ]
            for record in invalid:
                with self.subTest(record=record):
                    with self.assertRaises(RuntimeError):
                        installer.resolve_skill_source(record)

            with self.assertRaisesRegex(RuntimeError, "skill source missing"):
                installer.resolve_skill_source(self.skill_record("absent"))

    def test_priority_client_targets_are_exact_and_bounded(self):
        with temporary_root() as root, patch.dict(os.environ, {"USERPROFILE": str(root)}):
            zed = installer.approved_target(
                "zed", r"{userprofile}\.agents\skills\agentcore-project-lifecycle"
            )
            eigent = installer.approved_target(
                "eigent", r"{userprofile}\.eigent\skills\agentcore-project-lifecycle"
            )
            self.assertEqual(zed.name, "agentcore-project-lifecycle")
            self.assertEqual(eigent.name, "agentcore-project-lifecycle")
            self.assertNotEqual(zed.parent, eigent.parent)

    def test_approved_target_rejects_broadened_manifest_path(self):
        with temporary_root() as root, patch.dict(os.environ, {"USERPROFILE": str(root)}):
            with self.assertRaisesRegex(RuntimeError, "unapproved target"):
                installer.approved_target("cursor", r"{userprofile}\.cursor\skills")

    def test_approved_target_derives_only_an_exact_dynamic_leaf(self):
        with temporary_root() as root, patch.dict(os.environ, {"USERPROFILE": str(root)}):
            target = installer.approved_target(
                "cursor",
                r"{userprofile}\.cursor\skills\agentcore-project-lifecycle",
                "langfuse",
            )
            self.assertEqual(target, (root / ".cursor" / "skills" / "langfuse").resolve())

            with self.assertRaisesRegex(RuntimeError, "unsafe skill name"):
                installer.approved_target(
                    "cursor",
                    r"{userprofile}\.cursor\skills\agentcore-project-lifecycle",
                    "../langfuse",
                )

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
            self.assertEqual(
                (backup_run / "cursor" / "agentcore-project-lifecycle" / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "old",
            )
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
            self.assertEqual(
                (backup_run / "cursor" / "agentcore-project-lifecycle" / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "old",
            )
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
            self.assertEqual(
                (backup_run / "cursor" / "agentcore-project-lifecycle" / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "old",
            )
            self.assertEqual(len(list(target.parent.glob(".agentcore-project-lifecycle.failed-*"))), 1)

    def test_dynamic_skill_backup_and_restore_uses_skill_leaf(self):
        with temporary_root() as root:
            source = root / "source" / "langfuse"
            target = root / "skills" / "langfuse"
            backup_run = root / "backups" / "run"
            source.mkdir(parents=True)
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
                    installer.backup_and_replace(
                        source, target, backup_run, "cursor", source_hash
                    )

            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "old")
            self.assertEqual(
                (backup_run / "cursor" / "langfuse" / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "old",
            )
            self.assertFalse(list(target.parent.glob(".langfuse.staging-*")))
            self.assertFalse(list(target.parent.glob(".langfuse.prior-*")))
            self.assertFalse(list(target.parent.glob(".langfuse.failed-*")))

    def test_shared_native_target_is_replaced_once(self):
        with temporary_root() as root, patch.object(installer, "REPO_ROOT", root / "repo"), patch.dict(
            os.environ, {"USERPROFILE": str(root / "user")}
        ):
            source = root / "repo" / ".agents" / "skills" / "langfuse"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            manifest = {"hosts": self.native_hosts()}
            records = [self.skill_record("langfuse")]
            real_replace = installer.backup_and_replace

            with patch.object(
                installer, "backup_and_replace", wraps=real_replace
            ) as replace:
                payload = installer.execute_installation(
                    manifest, records, True, root / "backups" / "run"
                )

            self.assertEqual(replace.call_count, 1)
            self.assertEqual(
                (root / "user" / ".agents" / "skills" / "langfuse" / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "new",
            )
            self.assertEqual(len(payload["skills"][0]["hosts"]), 2)

    def test_source_equal_target_is_a_no_op(self):
        with temporary_root() as root, patch.object(installer, "REPO_ROOT", root / "repo"), patch.dict(
            os.environ, {"USERPROFILE": str(root / "user")}
        ):
            source = root / "user" / ".agents" / "skills" / "nia"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("same", encoding="utf-8")
            records = [self.skill_record("nia", source_root="user_skills")]

            with patch.object(
                installer,
                "backup_and_replace",
                side_effect=AssertionError("source-to-self replacement attempted"),
            ) as replace:
                payload = installer.execute_installation(
                    {"hosts": self.native_hosts()}, records, True, root / "backups"
                )

            replace.assert_not_called()
            statuses = {host["status"] for host in payload["skills"][0]["hosts"]}
            self.assertEqual(statuses, {"source_target_same"})

    def test_conflicting_sources_for_one_target_are_rejected_before_mutation(self):
        with temporary_root() as root, patch.object(installer, "REPO_ROOT", root / "repo"), patch.dict(
            os.environ, {"USERPROFILE": str(root / "user")}
        ):
            for name in ("langfuse", "agentcore-tool-discovery"):
                source = root / "repo" / ".agents" / "skills" / name
                source.mkdir(parents=True)
                (source / "SKILL.md").write_text(name, encoding="utf-8")
            collision = root / "user" / ".cursor" / "skills" / "collision"

            with patch.object(installer, "approved_target", return_value=collision), patch.object(
                installer,
                "backup_and_replace",
                side_effect=AssertionError("mutation attempted before conflict rejection"),
            ) as replace:
                with self.assertRaisesRegex(RuntimeError, "conflicting skill target"):
                    installer.execute_installation(
                        {"hosts": [self.native_hosts()[0]]},
                        [
                            self.skill_record("langfuse"),
                            self.skill_record("agentcore-tool-discovery"),
                        ],
                        True,
                        root / "backups",
                    )

            replace.assert_not_called()

    def test_non_native_hosts_remain_report_only(self):
        with temporary_root() as root, patch.object(installer, "REPO_ROOT", root / "repo"), patch.dict(
            os.environ, {"USERPROFILE": str(root / "user")}
        ):
            source = root / "repo" / ".agents" / "skills" / "langfuse"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("source", encoding="utf-8")
            manifest = {
                "hosts": [
                    {
                        "host": "claude-desktop",
                        "delivery": "generated_rule_adapter",
                        "source": "ide-profiles/claude-desktop/GLOBAL_RULES.md",
                        "validation": "manual_import",
                    }
                ]
            }

            with patch.object(
                installer,
                "backup_and_replace",
                side_effect=AssertionError("non-native mutation attempted"),
            ) as replace:
                payload = installer.execute_installation(
                    manifest,
                    [self.skill_record("langfuse")],
                    True,
                    root / "backups",
                )

            replace.assert_not_called()
            host = payload["skills"][0]["hosts"][0]
            self.assertEqual(host["status"], "manual_import")
            self.assertEqual(host["source"], manifest["hosts"][0]["source"])

    def test_cli_selectors_are_exclusive_and_default_payload_is_legacy_compatible(self):
        with self.assertRaises(SystemExit):
            installer.parse_args(["--all-approved", "--skill", "langfuse"])

        with temporary_root() as root, patch.object(installer, "REPO_ROOT", root / "repo"), patch.object(
            installer, "MANIFEST", root / "manifest.json"
        ), patch.object(
            installer, "PUBLICATION_CONTRACT", root / "publication.json"
        ), patch.object(
            installer, "BACKUP_ROOT", root / "backups"
        ), patch.dict(os.environ, {"USERPROFILE": str(root / "user")}):
            source = root / "repo" / ".agents" / "skills" / "agentcore-project-lifecycle"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("source", encoding="utf-8")
            installer.MANIFEST.write_text(
                json.dumps({"hosts": self.native_hosts()}), encoding="utf-8"
            )
            installer.PUBLICATION_CONTRACT.write_text(
                json.dumps(
                    {"skills": [self.skill_record("agentcore-project-lifecycle")]}
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                return_code = installer.main(["--json"])

            payload = json.loads(output.getvalue())
            self.assertEqual(return_code, 0)
            self.assertEqual(payload["mode"], "check")
            self.assertEqual(
                [skill["name"] for skill in payload["skills"]],
                ["agentcore-project-lifecycle"],
            )
            self.assertEqual(payload["source"], str(source.resolve()))
            self.assertEqual(payload["source_sha256"], installer.tree_digest(source))


if __name__ == "__main__":
    unittest.main()
