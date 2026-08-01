"""Server-side adapter to the neutral shared SwarmRecall plane.

AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE

- Uses SWARMRECALL_API_URL + SWARMRECALL_API_KEY (or AGENTCORE_RECALL_* aliases).
- Never logs secret values.
- Degraded-safe: failures never raise into PG18 evidence paths.
- Ordinary IDEs must not call this module; only agentcore-memory.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any
from uuid import uuid4


def _api_url() -> str:
    return (
        os.environ.get("AGENTCORE_RECALL_API_URL")
        or os.environ.get("SWARMRECALL_API_URL")
        or "http://127.0.0.1:3300"
    ).rstrip("/")


def _api_key() -> str:
    return (
        os.environ.get("AGENTCORE_RECALL_API_KEY")
        or os.environ.get("SWARMRECALL_API_KEY")
        or ""
    )


def recall_configured() -> bool:
    return bool(_api_url() and _api_key())


def recall_health(timeout: float = 3.0) -> dict[str, Any]:
    url = f"{_api_url()}/api/v1/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body) if body else {}
            return {"ok": resp.status == 200, "degraded": False, "status": resp.status, "body": data}
    except Exception as exc:  # noqa: BLE001 — degraded boundary
        return {"ok": False, "degraded": True, "error": type(exc).__name__}


def _request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    key = _api_key()
    if not key:
        return {"ok": False, "degraded": True, "error": "SWARMRECALL_API_KEY not configured"}
    url = f"{_api_url()}{path}"
    data = None
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw) if raw else None
            return {"ok": True, "degraded": False, "status": resp.status, "data": parsed}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:200]
        return {"ok": False, "degraded": True, "status": exc.code, "error": f"HTTP {exc.code}", "detail": detail}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "degraded": True, "error": type(exc).__name__}


def start_session(
    *,
    context: dict[str, Any] | None = None,
    pool_id: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if context is not None:
        body["context"] = context
    if pool_id:
        body["poolId"] = pool_id
    return _request("POST", "/api/v1/memory/sessions", body)


def store_semantic_memory(
    *,
    content: str,
    category: str = "decision",
    importance: float = 0.7,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    pool_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Project a curated semantic row. Never used for raw transcripts."""
    body: dict[str, Any] = {
        "content": content[:10000],
        "category": category,
        "importance": max(0.0, min(1.0, importance)),
        "tags": tags or [],
    }
    if metadata:
        body["metadata"] = metadata
    if session_id:
        body["sessionId"] = session_id
    if pool_id:
        body["poolId"] = pool_id
    if idempotency_key:
        body["idempotencyKey"] = idempotency_key
    return _request("POST", "/api/v1/memory", body)


def search_semantic(query: str, *, limit: int = 5, min_score: float = 0.3) -> dict[str, Any]:
    from urllib.parse import urlencode

    qs = urlencode({"q": query[:500], "limit": str(limit), "minScore": str(min_score)})
    return _request("GET", f"/api/v1/memory/search?{qs}")


def project_curated_fact(
    *,
    project_key: str,
    content: str,
    category: str,
    source_event_id: str | None = None,
    session_id: str | None = None,
    importance: float = 0.75,
) -> dict[str, Any]:
    """Best-effort projection used after PG18 evidence commit."""
    if not recall_configured():
        return {"ok": False, "degraded": True, "skipped": True, "error": "not_configured"}
    key = f"agentcore:{project_key}:{source_event_id or uuid4().hex}"
    meta = {
        "project_key": project_key,
        "source": "agentcore-memory",
        "source_event_id": source_event_id,
        "plane": "neutral_shared_swarmrecall",
    }
    return store_semantic_memory(
        content=content,
        category=category if category in {"fact", "preference", "decision", "context", "session_summary"} else "decision",
        importance=importance,
        tags=["agentcore", "curated", project_key],
        metadata=meta,
        session_id=session_id,
        idempotency_key=key,
    )
