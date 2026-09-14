"""Exact-match default-deny tests for agentcore_project_boundary."""

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


def _contract(projects: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "default_policy": "deny",
        "projects": projects,
        "foreign_markers": ["swarmclaw", "swarmvault"],
        "foreign_roots": [r"H:\SwarmData"],
    }


class ExactEnrollmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.contract_path = Path(self._temp.name) / "enrollment.json"
        self.contract_path.write_text(
            json.dumps(
                _contract(
                    [
                        {
                            "project_key": "nfa-platform",
                            "name": "NFA Platform",
                            "paths": [
                                r"D:\github\nfa-platform",
                                r"D:\agentcore-worktrees\nfa-platform",
                                r"D:\agentcore-worktrees\nfa-platform\goal-staging-001",
                            ],
                        }
                    ]
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._prior = os.environ.get(CONTRACT_ENV)
        os.environ[CONTRACT_ENV] = str(self.contract_path)

    def tearDown(self) -> None:
        if self._prior is None:
            os.environ.pop(CONTRACT_ENV, None)
        else:
            os.environ[CONTRACT_ENV] = self._prior
        self._temp.cleanup()

    def test_exact_paths_are_enrolled(self) -> None:
        for path in (
            r"D:\github\nfa-platform",
            r"D:\agentcore-worktrees\nfa-platform",
            r"D:\agentcore-worktrees\nfa-platform\goal-staging-001",
        ):
            project = require_enrolled_path(path)
            self.assertEqual(project["project_key"], "nfa-platform")

    def test_parent_enrollment_does_not_admit_unenrolled_sibling(self) -> None:
        sibling = r"D:\agentcore-worktrees\nfa-platform\goal-unspecified-002"
        self.assertIsNone(match_enrolled_path(sibling))
        with self.assertRaises(ProjectBoundaryError) as raised:
            require_enrolled_path(sibling)
        self.assertEqual(str(raised.exception), "project_not_enrolled")

    def test_parent_enrollment_does_not_admit_nested_child(self) -> None:
        child = r"D:\agentcore-worktrees\nfa-platform\goal-staging-001\apps"
        self.assertIsNone(match_enrolled_path(child))
        with self.assertRaises(ProjectBoundaryError) as raised:
            require_enrolled_path(child)
        self.assertEqual(str(raised.exception), "project_not_enrolled")

    def test_swarm_path_is_refused(self) -> None:
        with self.assertRaises(ProjectBoundaryError) as raised:
            match_enrolled_path(r"H:\SwarmData\anything")
        self.assertEqual(str(raised.exception), "swarm_project_refused")


if __name__ == "__main__":
    unittest.main()
