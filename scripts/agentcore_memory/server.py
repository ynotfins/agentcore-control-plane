#!/usr/bin/env python3
"""Minimal AgentCore memory health MCP server (stdio NDJSON).

Bifrost Windows Gateway speaks newline-delimited JSON-RPC on STDIO
(not Content-Length framing). Protocol version observed: 2025-06-18.

Tools: memory_health, memory_status
Never exposes credentials. Stable identity: agentcore-memory
"""

from __future__ import annotations

import json
import socket
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

SERVER_NAME = "agentcore-memory"
SERVER_VERSION = "0.1.0"
# Bifrost currently initializes with 2025-06-18; accept and echo it.
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
PG_HOST = "127.0.0.1"
PG_PORT = 55432


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str) -> None:
    sys.stderr.write(f"[{SERVER_NAME}] {msg}\n")
    sys.stderr.flush()


def postgres_reachable(timeout: float = 1.5) -> tuple[bool, str]:
    try:
        with socket.create_connection((PG_HOST, PG_PORT), timeout=timeout):
            return True, "tcp_ok"
    except OSError as exc:
        return False, exc.__class__.__name__


def tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "memory_health",
            "description": "Check AgentCore memory substrate reachability (Postgres TCP only; no credentials).",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "memory_status",
            "description": "Return sanitized memory/gateway status summary without secrets.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    ]


def memory_health() -> dict[str, Any]:
    ok, detail = postgres_reachable()
    status = "healthy" if ok else "degraded"
    return {
        "ok": True,
        "server": SERVER_NAME,
        "status": status,
        "checked_at": _now(),
        "postgres": {
            "host": PG_HOST,
            "port": PG_PORT,
            "reachable": ok,
            "probe": "tcp",
            "detail": detail if not ok else "connected",
        },
        "credentials_exposed": False,
    }


def memory_status() -> dict[str, Any]:
    health = memory_health()
    return {
        "ok": True,
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "status": health["status"],
        "checked_at": _now(),
        "components": {
            "postgres_agent_core": {
                "endpoint": f"{PG_HOST}:{PG_PORT}",
                "reachable": health["postgres"]["reachable"],
                "role": "canonical AgentCore database listener probe",
            },
            "gateway_write_path": {
                "note": "Normal durable memory writes remain governed; this server is health-only.",
            },
        },
        "secrets": "never_returned",
    }


def call_tool(name: str, _arguments: dict[str, Any] | None) -> dict[str, Any]:
    if name == "memory_health":
        return memory_health()
    if name == "memory_status":
        return memory_status()
    return {"ok": False, "error": f"Unknown tool: {name}"}


def handle_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    if req_id is None and method and str(method).startswith("notifications/"):
        return None

    try:
        if method == "initialize":
            requested = str((params or {}).get("protocolVersion") or DEFAULT_PROTOCOL_VERSION)
            version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
            result = {
                "protocolVersion": version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_defs()}
        elif method == "tools/call":
            payload = call_tool(params.get("name"), params.get("arguments") or {})
            result = {
                "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
                "structuredContent": payload,
                "isError": not payload.get("ok", True),
            }
        elif method in ("resources/list", "prompts/list"):
            result = {method.split("/")[0]: []}
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception:  # noqa: BLE001
        _log(traceback.format_exc())
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": "internal error (sanitized)"},
        }


def main() -> int:
    _log("starting stdio NDJSON server")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        response = handle_request(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
