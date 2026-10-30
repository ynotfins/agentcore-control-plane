"""Short-lived docs_search result cache. Invalidates when the corpus revision changes.

This is the MCP-layer cache. Bifrost semantic_cache remains inference-only.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any


class DocsSearchCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = max(1, int(ttl_seconds))
        self._store: dict[str, tuple[float, Any]] = {}

    def key(
        self,
        *,
        project_key: str,
        query: str,
        metadata_filter: dict[str, str] | None,
        methods: list[str] | None,
        trust_classes: list[str] | None,
        limit: int,
        corpus_revision: str,
    ) -> str:
        payload = {
            "project_key": project_key,
            "query": query,
            "metadata_filter": metadata_filter or {},
            "methods": methods or [],
            "trust_classes": trust_classes or [],
            "limit": limit,
            "corpus_revision": corpus_revision,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self._ttl, value)

    def clear(self) -> None:
        self._store.clear()


DOCS_SEARCH_CACHE = DocsSearchCache()


def corpus_revision_from_conn(conn: Any) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(MAX(updated_at), TIMESTAMPTZ '-infinity')::text
              AS corpus_revision
            FROM agentcore.retrieval_documents
            """
        )
        row = cur.fetchone()
    if isinstance(row, dict):
        return str(row.get("corpus_revision") or next(iter(row.values())))
    if row:
        return str(row[0])
    return "-infinity"
