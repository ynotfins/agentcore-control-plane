from __future__ import annotations

import io
import json
import sys
import urllib.error
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_ROOT = Path(__file__).resolve().parents[2]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from agentcore_memory import neutral_recall
from agentcore_memory import server


PROJECT_A = "project-a"
PROJECT_B = "project-b"
PROJECT_A_KEY = "".join(("sr_", "live_", "a" * 40))
PROJECT_B_KEY = "".join(("sr_", "live_", "b" * 40))
GLOBAL_POOL_ID = "11111111-1111-4111-8111-111111111111"
PROJECT_A_POOL_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
FOREIGN_POOL_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


class _Response:
    def __init__(self, payload: Any, status: int = 200) -> None:
        self.status = status
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _pool_payload(*, extra: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    pools = [
        {
            "id": GLOBAL_POOL_ID,
            "name": "agentcore-global-memory",
            "memoryAccess": "read",
        },
        {
            "id": PROJECT_A_POOL_ID,
            "name": f"agentcore-memory-{PROJECT_A}",
            "memoryAccess": "readwrite",
        },
    ]
    pools.extend(extra or [])
    return {"data": pools}


@pytest.fixture(autouse=True)
def _isolated_recall_environment(monkeypatch):
    for name in (
        "AGENTCORE_RECALL_API_URL",
        "AGENTCORE_RECALL_PROJECT_KEYS_JSON",
        "AGENTCORE_RECALL_API_KEY",
        "SWARMRECALL_API_URL",
        "SWARMRECALL_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    getattr(neutral_recall, "_POOL_CACHE", {}).clear()


def _configure(monkeypatch, mapping: dict[str, str] | None = None) -> None:
    monkeypatch.setenv("AGENTCORE_RECALL_API_URL", "http://127.0.0.1:3300")
    monkeypatch.setenv(
        "AGENTCORE_RECALL_PROJECT_KEYS_JSON",
        json.dumps(mapping or {PROJECT_A: PROJECT_A_KEY}),
    )


def test_configuration_never_falls_back_to_swarmclaw_credentials(monkeypatch) -> None:
    monkeypatch.setenv("SWARMRECALL_API_URL", "http://127.0.0.1:3300")
    monkeypatch.setenv("SWARMRECALL_API_KEY", "".join(("sr_", "live_", "c" * 40)))

    assert neutral_recall.recall_configured() is False
    assert neutral_recall.recall_configured(PROJECT_A) is False
    status = neutral_recall.recall_topology_status()
    assert status["configured"] is False
    assert "swarmclaw" not in json.dumps(status).lower()


@pytest.mark.parametrize(
    "url",
    [
        "https://recall.example.test",
        "http://192.168.1.10:3300",
        "file:///H:/SwarmData",
        "http://user:password@127.0.0.1:3300",
    ],
)
def test_configuration_requires_a_plain_loopback_http_endpoint(monkeypatch, url: str) -> None:
    monkeypatch.setenv("AGENTCORE_RECALL_API_URL", url)
    monkeypatch.setenv(
        "AGENTCORE_RECALL_PROJECT_KEYS_JSON",
        json.dumps({PROJECT_A: PROJECT_A_KEY}),
    )

    assert neutral_recall.recall_configured() is False


@pytest.mark.parametrize(
    "mapping",
    [
        "not-json",
        "[]",
        "{}",
        '{"project-a": ""}',
        '{"project-a": "wrong_prefix"}',
        '{"project-a": "sr_live_not-a-real-key"}',
        json.dumps({" project-a": PROJECT_A_KEY}),
        (
            '{"project-a":"'
            + PROJECT_A_KEY
            + '","project-a":"'
            + PROJECT_B_KEY
            + '"}'
        ),
        json.dumps({"Project-A": PROJECT_A_KEY, "project-a": PROJECT_B_KEY}),
    ],
)
def test_configuration_rejects_malformed_or_ambiguous_project_key_maps(
    monkeypatch, mapping: str
) -> None:
    monkeypatch.setenv("AGENTCORE_RECALL_API_URL", "http://localhost:3300")
    monkeypatch.setenv("AGENTCORE_RECALL_PROJECT_KEYS_JSON", mapping)

    assert neutral_recall.recall_configured() is False
    status = neutral_recall.recall_topology_status()
    assert status["configured"] is False
    assert "sr_live" not in json.dumps(status)


def test_pool_resolution_uses_the_exact_project_credential_and_caches_no_secret(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    observed: dict[str, Any] = {}

    def fake_urlopen(request, timeout):
        observed["url"] = request.full_url
        observed["authorization"] = request.headers["Authorization"]
        observed["timeout"] = timeout
        return _Response(_pool_payload())

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fake_urlopen)

    topology = neutral_recall.resolve_project_pools(PROJECT_A)

    assert topology == {
        "ok": True,
        "degraded": False,
        "global_pool_id": GLOBAL_POOL_ID,
        "project_pool_id": PROJECT_A_POOL_ID,
    }
    assert observed["url"].endswith("/api/v1/pools")
    assert observed["authorization"] == f"Bearer {PROJECT_A_KEY}"
    assert PROJECT_A_KEY not in repr(neutral_recall._POOL_CACHE)


def test_projection_writes_to_exact_project_pool_and_preserves_idempotency_key(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    requests: list[Any] = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        if request.full_url.endswith("/api/v1/pools"):
            return _Response(_pool_payload())
        return _Response({"id": "memory-1"}, status=201)

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fake_urlopen)

    result = neutral_recall.project_curated_fact(
        project_key=PROJECT_A,
        content="accepted decision",
        category="decision",
        source_event_id="event-123",
    )

    assert result["ok"] is True
    body = json.loads(requests[-1].data.decode("utf-8"))
    assert body["poolId"] == PROJECT_A_POOL_ID
    assert body["idempotencyKey"] == "agentcore:project-a:event-123"
    assert body["metadata"] == {
        "project_key": PROJECT_A,
        "visibility": "project",
        "source": "agentcore-memory",
        "source_event_id": "event-123",
        "plane": "neutral_shared_swarmrecall",
    }
    assert body["tags"] == ["agentcore", "curated", PROJECT_A]


def test_search_returns_only_exact_project_and_explicit_global_pool_records(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    hits = [
        {
            "data": {
                "id": "project-memory",
                "content": "project A decision",
                "category": "decision",
                "poolId": PROJECT_A_POOL_ID,
                "metadata": {
                    "project_key": PROJECT_A,
                    "visibility": "project",
                    "source": "agentcore-memory",
                    "source_event_id": "event-a",
                },
            },
            "score": 0.94,
        },
        {
            "data": {
                "id": "global-memory",
                "content": "shared preference",
                "category": "preference",
                "poolId": GLOBAL_POOL_ID,
                "metadata": {
                    "visibility": "global",
                    "source": "agentcore-memory",
                    "source_event_id": "event-global",
                },
            },
            "score": 0.91,
        },
        {
            "data": {
                "id": "foreign-pool",
                "content": "project B private",
                "poolId": FOREIGN_POOL_ID,
                "metadata": {
                    "project_key": PROJECT_B,
                    "visibility": "project",
                    "source": "agentcore-memory",
                },
            },
            "score": 0.99,
        },
        {
            "data": {
                "id": "forged-project-metadata",
                "content": "wrong project marker",
                "poolId": PROJECT_A_POOL_ID,
                "metadata": {
                    "project_key": PROJECT_B,
                    "visibility": "project",
                    "source": "agentcore-memory",
                },
            },
            "score": 0.98,
        },
        {
            "data": {
                "id": "private-agent-row",
                "content": "unpooled row",
                "poolId": None,
                "metadata": {"project_key": PROJECT_A, "source": "agentcore-memory"},
            },
            "score": 0.97,
        },
        {
            "data": {
                "id": "global-without-marker",
                "content": "not explicitly global",
                "poolId": GLOBAL_POOL_ID,
                "metadata": {"source": "agentcore-memory"},
            },
            "score": 0.96,
        },
    ]

    def fake_urlopen(request, timeout):
        if request.full_url.endswith("/api/v1/pools"):
            return _Response(_pool_payload())
        return _Response({"data": hits})

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fake_urlopen)

    result = neutral_recall.search_semantic(
        "decision", project_key=PROJECT_A, limit=5, min_score=0.3
    )

    assert result["ok"] is True
    assert result["degraded"] is False
    assert result["filtered_count"] == 4
    assert [row["id"] for row in result["results"]] == [
        "project-memory",
        "global-memory",
    ]
    assert result["results"][0]["scope"] == "project"
    assert result["results"][1]["scope"] == "global"
    assert all(row["source"] == "neutral_shared_swarmrecall" for row in result["results"])
    assert all(row["authority"] == "noncanonical_semantic_projection" for row in result["results"])


def test_search_fails_closed_when_identity_has_an_unexpected_pool_membership(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    search_requested = False

    def fake_urlopen(request, timeout):
        nonlocal search_requested
        if request.full_url.endswith("/api/v1/pools"):
            return _Response(
                _pool_payload(
                    extra=[
                        {
                            "id": FOREIGN_POOL_ID,
                            "name": f"agentcore-memory-{PROJECT_B}",
                            "memoryAccess": "read",
                        }
                    ]
                )
            )
        search_requested = True
        return _Response({"data": []})

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fake_urlopen)

    result = neutral_recall.search_semantic("private", project_key=PROJECT_A)

    assert result["ok"] is False
    assert result["degraded"] is True
    assert result["error"] == "invalid_pool_topology"
    assert search_requested is False


def test_missing_project_mapping_fails_before_any_http_request(monkeypatch) -> None:
    _configure(monkeypatch, {PROJECT_B: PROJECT_B_KEY})

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("HTTP must not run without an exact project mapping")

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fail_urlopen)

    result = neutral_recall.search_semantic("anything", project_key=PROJECT_A)

    assert result == {
        "ok": False,
        "degraded": True,
        "skipped": True,
        "error": "project_not_configured",
        "results": [],
    }


def test_long_project_keys_use_the_provisioner_hash_suffix(monkeypatch) -> None:
    project_key = "Project-" + ("A" * 80)
    project_key_secret = "".join(("sr_", "live_", "d" * 40))
    monkeypatch.setenv("AGENTCORE_RECALL_API_URL", "http://127.0.0.1:3300")
    monkeypatch.setenv(
        "AGENTCORE_RECALL_PROJECT_KEYS_JSON",
        json.dumps({project_key: project_key_secret}),
    )
    expected_pool_name = (
        "agentcore-memory-project-"
        + ("a" * 51)
        + "-75c25561a8fc"
    )

    def fake_urlopen(request, timeout):
        return _Response(
            {
                "data": [
                    {
                        "id": GLOBAL_POOL_ID,
                        "name": "agentcore-global-memory",
                        "memoryAccess": "read",
                    },
                    {
                        "id": PROJECT_A_POOL_ID,
                        "name": expected_pool_name,
                        "memoryAccess": "readwrite",
                    },
                ]
            }
        )

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fake_urlopen)

    result = neutral_recall.resolve_project_pools(project_key)

    assert result["ok"] is True


