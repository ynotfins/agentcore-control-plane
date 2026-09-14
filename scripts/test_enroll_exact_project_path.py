"""Tests for the Cursor/operator exact-path enrollment helper."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore_project_boundary import (  # noqa: E402
    CONTRACT_ENV,
    ProjectBoundaryError,
    match_enrolled_path,
    require_enrolled_path,
)
from enroll_exact_project_path import add_exact_enrolled_path  # noqa: E402


def _write_contract(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "default_policy": "deny",
                "projects": [
                    {
                        "project_key": "nfa-platform",
                        "name": "NFA Platform",
                        "paths": [r"D:\github\nfa-platform"],
                    }
                ],
                "foreign_markers": ["swarmclaw"],
                "foreign_roots": [r"H:\SwarmData"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class EnrollExactProjectPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        root = Path(self._temp.name)
        self.contract_path = root / "enrollment.json"
        self.rollback_root = root / "rollback"
        self.new_path = root / "goal-staging-001"
        self.new_path.mkdir()
        _write_contract(self.contract_path)
        self._prior = os.environ.get(CONTRACT_ENV)
        os.environ[CONTRACT_ENV] = str(self.contract_path)

    def tearDown(self) -> None:
        if self._prior is None:
            os.environ.pop(CONTRACT_ENV, None)
        else:
            os.environ[CONTRACT_ENV] = self._prior
        self._temp.cleanup()

    def test_devin_caller_is_rejected(self) -> None:
        with self.assertRaises(ProjectBoundaryError) as raised:
            add_exact_enrolled_path(
                project_key="nfa-platform",
                path=str(self.new_path),
                caller="devin",
                contract_path=self.contract_path,
            )
        self.assertEqual(str(raised.exception), "caller_not_authorized")
        self.assertIsNone(match_enrolled_path(self.new_path))

    def test_wildcard_path_is_rejected(self) -> None:
        with self.assertRaises(ProjectBoundaryError) as raised:
            add_exact_enrolled_path(
                project_key="nfa-platform",
                path=r"D:\agentcore-worktrees\nfa-platform\*",
                caller="cursor",
                contract_path=self.contract_path,
                require_exists=False,
            )
        self.assertEqual(str(raised.exception), "exact_path_required")

    def test_adds_exact_path_and_keeps_sibling_denied(self) -> None:
        result = add_exact_enrolled_path(
            project_key="nfa-platform",
            path=str(self.new_path),
            caller="operator",
            contract_path=self.contract_path,
            rollback_root=self.rollback_root,
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["already_enrolled"])
        self.assertTrue(Path(result["rollback"]).exists())
        self.assertEqual(require_enrolled_path(self.new_path)["project_key"], "nfa-platform")
        sibling = self.new_path.parent / "goal-unspecified-002"
        sibling.mkdir()
        self.assertIsNone(match_enrolled_path(sibling))

    def test_dry_run_does_not_write(self) -> None:
        result = add_exact_enrolled_path(
            project_key="nfa-platform",
            path=str(self.new_path),
            caller="cursor",
            contract_path=self.contract_path,
            dry_run=True,
        )
        self.assertTrue(result["dry_run"])
        self.assertIsNone(match_enrolled_path(self.new_path))

    def test_idempotent_when_already_enrolled(self) -> None:
        add_exact_enrolled_path(
            project_key="nfa-platform",
            path=str(self.new_path),
            caller="cursor",
            contract_path=self.contract_path,
            rollback_root=self.rollback_root,
        )
        again = add_exact_enrolled_path(
            project_key="nfa-platform",
            path=str(self.new_path),
            caller="cursor",
            contract_path=self.contract_path,
            rollback_root=self.rollback_root,
        )
        self.assertTrue(again["already_enrolled"])


if __name__ == "__main__":
    unittest.main()
