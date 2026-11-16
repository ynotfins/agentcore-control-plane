"""Enforce the progressive (Code Mode) AgentCore gateway tool surface.

Rule (proposal governance/proposals/2026-11-15-gateway-progressive-tool-surface-enforcement.md):
only an explicit essential allowlist of Bifrost MCP clients may be eager
(is_code_mode_client != true). Every other enabled client must be a Code Mode
client so its tools are discovered on demand via listToolFiles -> readToolFile
-> getToolDocs -> executeToolCode instead of being pushed into every tools/list.

Checks:
  static   registry + rendered/live Bifrost config.json client flags
  --live   optional tools/list probe through http://127.0.0.1:8080/mcp using a
           named User-scope virtual-key env var (value never printed); fails
           when the eager tool count exceeds --max-tools.

Exit 0 = pass, 1 = violation, 2 = usage/runtime error. Never prints secrets.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO / "contracts" / "bifrost-upstream-mcp-registry.json"
LIVE_CONFIG = Path(r"F:\AgentCore\runtime\bifrost\config.json")

# Eager essentials. Everything else must be Code Mode.
ESSENTIAL_EAGER = {
    "agentcore_memory",               # lifecycle: session_open/startup_context/... (10 tools)
    "sequential_thinking",            # 1 tool
    "agentcore_capability_catalog",   # 2-tool discovery surface
    "arabold_docs",                   # docs-first rule; candidate for Code Mode (see proposal)
    "agentcore_project_router",       # operator VK only (4 tools); never granted to builder/ide
}
DEFAULT_MAX_TOOLS = 30  # 4 Code Mode meta tools + essentials (27 on 2026-11-15)


def read_env(name: str) -> str:
    value = os.environ.get(name) or ""
    if not value and os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                value, _ = winreg.QueryValueEx(key, name)
        except OSError:
            value = ""
    return str(value or "")


def registry_violations(registry: dict[str, Any], essential: set[str]) -> list[str]:
    out: list[str] = []
    for sid, server in (registry.get("servers") or {}).items():
        if not isinstance(server, dict) or not server.get("enabled"):
            continue
        name = str(server.get("bifrost_client_name") or sid)
        if name in essential:
            continue
        if server.get("is_code_mode_client") is not True:
            out.append("registry:%s enabled but is_code_mode_client=%r" % (name, server.get("is_code_mode_client")))
    return out


def config_violations(config: dict[str, Any], essential: set[str]) -> list[str]:
    out: list[str] = []
    for client in ((config.get("mcp") or {}).get("client_configs")) or []:
        if not isinstance(client, dict):
            continue
        name = str(client.get("name") or "")
        if not name or name in essential:
            continue
        if client.get("is_code_mode_client") is not True:
            out.append("config:%s is eager (is_code_mode_client=%r, %s tools)" % (
                name, client.get("is_code_mode_client"), len(client.get("tools_to_execute") or [])))
    return out


def _post(url: str, headers: dict[str, str], body: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        hdrs = {k.lower(): v for k, v in resp.headers.items()}
    if "data:" in raw and not raw.lstrip().startswith("{"):
        raw = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:")][-1]
    return (json.loads(raw) if raw.strip() else {}), hdrs


def live_tool_count(url: str, key_env: str) -> int:
    key = read_env(key_env)
    if not key:
        raise RuntimeError("env var %s not set" % key_env)
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "Authorization": "Bearer " + key}
    _, h = _post(url, headers, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "eager-budget-check", "version": "1"}}})
    if h.get("mcp-session-id"):
        headers["Mcp-Session-Id"] = h["mcp-session-id"]
    total, cursor = 0, None
    while True:
        params = {"cursor": cursor} if cursor else {}
        j, _ = _post(url, headers, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": params})
        res = j.get("result") or {}
        total += len(res.get("tools") or [])
        cursor = res.get("nextCursor")
        if not cursor:
            return total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--config", default=str(LIVE_CONFIG) if LIVE_CONFIG.is_file() else "")
    ap.add_argument("--skip-registry", action="store_true", help="Skip registry check (e.g. pending locked-contract change)")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--url", default="http://127.0.0.1:8080/mcp")
    ap.add_argument("--key-env", action="append", default=[], help="Virtual-key env var name(s); default BIFROST_MCP_VIRTUAL_KEY")
    ap.add_argument("--max-tools", type=int, default=DEFAULT_MAX_TOOLS)
    args = ap.parse_args(argv)

    problems: list[str] = []
    if not args.skip_registry:
        problems += registry_violations(json.loads(Path(args.registry).read_text(encoding="utf-8")), ESSENTIAL_EAGER)
    if args.config:
        problems += config_violations(json.loads(Path(args.config).read_text(encoding="utf-8")), ESSENTIAL_EAGER)
    if args.live:
        for env in args.key_env or ["BIFROST_MCP_VIRTUAL_KEY"]:
            try:
                n = live_tool_count(args.url, env)
            except Exception as exc:  # noqa: BLE001
                print("LIVE_ERROR %s %s" % (env, type(exc).__name__))
                return 2
            status = "OK" if n <= args.max_tools else "OVER_BUDGET"
            print("LIVE %s tools=%d max=%d %s" % (env, n, args.max_tools, status))
            if n > args.max_tools:
                problems.append("live:%s exposes %d tools (> %d)" % (env, n, args.max_tools))
    for p in problems:
        print("VIOLATION", p)
    print("EAGER_BUDGET_CHECK", "FAIL" if problems else "PASS", "violations=%d" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