def test_http_auth_failure_is_sanitized_and_never_returns_credentials(monkeypatch) -> None:
    _configure(monkeypatch)

    def fake_urlopen(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            "http://127.0.0.1:3300/api/v1/pools",
            401,
            "Unauthorized",
            {},
            io.BytesIO(
                json.dumps({"error": f"bad key {PROJECT_A_KEY}"}).encode("utf-8")
            ),
        )

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fake_urlopen)

    result = neutral_recall.resolve_project_pools(PROJECT_A)

    rendered = json.dumps(result)
    assert result["ok"] is False
    assert result["error"] == "http_401"
    assert "sr_live" not in rendered
    assert "Unauthorized" not in rendered


def test_projection_does_not_return_an_upstream_credential_echo(monkeypatch) -> None:
    _configure(monkeypatch)

    def fake_urlopen(request, timeout):
        if request.full_url.endswith("/api/v1/pools"):
            return _Response(_pool_payload())
        return _Response({"id": "memory-1", "echo": PROJECT_A_KEY}, status=201)

    monkeypatch.setattr(neutral_recall.urllib.request, "urlopen", fake_urlopen)

    result = neutral_recall.project_curated_fact(
        project_key=PROJECT_A,
        content="accepted decision",
        category="decision",
        source_event_id="event-echo",
    )

    assert result["ok"] is True
    assert PROJECT_A_KEY not in json.dumps(result)


