"""One-shot live proof for OpenRouter JIT bridge (no secrets printed)."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import urllib.request

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "bifrost"))
from jit_vk_bridge import (  # noqa: E402
    list_openrouter_tools_on_vk,
    revoke_openrouter_tools,
    sync_lease_group,
)


def _operator_vk() -> str:
    vk = os.environ.get("BIFROST_MCP_VK_OPERATOR") or ""
    if vk:
        return vk
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
        vk, _ = winreg.QueryValueEx(k, "BIFROST_MCP_VK_OPERATOR")
    return str(vk)


def tools_list() -> list[str]:
    vk = _operator_vk()
    req = urllib.request.Request(
        "http://127.0.0.1:8080/mcp",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode(),
        headers={
            "Authorization": f"Bearer {vk}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode()
    m = re.search(r"data:\s*(\{.*\})", raw, re.S)
    payload = json.loads(m.group(1) if m else raw)
    return [t["name"] for t in payload.get("result", {}).get("tools", [])]


def main() -> int:
    con = sqlite3.connect(r"file:H:\AgentRuntime\bifrost\data\config.db?mode=ro", uri=True)
    row = con.execute(
        "SELECT discovered_tools_json FROM config_mcp_clients WHERE name = ?",
        ("openrouter",),
    ).fetchone()
    disc = json.loads(row[0] or "[]")
    names = []
    for t in disc:
        if isinstance(t, dict):
            names.append(t.get("name") or t.get("Name"))
        else:
            names.append(str(t))
    print("discovered_count", len(names))
    print(
        "has_preset",
        "get-preset" in names,
        "list-presets" in names,
        "generate-speech" in names,
        "transcribe-audio" in names,
    )

    r = sync_lease_group("openrouter-discovery-read", active=True)
    print("grant", r.ok, r.detail, "n=", len(r.tools))
    print("vk_tools_n", len(list_openrouter_tools_on_vk()))
    tools = tools_list()
    or_tools = sorted(t for t in tools if t.startswith("openrouter"))
    print("visible_openrouter", len(or_tools))
    print(or_tools)
    mem = [t for t in tools if "memory" in t or t.endswith("session_open")]
    print("memoryish_count", len(mem), "total", len(tools))

    r2 = revoke_openrouter_tools()
    print("revoke", r2.ok, r2.detail, list_openrouter_tools_on_vk())
    tools2 = tools_list()
    or2 = [t for t in tools2 if t.startswith("openrouter")]
    print("after_revoke_openrouter", or2, "total", len(tools2))
    return 0 if r.ok and r2.ok and not or2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
