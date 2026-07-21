"""Durable local hook spool when agentcore-gateway is temporarily unavailable."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SPOOL_ROOT = Path(
    os.environ.get(
        "AGENTCORE_CURSOR_SPOOL_ROOT",
        r"H:\AgentRuntime\clients\cursor\spool\pending",
    )
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_key(idempotency_key: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in idempotency_key)[:200]


def spool_write(idempotency_key: str, payload: dict[str, Any]) -> Path:
    """Atomically write a spooled event; returns the spool file path."""
    SPOOL_ROOT.mkdir(parents=True, exist_ok=True)
    target = SPOOL_ROOT / f"{_safe_key(idempotency_key)}.json"
    if target.is_file():
        return target
    tmp = target.with_suffix(".json.tmp")
    body = {
        "idempotency_key": idempotency_key,
        "spooled_at": _now(),
        "payload": payload,
    }
    tmp.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(target)
    return target


def spool_exists(idempotency_key: str) -> bool:
    return (SPOOL_ROOT / f"{_safe_key(idempotency_key)}.json").is_file()
