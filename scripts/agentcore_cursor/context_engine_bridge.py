"""Cursor lifecycle bridge into agentcore-memory / Context Engine identity.

AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE

Uses gateway HTTP tools when available; fail-open on errors (never blocks the IDE).
Does not embed SwarmRecall credentials in Cursor configs.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from agentcore_cursor.gateway import GatewayClient


def _device_id() -> str:
    raw = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown-device"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _project_key_from_path(workspace: Path) -> str:
    name = workspace.name.strip().lower().replace(" ", "-")
    return name or "unknown-project"


def open_context_session(workspace: Path, *, agent_key: str = "cursor") -> dict[str, Any]:
    project_key = _project_key_from_path(workspace)
    session_hint = uuid.uuid4().hex
    try:
        client = GatewayClient()
        result = client.call_tool(
            "agentcore_memory-session_open",
            {
                "project_key": project_key,
                "project_root": str(workspace.resolve()),
                "client_key": "cursor",
                "agent_key": agent_key,
                "session_key": f"cursor-context-engine:{project_key}:{session_hint}",
            },
        )
        return {
            "ok": True,
            "project_key": project_key,
            "device_id": _device_id(),
            "gateway": result,
        }
    except Exception as exc:  # noqa: BLE001 — fail-open
        return {"ok": False, "degraded": True, "error": type(exc).__name__, "project_key": project_key}


def retrieve_startup_packet(project_key: str, project_root: str) -> dict[str, Any]:
    try:
        client = GatewayClient()
        return {
            "ok": True,
            "packet": client.call_tool(
                "agentcore_memory-startup_context",
                {"project_key": project_key, "project_root": project_root, "context_profile": "standard-context"},
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "degraded": True, "error": type(exc).__name__}


def append_accepted_summary(
    *,
    session_id: str,
    project_key: str,
    project_root: str,
    summary: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    key = idempotency_key or hashlib.sha256(
        f"{session_id}:{summary[:200]}".encode("utf-8")
    ).hexdigest()
    try:
        client = GatewayClient()
        return {
            "ok": True,
            "result": client.call_tool(
                "agentcore_memory-append_event",
                {
                    "project_key": project_key,
                    "project_root": project_root,
                    "session_id": session_id,
                    "event_kind": "decision",
                    "idempotency_key": key,
                    "payload": {
                        "summary": summary[:4000],
                        "project_key": project_key,
                        "source": "cursor-context-engine-bridge",
                    },
                    "trust_class": "project_verified",
                },
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "degraded": True, "error": type(exc).__name__}
