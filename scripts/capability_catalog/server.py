#!/usr/bin/env python3
"""Read-only AgentCore capability catalog MCP (stdio NDJSON).

The catalog projects an allowlisted metadata view from the canonical Bifrost
registry. It never returns launch commands, environment names or values,
headers, raw MCP schemas, or credential material.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any


SERVER_NAME = "agentcore-capability-catalog"
SERVER_VERSION = "0.1.0"
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"


def _log(message: str) -> None:
    sys.stderr.write(f"[{SERVER_NAME}] {message}\n")
    sys.stderr.flush()


def _load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _available_profiles(registry: dict[str, Any], capability_id: str) -> list[str]:
    return sorted(
        profile_id
        for profile_id, profile in registry["capability_profiles"].items()
        if capability_id in (profile.get("allowed_server_ids") or [])
    )


def _elevation_metadata(
    registry: dict[str, Any], capability_id: str, server: dict[str, Any]
) -> dict[str, str]:
    profiles = _available_profiles(registry, capability_id)
    if not server.get("enabled"):
        return {
            "route": "not_executable",
            "profile": "none",
            "requirement": "Complete the canonical admission and activation gate.",
        }
    if "operator" in profiles:
        return {
            "route": "existing_operator_authority_path",
            "profile": "operator",
            "requirement": "Use the existing operator authority and approval workflow.",
        }
    return {
        "route": "existing_profile_or_operator_authority_path",
        "profile": profiles[0] if profiles else "operator",
        "requirement": "Use an already granted profile or the existing operator authority path.",
    }


def _summary(
    registry: dict[str, Any], capability_id: str, server: dict[str, Any]
) -> dict[str, Any]:
    permitted = list(server.get("permitted_tools") or [])
    denied = list(server.get("denied_tools") or [])
    return {
        "capability_id": capability_id,
        "display_name": str(server.get("display_name") or capability_id),
        "purpose": str(server.get("purpose") or ""),
        "enabled": bool(server.get("enabled")),
        "status": str(server.get("status") or "unspecified"),
        "code_mode": bool(server.get("is_code_mode_client")),
        "permitted_tool_count": len(permitted),
        "denied_tool_count": len(denied),
        "profiles": _available_profiles(registry, capability_id),
        "elevation": _elevation_metadata(registry, capability_id, server),
    }


def list_capabilities(
    arguments: dict[str, Any], *, registry: dict[str, Any] | None = None
) -> dict[str, Any]:
    source = registry if registry is not None else _load_registry()
    query = str(arguments.get("query") or "").strip().casefold()
    entries: list[dict[str, Any]] = []
    for capability_id, spec in sorted(source["servers"].items()):
        searchable = "\n".join(
            [
                capability_id,
                str(spec.get("display_name") or ""),
                str(spec.get("purpose") or ""),
                str(spec.get("status") or ""),
                *(str(item) for item in spec.get("permitted_tools") or []),
                *(str(item) for item in spec.get("denied_tools") or []),
            ]
        ).casefold()
        if query and query not in searchable:
            continue
        entries.append(_summary(source, capability_id, spec))
    return {"ok": True, "query": query or None, "count": len(entries), "capabilities": entries}


def get_capability_detail(
    arguments: dict[str, Any], *, registry: dict[str, Any] | None = None
) -> dict[str, Any]:
    source = registry if registry is not None else _load_registry()
    capability_id = str(arguments.get("capability_id") or "").strip()
    spec = source["servers"].get(capability_id)
    if not capability_id or not isinstance(spec, dict):
        return {"ok": False, "error": "capability_not_found", "capability_id": capability_id}
    detail = _summary(source, capability_id, spec)
    detail.update(
        {
            "project_scope": str(spec.get("project_scope") or "unspecified"),
            "write_classification": str(spec.get("write_classification") or "unspecified"),
            "permitted_tools": list(spec.get("permitted_tools") or []),
            "denied_tools": list(spec.get("denied_tools") or []),
        }
    )
    return {"ok": True, "capability": detail}


def tool_defs() -> list[dict[str, Any]]:
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    return [
        {
            "name": "list_capabilities",
            "description": "List or search compact AgentCore capability metadata.",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string", "maxLength": 200}},
                "additionalProperties": False,
            },
            "annotations": annotations,
        },
        {
            "name": "get_capability_detail",
            "description": "Get exact admitted tools, profile visibility, and the governed elevation route for one capability.",
            "inputSchema": {
                "type": "object",
                "properties": {"capability_id": {"type": "string", "maxLength": 100}},
                "required": ["capability_id"],
                "additionalProperties": False,
            },
            "annotations": annotations,
        },
    ]


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "list_capabilities":
        return list_capabilities(arguments)
    if name == "get_capability_detail":
        return get_capability_detail(arguments)
    return {"ok": False, "error": "unknown_tool"}


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    if request_id is None and method and str(method).startswith("notifications/"):
        return None
    try:
        if method == "initialize":
            requested = str(params.get("protocolVersion") or DEFAULT_PROTOCOL_VERSION)
            result: dict[str, Any] = {
                "protocolVersion": requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_defs()}
        elif method == "tools/call":
            payload = call_tool(str(params.get("name") or ""), params.get("arguments") or {})
            result = {
                "content": [{"type": "text", "text": json.dumps(payload, separators=(",", ":"))}],
                "structuredContent": payload,
                "isError": not payload.get("ok", False),
            }
        elif method in {"resources/list", "prompts/list"}:
            result = {method.split("/")[0]: []}
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception:  # noqa: BLE001
        _log(traceback.format_exc())
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": "internal error (sanitized)"},
        }


def main() -> int:
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, ValueError):
            pass
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        response = handle_request(message)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
