"""Project-scoped broker for the neutral shared SwarmRecall projection plane.

AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE

PostgreSQL 18 remains canonical. This module only projects curated records and
retrieves bounded semantic hints. Each enrolled project uses its own Recall
agent credential, and the broker validates the agent's exact pool topology
before every uncached operation. Secret values are never cached or returned.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode, urlsplit
from uuid import UUID, uuid4


_API_URL_ENV = "AGENTCORE_RECALL_API_URL"
_PROJECT_KEYS_ENV = "AGENTCORE_RECALL_PROJECT_KEYS_JSON"
_API_KEY_PATTERN = re.compile(r"^sr_live_[A-Za-z0-9]+$")
_PROJECT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")
_GLOBAL_POOL_NAME = "agentcore-global-memory"
_PROJECT_POOL_PREFIX = "agentcore-memory-"
_POOL_CACHE_TTL_SECONDS = 60.0
_MAX_SEARCH_LIMIT = 20
_MAX_RESULT_CONTENT = 4000

# Values are expiry, global pool UUID, project pool UUID. No credentials or
# credential-derived values are retained here.
_POOL_CACHE: dict[tuple[str, str], tuple[float, str, str]] = {}


def _api_url() -> str:
    raw = str(os.environ.get(_API_URL_ENV) or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlsplit(raw)
        _ = parsed.port
    except (TypeError, ValueError):
        return ""
    if parsed.scheme not in {"http", "https"}:
        return ""
    if (parsed.hostname or "").lower() not in {"127.0.0.1", "::1", "localhost"}:
        return ""
    if parsed.username is not None or parsed.password is not None:
        return ""
    if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        return ""
    return raw.rstrip("/")


def _project_keys() -> dict[str, str]:
    raw = str(os.environ.get(_PROJECT_KEYS_ENV) or "")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        parsed = json.loads(raw, object_pairs_hook=unique_object)
    except (TypeError, ValueError):
        return {}
    if not isinstance(parsed, dict) or not parsed:
        return {}
    result: dict[str, str] = {}
    normalized_keys: set[str] = set()
    for project_key, secret in parsed.items():
        if not isinstance(project_key, str) or not _PROJECT_KEY_PATTERN.fullmatch(project_key):
            return {}
        normalized_key = project_key.lower()
        if normalized_key in normalized_keys:
            return {}
        if not isinstance(secret, str) or not _API_KEY_PATTERN.fullmatch(secret):
            return {}
        normalized_keys.add(normalized_key)
        result[project_key] = secret
    return result


def _project_api_key(project_key: str) -> str:
    return _project_keys().get(project_key, "")


def recall_configured(project_key: str | None = None) -> bool:
    """Return configuration state without probing Recall or exposing identity."""
    if not _api_url():
        return False
    project_keys = _project_keys()
    if not project_keys:
        return False
    return project_key in project_keys if project_key is not None else True


def recall_topology_status() -> dict[str, Any]:
    """Return secret-safe static configuration and non-secret cache status."""
    url_valid = bool(_api_url())
    project_keys = _project_keys()
    return {
        "configured": bool(url_valid and project_keys),
        "endpoint_scope": "loopback" if url_valid else "invalid_or_missing",
        "project_count": len(project_keys),
        "cached_project_topologies": sum(
            1 for expiry, _global, _project in _POOL_CACHE.values() if expiry > time.monotonic()
        ),
        "credentials_exposed": False,
    }


def recall_health(timeout: float = 3.0) -> dict[str, Any]:
    api_url = _api_url()
    if not api_url:
        return {"ok": False, "degraded": True, "error": "invalid_or_missing_endpoint"}
    url = f"{api_url}/api/v1/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body) if body else {}
            reported_status = str(data.get("status") or "").strip().lower()
            services = data.get("services") if isinstance(data, dict) else None
            failed_services = sorted(
                str(name)
                for name, value in (services.items() if isinstance(services, dict) else [])
                if value is False
                or (isinstance(value, dict) and value.get("ok") is False)
            )
            body_degraded = reported_status in {
                "degraded",
                "error",
                "failed",
                "unhealthy",
            }
            ok = resp.status == 200 and not body_degraded and not failed_services
            return {
                "ok": ok,
                "degraded": not ok,
                "status": resp.status,
                "body": data,
                "failed_services": failed_services,
            }
    except Exception as exc:  # noqa: BLE001 - degraded boundary
        return {"ok": False, "degraded": True, "error": type(exc).__name__}


def _request(
    project_key: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    api_url = _api_url()
    key = _project_api_key(project_key)
    if not api_url:
        return {"ok": False, "degraded": True, "error": "invalid_or_missing_endpoint"}
    if not key:
        return {"ok": False, "degraded": True, "error": "project_not_configured"}
    data = None
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{api_url}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return {
                    "ok": False,
                    "degraded": True,
                    "status": resp.status,
                    "error": "invalid_json_response",
                }
            return {
                "ok": True,
                "degraded": False,
                "status": resp.status,
                "data": parsed,
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "degraded": True,
            "status": exc.code,
            "error": f"http_{exc.code}",
        }
    except Exception as exc:  # noqa: BLE001 - degraded boundary
        return {"ok": False, "degraded": True, "error": type(exc).__name__}


def _valid_pool_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        UUID(value)
    except (ValueError, TypeError, AttributeError):
        return None
    return value


def _project_slug(project_key: str) -> str:
    slug = project_key.lower()
    if len(slug) <= 72:
        return slug
    digest = hashlib.sha256(project_key.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:59]}-{digest}"


def _sanitized_mutation_result(response: dict[str, Any]) -> dict[str, Any]:
    result = {
        "ok": bool(response.get("ok")),
        "degraded": bool(response.get("degraded")),
    }
    for key in ("status", "error"):
        if key in response:
            result[key] = response[key]
    data = response.get("data")
    record_id = _valid_pool_id(data.get("id")) if isinstance(data, dict) else None
    if record_id:
        result["record_id"] = record_id
    return result


def resolve_project_pools(project_key: str) -> dict[str, Any]:
    """Resolve and validate the only two pools an AgentCore project may see."""
    api_url = _api_url()
    if not api_url:
        return {"ok": False, "degraded": True, "error": "invalid_or_missing_endpoint"}
    if not _project_api_key(project_key):
        return {"ok": False, "degraded": True, "error": "project_not_configured"}

    cache_key = (api_url, project_key)
    cached = _POOL_CACHE.get(cache_key)
    now = time.monotonic()
    if cached and cached[0] > now:
        return {
            "ok": True,
            "degraded": False,
            "global_pool_id": cached[1],
            "project_pool_id": cached[2],
        }

    response = _request(project_key, "GET", "/api/v1/pools")
    if not response.get("ok"):
        return response
    envelope = response.get("data")
    rows = envelope.get("data") if isinstance(envelope, dict) else None
    if not isinstance(rows, list):
        return {"ok": False, "degraded": True, "error": "invalid_pool_response"}

    expected_project_name = f"{_PROJECT_POOL_PREFIX}{_project_slug(project_key)}"
    expected_names = {_GLOBAL_POOL_NAME, expected_project_name}
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            return {"ok": False, "degraded": True, "error": "invalid_pool_topology"}
        name = row.get("name")
        if not isinstance(name, str) or name not in expected_names or name in by_name:
            return {"ok": False, "degraded": True, "error": "invalid_pool_topology"}
        by_name[name] = row
    if set(by_name) != expected_names:
        return {"ok": False, "degraded": True, "error": "invalid_pool_topology"}

    global_row = by_name[_GLOBAL_POOL_NAME]
    project_row = by_name[expected_project_name]
    global_id = _valid_pool_id(global_row.get("id"))
    project_id = _valid_pool_id(project_row.get("id"))
    if not global_id or not project_id or global_id == project_id:
        return {"ok": False, "degraded": True, "error": "invalid_pool_topology"}
    if global_row.get("memoryAccess") not in {"read", "readwrite"}:
        return {"ok": False, "degraded": True, "error": "invalid_pool_topology"}
    if project_row.get("memoryAccess") != "readwrite":
        return {"ok": False, "degraded": True, "error": "invalid_pool_topology"}

    _POOL_CACHE[cache_key] = (
        now + _POOL_CACHE_TTL_SECONDS,
        global_id,
        project_id,
    )
    return {
        "ok": True,
        "degraded": False,
        "global_pool_id": global_id,
        "project_pool_id": project_id,
    }


def start_session(
    *,
    project_key: str | None = None,
    context: dict[str, Any] | None = None,
    pool_id: str | None = None,
) -> dict[str, Any]:
    if not project_key:
        return {"ok": False, "degraded": True, "error": "project_not_configured"}
    topology = resolve_project_pools(project_key)
    if not topology.get("ok"):
        return topology
    expected_pool = str(topology["project_pool_id"])
    if pool_id and pool_id != expected_pool:
        return {"ok": False, "degraded": True, "error": "pool_scope_mismatch"}
    body: dict[str, Any] = {"poolId": expected_pool}
    if context is not None:
        body["context"] = context
    return _sanitized_mutation_result(
        _request(project_key, "POST", "/api/v1/memory/sessions", body)
    )


def store_semantic_memory(
    *,
    project_key: str | None = None,
    content: str,
    category: str = "decision",
    importance: float = 0.7,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    pool_id: str | None = None,
    idempotency_key: str | None = None,
    visibility: str = "project",
) -> dict[str, Any]:
    """Project a curated row to an exact validated project or global pool."""
    if not project_key:
        return {"ok": False, "degraded": True, "error": "project_not_configured"}
    if visibility not in {"project", "global"}:
        return {"ok": False, "degraded": True, "error": "invalid_visibility"}
    topology = resolve_project_pools(project_key)
    if not topology.get("ok"):
        return topology
    selected_pool = str(
        topology["project_pool_id" if visibility == "project" else "global_pool_id"]
    )
    if pool_id and pool_id != selected_pool:
        return {"ok": False, "degraded": True, "error": "pool_scope_mismatch"}

    safe_metadata = dict(metadata or {})
    safe_metadata["visibility"] = visibility
    safe_metadata["source"] = "agentcore-memory"
    safe_metadata["plane"] = "neutral_shared_swarmrecall"
    if visibility == "project":
        safe_metadata["project_key"] = project_key
    elif safe_metadata.get("project_key") not in {None, project_key}:
        return {"ok": False, "degraded": True, "error": "metadata_scope_mismatch"}

    body: dict[str, Any] = {
        "content": str(content)[:10000],
        "category": category,
        "importance": max(0.0, min(1.0, importance)),
        "tags": tags or [],
        "metadata": safe_metadata,
        "poolId": selected_pool,
    }
    if session_id:
        body["sessionId"] = session_id
    if idempotency_key:
        body["idempotencyKey"] = idempotency_key
    return _sanitized_mutation_result(
        _request(project_key, "POST", "/api/v1/memory", body)
    )


def _sanitized_search_row(
    hit: Any,
    *,
    project_key: str,
    global_pool_id: str,
    project_pool_id: str,
) -> dict[str, Any] | None:
    if not isinstance(hit, dict) or not isinstance(hit.get("data"), dict):
        return None
    row = hit["data"]
    metadata = row.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("source") != "agentcore-memory":
        return None
    pool_id = row.get("poolId")
    if pool_id == project_pool_id:
        if metadata.get("project_key") != project_key or metadata.get("visibility") != "project":
            return None
        scope = "project"
    elif pool_id == global_pool_id:
        if metadata.get("visibility") != "global":
            return None
        scope = "global"
    else:
        return None
    if not isinstance(row.get("content"), str) or not row["content"].strip():
        return None
    score = hit.get("score")
    if not isinstance(score, (int, float)):
        return None
    return {
        "id": str(row.get("id") or ""),
        "content": row["content"][:_MAX_RESULT_CONTENT],
        "category": str(row.get("category") or "context"),
        "score": float(score),
        "scope": scope,
        "source": "neutral_shared_swarmrecall",
        "authority": "noncanonical_semantic_projection",
        "provenance": {
            "source_event_id": metadata.get("source_event_id"),
            "project_key": metadata.get("project_key"),
            "plane": "neutral_shared_swarmrecall",
        },
    }


def search_semantic(
    query: str,
    *,
    project_key: str | None = None,
    limit: int = 5,
    min_score: float = 0.3,
) -> dict[str, Any]:
    """Search with a project credential and re-enforce scope on every result."""
    if not project_key or not recall_configured(project_key):
        return {
            "ok": False,
            "degraded": True,
            "skipped": True,
            "error": "project_not_configured",
            "results": [],
        }
    normalized_query = str(query).strip()
    if not normalized_query:
        return {
            "ok": True,
            "degraded": False,
            "skipped": True,
            "results": [],
            "filtered_count": 0,
        }
    topology = resolve_project_pools(project_key)
    if not topology.get("ok"):
        return {**topology, "results": []}
    bounded_limit = max(1, min(int(limit), _MAX_SEARCH_LIMIT))
    bounded_score = max(0.0, min(float(min_score), 1.0))
    qs = urlencode(
        {
            "q": normalized_query[:500],
            "limit": str(bounded_limit),
            "minScore": str(bounded_score),
        }
    )
    response = _request(project_key, "GET", f"/api/v1/memory/search?{qs}")
    if not response.get("ok"):
        return {**response, "results": []}
    envelope = response.get("data")
    hits = envelope.get("data") if isinstance(envelope, dict) else None
    if not isinstance(hits, list):
        return {
            "ok": False,
            "degraded": True,
            "error": "invalid_search_response",
            "results": [],
        }
    accepted: list[dict[str, Any]] = []
    filtered_count = 0
    for hit in hits:
        row = _sanitized_search_row(
            hit,
            project_key=project_key,
            global_pool_id=str(topology["global_pool_id"]),
            project_pool_id=str(topology["project_pool_id"]),
        )
        if row is None:
            filtered_count += 1
            continue
        accepted.append(row)
    return {
        "ok": True,
        "degraded": False,
        "results": accepted[:bounded_limit],
        "filtered_count": filtered_count,
        "isolation_enforced": True,
    }


def project_curated_fact(
    *,
    project_key: str,
    content: str,
    category: str,
    source_event_id: str | None = None,
    session_id: str | None = None,
    importance: float = 0.75,
) -> dict[str, Any]:
    """Best-effort project-pool projection used only after the PG18 commit."""
    if not recall_configured(project_key):
        return {
            "ok": False,
            "degraded": True,
            "skipped": True,
            "error": "project_not_configured",
        }
    key = f"agentcore:{project_key}:{source_event_id or uuid4().hex}"
    metadata = {
        "project_key": project_key,
        "visibility": "project",
        "source": "agentcore-memory",
        "source_event_id": source_event_id,
        "plane": "neutral_shared_swarmrecall",
    }
    allowed_categories = {"fact", "preference", "decision", "context", "session_summary"}
    return store_semantic_memory(
        project_key=project_key,
        content=content,
        category=category if category in allowed_categories else "decision",
        importance=importance,
        tags=["agentcore", "curated", project_key],
        metadata=metadata,
        session_id=session_id,
        idempotency_key=key,
        visibility="project",
    )
