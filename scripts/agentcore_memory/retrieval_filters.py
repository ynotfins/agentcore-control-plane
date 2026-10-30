"""Build hybrid_retrieve_documents metadata filters from MCP tool arguments."""

from __future__ import annotations

from typing import Any

FILTER_KEYS = ("framework", "asset_type", "language")


def metadata_filter_from_args(args: dict[str, Any] | None) -> dict[str, str] | None:
    """Return a jsonb-containment object, or None when no filters were requested."""
    if not args:
        return None
    filt: dict[str, str] = {}
    for key in FILTER_KEYS:
        raw = args.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str):
            raise ValueError(f"{key} must be a string")
        value = raw.strip()
        if not value:
            continue
        if len(value) > 64:
            raise ValueError(f"{key} exceeds 64 characters")
        filt[key] = value
    return filt or None
