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
