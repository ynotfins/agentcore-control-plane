from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore import workflow_cli  # noqa: E402


class WorkflowCliProjectBoundaryTests(unittest.TestCase):
    def test_init_rejects_existing_unregistered_target_before_database_write(self) -> None:
        fixture_parent = Path(r"D:\agentcore-fixture")
        fixture_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=fixture_parent) as temp_dir:
            args = argparse.Namespace(
                project_key="unregistered-project",
                project_name=None,
                target=temp_dir,
                git_remote=None,
                worktree=None,
                json=False,
            )
            with patch.object(workflow_cli, "_ensure_project") as ensure_project:
                result = workflow_cli.cmd_init(args)

        self.assertEqual(result, 2)
        ensure_project.assert_not_called()

    def test_init_rejects_unregistered_worktree_before_database_write(self) -> None:
        fixture_parent = Path(r"D:\agentcore-fixture")
        fixture_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=fixture_parent) as temp_dir:
            args = argparse.Namespace(
                project_key="agentcore-control-plane",
                project_name=None,
                target=r"D:\github\agentcore-control-plane",
                git_remote=None,
                worktree=temp_dir,
                json=False,
            )
            with patch.object(workflow_cli, "_ensure_project") as ensure_project:
                result = workflow_cli.cmd_init(args)

        self.assertEqual(result, 2)
        ensure_project.assert_not_called()

    def test_init_does_not_register_project_when_worktree_creation_fails(self) -> None:
        args = argparse.Namespace(
            project_key="agentcore-control-plane",
            project_name=None,
            target=r"D:\github\agentcore-control-plane",
            git_remote=None,
            worktree=r"D:\agentcore-worktrees\agentcore-control-plane",
            json=False,
        )
        with (
            patch.object(workflow_cli, "validate_project_identity", return_value={}),
            patch.object(Path, "mkdir", side_effect=OSError("simulated mkdir failure")),
            patch.object(workflow_cli, "_ensure_project") as ensure_project,
        ):
            result = workflow_cli.cmd_init(args)

        self.assertEqual(result, 2)
        ensure_project.assert_not_called()


if __name__ == "__main__":
    unittest.main()
