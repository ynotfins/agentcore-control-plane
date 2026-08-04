"""Project identity preflight for LangGraph memory gateway callers."""

from __future__ import annotations

import pytest

from agentcore_workflow import memory_gateway


@pytest.mark.parametrize(
    ("call", "args"),
    [
        (memory_gateway.open_memory_session, ("agentcore-control-plane", "")),
        (memory_gateway.startup_context, ("agentcore-control-plane", "   ")),
        (
            memory_gateway.append_event,
            ("agentcore-control-plane", "", "session", "prompt", {"text": "x"}),
        ),
        (memory_gateway.close_memory_session, ("agentcore-control-plane", "", "session")),
    ],
)
def test_project_scoped_call_rejects_empty_root_before_tool_discovery(monkeypatch, call, args) -> None:
    def unexpected_tool_discovery(*_args, **_kwargs):
        raise AssertionError("gateway tool discovery must not run for an empty project root")

    monkeypatch.setattr(memory_gateway, "resolve_memory_tool_name", unexpected_tool_discovery)

    with pytest.raises(ValueError, match="^project_root_required$"):
        call(*args)


def test_session_open_preserves_canonical_root_and_separate_worktree(monkeypatch) -> None:
    captured = {}

    monkeypatch.setattr(
        memory_gateway,
        "resolve_memory_tool_name",
        lambda _name: "agentcore_memory-session_open",
    )

    def capture_call(tool_name, arguments):
        captured["tool_name"] = tool_name
        captured["arguments"] = arguments
        return {"ok": True}

    monkeypatch.setattr(memory_gateway, "call_gateway_tool", capture_call)

    memory_gateway.open_memory_session(
        "agentcore-context-engine",
        r"D:\github\agentcore-context-engine",
        canonical_repo_path=r"D:\github\agentcore-context-engine",
        worktree_path=r"D:\agentcore-worktrees\agentcore-context-engine",
        session_key="workflow-test",
    )

    assert captured["tool_name"] == "agentcore_memory-session_open"
    assert captured["arguments"]["project_root"] == r"D:\github\agentcore-context-engine"
    assert captured["arguments"]["canonical_repo_path"] == r"D:\github\agentcore-context-engine"
    assert captured["arguments"]["worktree_path"] == r"D:\agentcore-worktrees\agentcore-context-engine"
