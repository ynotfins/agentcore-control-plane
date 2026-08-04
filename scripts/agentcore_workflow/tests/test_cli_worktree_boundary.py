from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from agentcore import workflow_cli
from agentcore_workflow.state import initial_state


def _git(*args: str, cwd: Path) -> None:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def _init_repo(path: Path) -> None:
    path.mkdir()
    _git("init", cwd=path)
    (path / "README.md").write_text("fixture", encoding="utf-8")
    _git("add", "README.md", cwd=path)
    _git(
        "-c", "user.name=AgentCore Test", "-c", "user.email=test@agentcore.invalid",
        "commit", "-m", "fixture", cwd=path,
    )


def test_authorized_input_file_is_resolved_inside_assigned_worktree(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    goal = worktree / "project" / "goal.md"
    goal.parent.mkdir()
    goal.write_text("goal", encoding="utf-8")

    resolved = workflow_cli._authorized_workflow_input("project/goal.md", worktree)

    assert resolved == goal.resolve()


def test_authorized_input_file_rejects_path_outside_assigned_worktree(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError, match="outside_assigned_worktree"):
        workflow_cli._authorized_workflow_input(str(outside), worktree)


def test_initial_state_preserves_selected_worktree(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    worktree = tmp_path / "worktree"
    state = initial_state(
        "project-id",
        "project-key",
        "thread-id",
        project_root=str(canonical),
        worktree_path=str(worktree),
    )

    assert state["project_root"] == str(canonical.resolve())
    assert state["worktree_path"] == str(worktree.resolve())


def test_resolved_project_requires_persisted_primary_worktree(monkeypatch) -> None:
    class _Cursor:
        def execute(self, _query, _params):
            return self

        def fetchone(self):
            return {
                "id": "project-id",
                "project_key": "project-key",
                "project_name": "Project",
                "root_path": r"D:\github\project",
                "current_milestone": "M6",
                "trust_class": "project_verified",
                "worktree_path": None,
                "canonical_repo_path": None,
            }

    class _Connection:
        def __enter__(self):
            return _Cursor()

        def __exit__(self, *_args):
            return False

    class _Psycopg:
        @staticmethod
        def connect(*_args, **_kwargs):
            return _Connection()

    monkeypatch.setattr(workflow_cli, "_import_psycopg", lambda: (_Psycopg, object()))
    monkeypatch.setattr(workflow_cli, "_pg_conninfo", lambda: "test")

    project = workflow_cli._resolve_project("project-key")

    assert project is not None
    assert project["worktree_path"] is None


def test_existing_worktree_must_belong_to_canonical_repository(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    unrelated = tmp_path / "unrelated"
    _init_repo(canonical)
    _init_repo(unrelated)

    with pytest.raises(ValueError, match="different_repository"):
        workflow_cli._ensure_git_worktree(canonical, unrelated)


def test_created_worktree_is_verified_against_canonical_repository(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    worktree = tmp_path / "worktree"
    _init_repo(canonical)

    workflow_cli._ensure_git_worktree(canonical, worktree)

    assert worktree.is_dir()
    assert workflow_cli._git_common_dir(canonical) == workflow_cli._git_common_dir(worktree)


def test_workflow_result_with_terminal_error_is_not_success() -> None:
    assert not workflow_cli._workflow_result_ok(
        {"completed": True, "judge_verdict": "proceed", "errors": ["gate failed"]}
    )


def test_workflow_result_requires_terminal_success_signal() -> None:
    assert workflow_cli._workflow_result_ok(
        {"completed": True, "judge_verdict": "proceed", "errors": []}
    )
    assert not workflow_cli._workflow_result_ok(
        {"completed": False, "judge_verdict": "", "errors": []}
    )
