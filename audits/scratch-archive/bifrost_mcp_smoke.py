"""Authenticated Bifrost MCP smoke test. Never prints the virtual key."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import winreg

URL = "http://127.0.0.1:8080/mcp"


def user_env(name: str) -> str:
    val = os.environ.get(name) or ""
    if val:
        return val
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            val, _ = winreg.QueryValueEx(k, name)
            return str(val or "")
    except OSError:
        return ""


def mcp_post(payload: dict, session_id: str | None = None) -> tuple[int, dict, dict]:
    body = json.dumps(payload).encode("utf-8")
    vk = user_env("BIFROST_MCP_VIRTUAL_KEY")
    if not vk:
        raise SystemExit("missing BIFROST_MCP_VIRTUAL_KEY")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {vk}",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            code = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        hdrs = {k.lower(): v for k, v in e.headers.items()}
        code = e.code
    # Parse JSON or SSE data lines
    data = None
    if raw.strip().startswith("{"):
        data = json.loads(raw)
    else:
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if chunk and chunk != "[DONE]":
                    try:
                        data = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
    return code, data or {"raw_prefix": raw[:200]}, hdrs


def main() -> int:
    vk = user_env("BIFROST_MCP_VIRTUAL_KEY")
    digest = hashlib.sha256(vk.encode("utf-8")).hexdigest()[:12]
    print(f"vk_present={bool(vk)} vk_len={len(vk)} vk_sha256_12={digest}")

    # health already checked separately; initialize
    code, data, hdrs = mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "agentcore-cherry-smoke", "version": "0.1.0"},
            },
        }
    )
    session = hdrs.get("mcp-session-id")
    print(f"initialize status={code} session={bool(session)} keys={list((data or {}).keys())}")
    if code >= 400:
        print("initialize_failed", json.dumps(data)[:500])
        return 2

    # notifications/initialized
    code2, _, _ = mcp_post(
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session_id=session,
    )
    print(f"initialized_notification status={code2}")

    code3, tools, _ = mcp_post(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        session_id=session,
    )
    tool_list = ((tools or {}).get("result") or {}).get("tools") or []
    names = [t.get("name") for t in tool_list]
    prefixes = sorted({(n.split("-", 1)[0] if "-" in n else n.split("_", 1)[0]) for n in names if n})
    mem = [n for n in names if n and ("agentcore_memory" in n or n.startswith("memory_"))]
    swarm = [n for n in names if n and "swarm" in n.lower()]
    print(f"tools/list status={code3} total={len(names)} prefixes={prefixes}")
    print(f"memory_tools_count={len(mem)}")
    print("memory_tools=", sorted(mem))
    print(f"swarm_tools_count={len(swarm)}")

    # safe read-only call
    mem_tool = next((n for n in names if n.endswith("memory_status") or n == "memory_status"), None)
    if not mem_tool:
        print("no memory_status tool")
        return 3
    code4, status, _ = mcp_post(
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": mem_tool, "arguments": {}}},
        session_id=session,
    )
    result = (status or {}).get("result") or {}
    # sanitize content text length only
    content = result.get("content") or []
    text_lens = [len(c.get("text", "")) for c in content if isinstance(c, dict)]
    print(f"memory_status status={code4} content_parts={len(content)} text_lens={text_lens}")
    # check localhost binding hint via URL constant
    print("endpoint=", URL)
    print("SMOKE=PASS" if code == 200 and code3 == 200 and code4 == 200 and not swarm else "SMOKE=FAIL")
    return 0 if code == 200 and code3 == 200 and code4 == 200 and not swarm else 4


if __name__ == "__main__":
    raise SystemExit(main())
