from __future__ import annotations

import json

from agentcore_memory import neutral_recall


class _Response:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_health_rejects_http_200_with_degraded_database(monkeypatch) -> None:
    monkeypatch.setattr(
        neutral_recall.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _Response(
            {"status": "degraded", "services": {"database": False}}
        ),
    )

    result = neutral_recall.recall_health()

    assert result["ok"] is False
    assert result["degraded"] is True
    assert result["failed_services"] == ["database"]


def test_health_accepts_http_200_with_healthy_services(monkeypatch) -> None:
    monkeypatch.setattr(
        neutral_recall.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _Response(
            {"status": "ok", "services": {"database": True}}
        ),
    )

    result = neutral_recall.recall_health()

    assert result["ok"] is True
    assert result["degraded"] is False
    assert result["failed_services"] == []
