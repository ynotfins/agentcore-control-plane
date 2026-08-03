from __future__ import annotations

from contextlib import contextmanager

from agentcore_workflow import db


class _Connection:
    def __init__(self) -> None:
        self.query = ""
        self.params: list[object] = []

    def execute(self, query: str, params: list[object]) -> None:
        self.query = query
        self.params = params


def _capture(monkeypatch) -> _Connection:
    connection = _Connection()

    @contextmanager
    def _conn(*, admin: bool = False):
        assert admin is True
        yield connection

    monkeypatch.setattr(db, "conn", _conn)
    return connection


def test_completed_run_sets_terminal_timestamp(monkeypatch) -> None:
    connection = _capture(monkeypatch)

    db.update_run_status("run-id", "completed")

    assert "completed_at = COALESCE(completed_at, now())" in connection.query


def test_running_run_clears_prior_terminal_timestamp(monkeypatch) -> None:
    connection = _capture(monkeypatch)

    db.update_run_status("run-id", "running")

    assert "completed_at = NULL" in connection.query
