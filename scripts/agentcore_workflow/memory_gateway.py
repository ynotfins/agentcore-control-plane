"""Sync AgentCore-memory calls through agentcore-gateway (streamable HTTP).

Used by LangGraph production and Studio nodes. Reads the workflow/builder VK
from Windows env at call time; never logs the Authorization value.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
import urllib.error
import urllib.request
from typing import Any, Optional

from .mcp_client import GATEWAY_URL, GATEWAY_TIMEOUT_SECONDS, resolve_workflow_vk

logger = logging.getLogger(__name__)

MEMORY_TOOL_CANDIDATES = {
    "session_open": ("agentcore_memory-session_open", "session_open"),
    "session_close": ("agentcore_memory-session_close", "session_close"),
    "startup_context": ("agentcore_memory-startup_context", "startup_context"),
    "append_event": ("agentcore_memory-append_event", "append_event"),
    "retrieve_context": ("agentcore_memory-retrieve_context", "retrieve_context"),
    "expand_source": ("agentcore_memory-expand_source", "expand_source"),
    "build_handoff": ("agentcore_memory-build_handoff", "build_handoff"),
    "memory_status": ("agentcore_memory-memory_status", "memory_status"),
    "propose_fact": ("agentcore_memory-propose_fact", "propose_fact"),
    "docs_search": ("agentcore_memory-docs_search", "docs_search"),
}


def _headers() -> dict[str, str]:
    _, vk = resolve_workflow_vk()
    return {
        "Authorization": f"Bearer {vk}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }


def _parse_mcp_response(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if not raw:
        return {}
    if "data:" in raw:
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload and payload != "[DONE]":
                    return json.loads(payload)
    return json.loads(raw)


def call_gateway_tool(tool_name: str, arguments: dict[str, Any], *, url: str = GATEWAY_URL) -> dict[str, Any]:
    if not url.startswith("http://127.0.0.1") and not url.startswith("http://localhost"):
        raise RuntimeError("gateway URL must be localhost")
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=GATEWAY_TIMEOUT_SECONDS) as resp:
            parsed = _parse_mcp_response(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _ = exc.read()  # discard; do not log body (may contain secrets)
        raise RuntimeError(f"gateway tools/call HTTP {exc.code}") from None
    if "error" in parsed:
        raise RuntimeError(f"gateway tool error: {parsed['error']}")
    return parsed.get("result") or parsed


def list_gateway_tools(*, url: str = GATEWAY_URL) -> list[str]:
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=GATEWAY_TIMEOUT_SECONDS) as resp:
        parsed = _parse_mcp_response(resp.read().decode("utf-8"))
    tools = ((parsed.get("result") or {}).get("tools")) or []
    return [t.get("name", "") for t in tools if isinstance(t, dict)]


def resolve_memory_tool_name(bare: str, available: Optional[list[str]] = None) -> str:
    names = set(available if available is not None else list_gateway_tools())
    for candidate in MEMORY_TOOL_CANDIDATES.get(bare, (bare,)):
        if candidate in names:
            return candidate
    for n in names:
        if n.endswith(bare) or n.endswith(f"_{bare}") or n.endswith(f"-{bare}"):
            return n
    raise RuntimeError(f"memory tool not visible via gateway: {bare}")


def open_memory_session(project_key: str, **kwargs: Any) -> dict[str, Any]:
    name = resolve_memory_tool_name("session_open")
    args: dict[str, Any] = {"project_key": project_key, "client_key": "langgraph", "agent_key": "langgraph-workflow"}
    args.update({k: v for k, v in kwargs.items() if v is not None})
    return call_gateway_tool(name, args)


def startup_context(project_key: str, session_id: Optional[str] = None, budget_name: str = "small") -> dict[str, Any]:
    name = resolve_memory_tool_name("startup_context")
    args: dict[str, Any] = {"project_key": project_key, "budget_name": budget_name}
    if session_id:
        args["session_id"] = session_id
    return call_gateway_tool(name, args)


def append_event(
    session_id: str,
    event_kind: str,
    payload: dict[str, Any],
    *,
    idempotency_key: Optional[str] = None,
    trust_class: str = "project_verified",
) -> dict[str, Any]:
    name = resolve_memory_tool_name("append_event")
    args = {
        "session_id": session_id,
        "event_kind": event_kind,
        "idempotency_key": idempotency_key or str(uuid.uuid4()),
        "payload": payload,
        "trust_class": trust_class,
    }
    return call_gateway_tool(name, args)


def close_memory_session(session_id: str) -> dict[str, Any]:
    name = resolve_memory_tool_name("session_close")
    return call_gateway_tool(name, {"session_id": session_id})


def assert_ten_memory_tools() -> list[str]:
    from .node_tool_policy import assert_ten_memory_tools as _assert

    names = list_gateway_tools()
    _assert(names)
    return names
