from __future__ import annotations

import argparse

import pytest

from agentcore import workflow_cli


def _start_args(*, provider: str | None = None, model: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        provider=provider,
        model=model,
        project_key="unregistered-project",
        project=None,
        risk_profile=None,
        budget_profile=None,
    )


@pytest.mark.parametrize(
    ("provider", "model", "expected_provider", "expected_model"),
    [
        (None, None, "omniroute", "deepseek-v4-pro"),
        ("omniroute", "chosen-model", "omniroute", "chosen-model"),
    ],
)
def test_cmd_start_accepts_omniroute_selection(
    monkeypatch,
    capsys,
    provider: str | None,
    model: str | None,
    expected_provider: str,
    expected_model: str,
) -> None:
    args = _start_args(provider=provider, model=model)
    monkeypatch.delenv("AGENTCORE_WORKFLOW_PROVIDER", raising=False)
    monkeypatch.delenv("AGENTCORE_WORKFLOW_MODEL", raising=False)
    monkeypatch.setattr(workflow_cli, "_resolve_project", lambda _key: None)

    assert workflow_cli.cmd_start(args) == 2

    captured = capsys.readouterr()
    assert "not supported" not in captured.err
    assert "project_key not registered" in captured.err
    assert args.provider == expected_provider
    assert args.model == expected_model


def test_cmd_start_uses_omniroute_environment_selection(monkeypatch, capsys) -> None:
    args = _start_args()
    monkeypatch.setenv("AGENTCORE_WORKFLOW_PROVIDER", "omniroute")
    monkeypatch.setenv("AGENTCORE_WORKFLOW_MODEL", "environment-model")
    monkeypatch.setattr(workflow_cli, "_resolve_project", lambda _key: None)

    assert workflow_cli.cmd_start(args) == 2

    captured = capsys.readouterr()
    assert "not supported" not in captured.err
    assert "project_key not registered" in captured.err
    assert args.provider == "omniroute"
    assert args.model == "environment-model"