class _Cursor:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _query, _params=None) -> None:
        return None

    def fetchall(self) -> list[dict[str, Any]]:
        return []


class _Connection:
    def cursor(self) -> _Cursor:
        return _Cursor()


class _Profile:
    def as_dict(self) -> dict[str, Any]:
        return {"profile_name": "standard-context", "max_total_tokens": 1000}


def test_retrieve_context_adds_bounded_noncanonical_recall_results(monkeypatch) -> None:
    @contextmanager
    def fake_db():
        yield _Connection()

    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setattr(
        server,
        "get_project",
        lambda _conn, project_key: {"id": "project-id", "project_key": project_key},
    )
    monkeypatch.setattr(server, "set_project", lambda *_args: None)
    monkeypatch.setattr(server, "resolve_context_profile", lambda *_args: (_Profile(), "budget"))
    monkeypatch.setattr(
        server,
        "hybrid_retrieval",
        lambda _args, _conn: [{"source": "postgres", "id": "canonical-1"}],
    )
    monkeypatch.setattr(
        server,
        "search_semantic",
        lambda query, **_kwargs: {
            "ok": True,
            "degraded": False,
            "results": [
                {
                    "id": "recall-1",
                    "content": "semantic decision",
                    "source": "neutral_shared_swarmrecall",
                    "authority": "noncanonical_semantic_projection",
                    "scope": "project",
                    "score": 0.88,
                }
            ],
            "filtered_count": 0,
        },
    )

    result = server.retrieve_context(
        {"project_key": PROJECT_A, "query": "decision", "limit": 500}
    )

    assert result["retrieval_results"] == [{"source": "postgres", "id": "canonical-1"}]
    assert result["neutral_recall"] == {
        "ok": True,
        "degraded": False,
        "source": "neutral_shared_swarmrecall",
        "authority": "noncanonical_semantic_projection",
        "results": [
            {
                "id": "recall-1",
                "content": "semantic decision",
                "source": "neutral_shared_swarmrecall",
                "authority": "noncanonical_semantic_projection",
                "scope": "project",
                "score": 0.88,
            }
        ],
        "filtered_count": 0,
    }


def test_retrieve_context_reports_recall_degradation_without_failing_pg18(monkeypatch) -> None:
    @contextmanager
    def fake_db():
        yield _Connection()

    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setattr(
        server,
        "get_project",
        lambda _conn, project_key: {"id": "project-id", "project_key": project_key},
    )
    monkeypatch.setattr(server, "set_project", lambda *_args: None)
    monkeypatch.setattr(server, "resolve_context_profile", lambda *_args: (_Profile(), "budget"))
    monkeypatch.setattr(server, "hybrid_retrieval", lambda _args, _conn: [])
    monkeypatch.setattr(
        server,
        "search_semantic",
        lambda query, **_kwargs: {
            "ok": False,
            "degraded": True,
            "error": "http_503",
            "results": [],
        },
    )

    result = server.retrieve_context({"project_key": PROJECT_A, "query": "decision"})

    assert result["ok"] is True
    assert result["neutral_recall"] == {
        "ok": False,
        "degraded": True,
        "source": "neutral_shared_swarmrecall",
        "authority": "noncanonical_semantic_projection",
        "results": [],
        "error": "http_503",
    }
