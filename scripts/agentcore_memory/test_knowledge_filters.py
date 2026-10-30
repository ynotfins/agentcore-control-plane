"""Unit tests for knowledge-corpus MCP filters and docs_search cache."""

from __future__ import annotations

import pytest

from docs_search_cache import DocsSearchCache
from retrieval_filters import metadata_filter_from_args
from server import tool_defs


def test_ten_tool_surface_unchanged() -> None:
    tools = {tool["name"]: tool for tool in tool_defs()}
    assert len(tools) == 10
    assert "hybrid_retrieve_documents" not in tools


def test_metadata_filter_omits_empty_and_builds_containment() -> None:
    assert metadata_filter_from_args({}) is None
    assert metadata_filter_from_args({"framework": "  "}) is None
    assert metadata_filter_from_args(
        {"framework": "fastapi", "asset_type": "boilerplate", "language": "python"}
    ) == {
        "framework": "fastapi",
        "asset_type": "boilerplate",
        "language": "python",
    }


def test_metadata_filter_rejects_non_string() -> None:
    with pytest.raises(ValueError):
        metadata_filter_from_args({"framework": ["fastapi"]})


def test_docs_search_cache_hits_same_revision_and_misses_on_change() -> None:
    cache = DocsSearchCache(ttl_seconds=60)
    kwargs = {
        "project_key": "agentcore-control-plane",
        "query": "fastapi dependency injection",
        "metadata_filter": {"framework": "fastapi", "asset_type": "boilerplate"},
        "methods": None,
        "trust_classes": None,
        "limit": 5,
        "corpus_revision": "rev-1",
    }
    key1 = cache.key(**kwargs)
    cache.set(key1, {"results": ["a"]})
    assert cache.get(key1) == {"results": ["a"]}
    kwargs["corpus_revision"] = "rev-2"
    key2 = cache.key(**kwargs)
    assert key1 != key2
    assert cache.get(key2) is None
