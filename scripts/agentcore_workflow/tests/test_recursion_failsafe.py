"""Recursion-blowout failsafe for DA workers (deepseek/deepseek-v4.1-flash-1017 loops)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agentcore_workflow import deepagents_worker as dw  # noqa: E402


def _config(limit: int = 97) -> dict:
    return {"configurable": {"thread_id": "t"}, "recursion_limit": limit}


def test_retries_once_with_bigger_budget(monkeypatch):
    seen: list[tuple[int, bool]] = []

    def make_invoke(cfg, nudge):
        seen.append((int(cfg["recursion_limit"]), nudge))

        def _call():
            if len(seen) == 1:
                raise dw.GraphRecursionError("Recursion limit of 97 reached")
            return {"messages": []}

        return _call

    out = dw._invoke_with_recursion_failsafe(make_invoke, _config(), timeout_sec=5, on_timeout={"status": "failed"})

    assert out == {"messages": []}
    assert seen[0] == (97, False)
    assert seen[1][1] is True and seen[1][0] > 97


def test_retry_budget_is_capped(monkeypatch):
    monkeypatch.setenv("AGENTCORE_DA_RECURSION_MAX", "120")
    seen: list[int] = []

    def make_invoke(cfg, nudge):
        seen.append(int(cfg["recursion_limit"]))

        def _call():
            raise dw.GraphRecursionError("Recursion limit reached")

        return _call

    with pytest.raises(dw.GraphRecursionError):
        dw._invoke_with_recursion_failsafe(make_invoke, _config(100), timeout_sec=5, on_timeout={"status": "failed"})

    assert seen == [100, 120]


def test_no_retry_when_budget_cannot_grow(monkeypatch):
    monkeypatch.setenv("AGENTCORE_DA_RECURSION_MAX", "50")
    seen: list[int] = []

    def make_invoke(cfg, nudge):
        seen.append(int(cfg["recursion_limit"]))

        def _call():
            raise dw.GraphRecursionError("Recursion limit reached")

        return _call

    with pytest.raises(dw.GraphRecursionError):
        dw._invoke_with_recursion_failsafe(make_invoke, _config(97), timeout_sec=5, on_timeout={"status": "failed"})

    assert seen == [97]
