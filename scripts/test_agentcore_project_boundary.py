"""Exact-match and opt-in path_prefix default-deny tests for agentcore_project_boundary."""

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
    load_enrollment_contract,
    match_enrolled_path,
    require_enrolled_path,
)


def _contract(
    projects: list[dict],
    *,
    approved_path_prefix_parents: list[str] | None = None,
) -> dict:
    contract: dict = {
        "schema_version": 1,
        "default_policy": "deny",
        "projects": projects,
        "foreign_markers": ["swarmclaw", "swarmvault"],
        "foreign_roots": [r"H:\SwarmData"],
    }
    if approved_path_prefix_parents is not None:
        contract["approved_path_prefix_parents"] = approved_path_prefix_parents
    return contract


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


class PathPrefixEnrollmentTests(unittest.TestCase):
    """Opt-in path_prefix matching stays additive to exact-path enrollment."""

    PARENT = r"D:\agentcore-worktrees\nfa-platform"

    def _write(self, *, approved_path_prefix_parents, path_prefixes) -> None:
        self.contract_path.write_text(
            json.dumps(
                _contract(
                    [
                        {
                            "project_key": "nfa-platform",
                            "name": "NFA Platform",
                            "paths": [r"D:\github\nfa-platform"],
                            "path_prefixes": path_prefixes,
                        }
                    ],
                    approved_path_prefix_parents=approved_path_prefix_parents,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.contract_path = Path(self._temp.name) / "enrollment.json"
        self._prior = os.environ.get(CONTRACT_ENV)
        os.environ[CONTRACT_ENV] = str(self.contract_path)

    def tearDown(self) -> None:
        if self._prior is None:
            os.environ.pop(CONTRACT_ENV, None)
        else:
            os.environ[CONTRACT_ENV] = self._prior
        self._temp.cleanup()

    def test_child_under_allowlisted_prefix_matches(self) -> None:
        self._write(
            approved_path_prefix_parents=[self.PARENT],
            path_prefixes=[self.PARENT],
        )
        child = str(Path(self.PARENT) / "goal-staging-002")
        project = require_enrolled_path(child)
        self.assertEqual(project["project_key"], "nfa-platform")
        self.assertEqual(require_enrolled_path(self.PARENT)["project_key"], "nfa-platform")

    def test_non_prefix_sibling_still_fails(self) -> None:
        self._write(
            approved_path_prefix_parents=[self.PARENT],
            path_prefixes=[self.PARENT],
        )
        sibling = r"D:\agentcore-worktrees\other-project\goal-staging-002"
        self.assertIsNone(match_enrolled_path(sibling))
        with self.assertRaises(ProjectBoundaryError) as raised:
            require_enrolled_path(sibling)
        self.assertEqual(str(raised.exception), "project_not_enrolled")

    def test_unapproved_prefix_fails_closed_on_load(self) -> None:
        self._write(approved_path_prefix_parents=[], path_prefixes=[self.PARENT])
        with self.assertRaises(ProjectBoundaryError) as raised:
            load_enrollment_contract()
        self.assertEqual(str(raised.exception), "unapproved_path_prefix_refused")

    def test_wildcard_prefix_fails_closed_on_load(self) -> None:
        self._write(
            approved_path_prefix_parents=[self.PARENT],
            path_prefixes=[self.PARENT + r"\*"],
        )
        with self.assertRaises(ProjectBoundaryError) as raised:
            load_enrollment_contract()
        self.assertEqual(str(raised.exception), "wildcard_path_prefix_refused")

    def test_shallow_approved_parent_fails_closed_on_load(self) -> None:
        self._write(
            approved_path_prefix_parents=[r"D:\agentcore-worktrees"],
            path_prefixes=[],
        )
        with self.assertRaises(ProjectBoundaryError) as raised:
            load_enrollment_contract()
        self.assertEqual(str(raised.exception), "shallow_path_prefix_parent_refused")

    def test_foreign_approved_parent_fails_closed_on_load(self) -> None:
        self._write(
            approved_path_prefix_parents=[r"H:\SwarmData\nfa-platform"],
            path_prefixes=[],
        )
        with self.assertRaises(ProjectBoundaryError) as raised:
            load_enrollment_contract()
        self.assertEqual(str(raised.exception), "swarm_project_refused")

    def test_traversal_target_fails_closed(self) -> None:
        self._write(
            approved_path_prefix_parents=[self.PARENT],
            path_prefixes=[self.PARENT],
        )
        traversal = self.PARENT + r"\..\other-project"
        self.assertIsNone(match_enrolled_path(traversal))
        with self.assertRaises(ProjectBoundaryError) as raised:
            require_enrolled_path(traversal)
        self.assertEqual(str(raised.exception), "project_not_enrolled")


if __name__ == "__main__":
    unittest.main()