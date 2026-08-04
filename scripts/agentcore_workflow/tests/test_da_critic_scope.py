"""Regression coverage for bounded Deep Agents critic assignments."""

from __future__ import annotations

from agentcore_workflow.deepagents_worker import (
    DEFAULT_CRITIC_MAX_ITER,
    _worker_invoke_config,
)
from agentcore_workflow.nodes import node_da_critic
from agentcore_workflow.state import initial_state


def test_critic_without_file_changes_reviews_only_builder_output(monkeypatch, tmp_path):
    """A no-change worker result must not trigger an open-ended repository review."""
    captured: dict = {}

    def fake_critic_worker(**kwargs):
        captured.update(kwargs)
        return {
            "status": "completed",
            "passed": True,
            "score": 1.0,
            "findings": [],
        }

    monkeypatch.setattr(
        "agentcore_workflow.deepagents_worker.DEEPAGENTS_AVAILABLE", True
    )
    monkeypatch.setattr(
        "agentcore_workflow.deepagents_worker.run_critic_worker",
        fake_critic_worker,
    )

    state = dict(initial_state("project-id", "project-key", "thread-id"))
    state.update(
        {
            "current_micro_key": "CANARY.1.1",
            "worktree_path": str(tmp_path),
            "da_builder_result": {
                "status": "completed",
                "output": "CE021_CANARY_OK",
                "files_changed": [],
            },
        }
    )

    result = node_da_critic(state)

    assert result["next_action"] == "post_exec_judge"
    assert "CE021_CANARY_OK" in captured["task"]
    assert "No files changed" in captured["task"]
    assert "Do not inspect the repository" in captured["task"]


def test_critic_with_file_changes_receives_exact_review_scope(monkeypatch, tmp_path):
    """A code-changing worker result must name the files the critic may inspect."""
    captured: dict = {}

    def fake_critic_worker(**kwargs):
        captured.update(kwargs)
        return {
            "status": "completed",
            "passed": True,
            "score": 1.0,
            "findings": [],
        }

    monkeypatch.setattr(
        "agentcore_workflow.deepagents_worker.DEEPAGENTS_AVAILABLE", True
    )
    monkeypatch.setattr(
        "agentcore_workflow.deepagents_worker.run_critic_worker",
        fake_critic_worker,
    )

    state = dict(initial_state("project-id", "project-key", "thread-id"))
    state.update(
        {
            "current_micro_key": "BUILD.1.1",
            "worktree_path": str(tmp_path),
            "da_builder_result": {
                "status": "completed",
                "output": "Implemented the bounded change.",
                "files_changed": ["src/service.py", "tests/test_service.py"],
            },
        }
    )

    node_da_critic(state)

    assert "Inspect only these changed files" in captured["task"]
    assert "- src/service.py" in captured["task"]
    assert "- tests/test_service.py" in captured["task"]
    assert "Implemented the bounded change." in captured["task"]


def test_worker_iteration_budget_uses_langgraph_recursion_limit() -> None:
    config = _worker_invoke_config(
        role="builder",
        thread_uuid="thread-id",
        max_iterations=3,
    )

    assert config["recursion_limit"] == 25
    assert "max_iterations" not in config["configurable"]


def test_critic_default_budget_allows_bounded_read_and_review_cycle() -> None:
    assert DEFAULT_CRITIC_MAX_ITER == 4
    config = _worker_invoke_config(
        role="critic",
        thread_uuid="thread-id",
        max_iterations=DEFAULT_CRITIC_MAX_ITER,
    )

    assert config["recursion_limit"] == 33
