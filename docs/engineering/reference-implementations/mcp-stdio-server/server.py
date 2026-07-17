#!/usr/bin/env python3
"""Reference implementation — MCP stdio server (Bifrost-compatible NDJSON-RPC).

Teaches ONE pattern: how to build a minimal MCP stdio server that works
behind the Bifrost gateway on CHAOSCENTRAL.

This is a reference implementation, not a template. See:
    templates/mcp-server-python/  for the Copier template.
    recipes/03-mcp-stdio-server.md  for the recipe.

Run: python server.py
Test: echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}' | python server.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

SERVER_NAME = "reference-mcp-stdio"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(level: str, msg: str, **ctx: Any) -> None:
    sys.stderr.write(json.dumps({"ts": _now(), "level": level, "msg": msg, **ctx}) + "\n")
    sys.stderr.flush()


def _send(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _send_error(req_id: Any, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _send_result(req_id: Any, result: Any) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


# ─────────────────────────────────────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────────────────────────────────────

def tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "echo",
            "description": "Echo the input text. Reference implementation tool.",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Text to echo"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        },
        {
            "name": "server_info",
            "description": "Return server version and status.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    ]


def handle_tool_call(name: str, args: dict[str, Any]) -> Any:
    if name == "echo":
        return {"ok": True, "echo": args["text"], "server": SERVER_NAME}
    if name == "server_info":
        return {"ok": True, "name": SERVER_NAME, "version": SERVER_VERSION, "ts": _now()}
    raise ValueError(f"unknown tool: {name!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Message dispatch
# ─────────────────────────────────────────────────────────────────────────────

_initialized = False


def dispatch(msg: dict[str, Any]) -> None:
    global _initialized
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        client_version = params.get("protocolVersion", PROTOCOL_VERSION)
        negotiated = client_version if client_version in SUPPORTED_VERSIONS else PROTOCOL_VERSION
        _send_result(req_id, {
            "protocolVersion": negotiated,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    elif method in ("notifications/initialized", "initialized"):
        _initialized = True
        # Notifications have no response

    elif method == "tools/list":
        _send_result(req_id, {"tools": tool_defs()})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        _log("debug", "tool_call", tool=tool_name)
        try:
            result = handle_tool_call(tool_name, tool_args)
            _send_result(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, default=str)}],
            })
        except Exception as exc:
            _log("error", "tool_call_error", tool=tool_name, error=type(exc).__name__)
            if req_id is not None:
                _send_error(req_id, -32000, f"{type(exc).__name__}: {exc}")

    elif method == "ping":
        if req_id is not None:
            _send_result(req_id, {})

    else:
        if req_id is not None:
            _send_error(req_id, -32601, f"method not found: {method!r}")


def main() -> None:
    _log("info", "startup", server=SERVER_NAME, version=SERVER_VERSION)
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            _log("warn", "json_parse_error", error=str(exc))
            continue
        try:
            dispatch(msg)
        except Exception as exc:
            _log("error", "dispatch_error", error=type(exc).__name__, detail=str(exc))


if __name__ == "__main__":
    main()
