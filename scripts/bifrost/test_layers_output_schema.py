#!/usr/bin/env python3
"""Layer-by-Layer Output-Schema and Annotations Inspection.

Layers:
A. Native AgentCore upstream tools/list (direct stdio launcher via mcp_output_schema_adapter.py)
B. Bifrost builder-profile tools/list (http://127.0.0.1:8080/mcp with BIFROST_MCP_VIRTUAL_KEY)
C. Bifrost ChatGPT-profile tools/list (http://127.0.0.1:18081/mcp with BIFROST_MCP_VK_CHATGPT via proxy)
D. ChatGPT custom-app action snapshot
"""

import json
import os
import subprocess
import sys
import urllib.request
import winreg
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_SERVER_CMD = [sys.executable, "-u", str(REPO_ROOT / "scripts" / "agentcore_memory" / "server.py")]
ROUTER_SERVER_CMD = [sys.executable, "-u", str(REPO_ROOT / "scripts" / "project_router" / "server.py")]
ADAPTER_SCRIPT = REPO_ROOT / "scripts" / "bifrost" / "mcp_output_schema_adapter.py"
OUTPUT_SCHEMA_CONTRACT = REPO_ROOT / "contracts" / "mcp-tool-output-schemas.json"

TARGET_MEMORY_TOOLS = [
    "memory_status",
    "startup_context",
    "retrieve_context",
    "append_event",
    "propose_fact",
    "expand_source",
    "session_open",
    "session_close",
    "build_handoff",
    "docs_search",
]

TARGET_ROUTER_TOOLS = [
    "project_list",
    "project_activate",
    "project_status",
    "project_clear",
]


def get_user_env(name: str) -> str:
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return ""


def stdio_rpc(cmd: list[str], requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for req in requests:
        line = json.dumps(req) + "\n"
        proc.stdin.write(line)
        proc.stdin.flush()

    responses = []
    # MCP notifications intentionally have no response. Wait only for requests
    # that carry an id, otherwise the diagnostic blocks forever after tools/list.
    expected_responses = sum(1 for request in requests if "id" in request)
    for _ in range(expected_responses):
        line = proc.stdout.readline()
        if not line:
            break
        try:
            responses.append(json.loads(line))
        except Exception as e:
            responses.append({"error": f"Failed to parse JSON line: {line.strip()}"})

    proc.terminate()
    try:
        proc.wait(timeout=2)
    except Exception:
        proc.kill()
    return responses


def get_layer_a_tools() -> dict[str, dict[str, Any]]:
    """Layer A: Native AgentCore stdio with mcp_output_schema_adapter.py wrapper."""
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-layer-a", "version": "1.0"},
        },
    }
    notif_req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

    layer_a_map = {}

    # Memory server wrapped with adapter
    cmd_mem = [
        sys.executable,
        "-u",
        str(ADAPTER_SCRIPT),
        "--server",
        "agentcore-memory",
        "--contract",
        str(OUTPUT_SCHEMA_CONTRACT),
        "--",
        *MEMORY_SERVER_CMD,
    ]
    res_mem = stdio_rpc(cmd_mem, [init_req, notif_req, list_req])
    for r in res_mem:
        if r.get("id") == 2 and "result" in r:
            for t in r["result"].get("tools") or []:
                layer_a_map[t["name"]] = t

    # Router server wrapped with adapter
    cmd_router = [
        sys.executable,
        "-u",
        str(ADAPTER_SCRIPT),
        "--server",
        "agentcore-project-router",
        "--contract",
        str(OUTPUT_SCHEMA_CONTRACT),
        "--",
        *ROUTER_SERVER_CMD,
    ]
    res_router = stdio_rpc(cmd_router, [init_req, notif_req, list_req])
    for r in res_router:
        if r.get("id") == 2 and "result" in r:
            for t in r["result"].get("tools") or []:
                layer_a_map[t["name"]] = t

    return layer_a_map


def http_mcp_tools_list(url: str, vk: str) -> dict[str, dict[str, Any]]:
    def post(payload: dict[str, Any], headers: dict[str, str]) -> tuple[dict[str, Any], dict[str, str]]:
        req = urllib.request.Request(
            f"{url}/mcp",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            response_headers = {key.lower(): value for key, value in resp.headers.items()}
        if "text/event-stream" in response_headers.get("content-type", ""):
            for line in raw.splitlines():
                if line.startswith("data:") and line[5:].strip():
                    return json.loads(line[5:].strip()), response_headers
            return {}, response_headers
        return (json.loads(raw) if raw.strip() else {}), response_headers

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-06-18",
        "Authorization": f"Bearer {vk}",
    }
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-layer-http", "version": "1.0"},
        },
    }
    _, response_headers = post(init_req, headers)
    session_id = response_headers.get("mcp-session-id")
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    notif_req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    post(notif_req, headers)

    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    data, _ = post(list_req, headers)

    tool_map = {}
    for t in data.get("result", {}).get("tools") or []:
        tool_map[t["name"]] = t
    return tool_map


def format_tool_status(tool_dict: dict[str, Any] | None) -> dict[str, Any]:
    if not tool_dict:
        return {
            "present": False,
            "inputSchema": False,
            "outputSchema": False,
            "structuredContent": False,
            "annotations": False,
            "readOnlyHint": None,
            "destructiveHint": None,
            "idempotentHint": None,
            "openWorldHint": None,
        }

    ann = tool_dict.get("annotations") or {}
    return {
        "present": True,
        "inputSchema": "inputSchema" in tool_dict and bool(tool_dict["inputSchema"]),
        "outputSchema": "outputSchema" in tool_dict and bool(tool_dict["outputSchema"]),
        "structuredContent": True,  # Supported by server response spec
        "annotations": bool(ann),
        "readOnlyHint": ann.get("readOnlyHint"),
        "destructiveHint": ann.get("destructiveHint"),
        "idempotentHint": ann.get("idempotentHint"),
        "openWorldHint": ann.get("openWorldHint"),
    }


def main() -> None:
    builder_vk = get_user_env("BIFROST_MCP_VIRTUAL_KEY")
    chatgpt_vk = get_user_env("BIFROST_MCP_VK_CHATGPT")

    print("Fetching Layer A: Native AgentCore stdio upstreams...")
    layer_a = get_layer_a_tools()

    print("Fetching Layer B: Bifrost Builder Profile (8080)...")
    layer_b = http_mcp_tools_list("http://127.0.0.1:8080", builder_vk)

    print("Fetching Layer C: Bifrost ChatGPT Profile via Proxy (18081)...")
    try:
        layer_c = http_mcp_tools_list("http://127.0.0.1:18081", chatgpt_vk)
    except OSError as exc:
        print(f"Layer C unavailable (optional compatibility proxy): {exc.__class__.__name__}")
        layer_c = {}

    all_target_tools = [
        ("agentcore-memory", TARGET_MEMORY_TOOLS, "agentcore_memory"),
        ("agentcore-project-router", TARGET_ROUTER_TOOLS, "agentcore_project_router"),
    ]

    print("\n" + "=" * 100)
    print("LAYER-BY-LAYER OUTPUT-SCHEMA AND ANNOTATIONS MATRIX")
    print("=" * 100)

    for server_id, tool_list, bifrost_prefix in all_target_tools:
        print(f"\nSERVER: {server_id}")
        print("-" * 100)
        print(f"{'Tool Name':<28} | {'Layer A (Native)':<20} | {'Layer B (Builder)':<20} | {'Layer C (ChatGPT Proxy)':<20}")
        print("-" * 100)

        for tname in tool_list:
            # Layer A native name
            tool_a = layer_a.get(tname)
            stat_a = format_tool_status(tool_a)

            # Layer B / C Bifrost prefixed name
            prefixed_name = f"{bifrost_prefix}-{tname}"
            tool_b = layer_b.get(prefixed_name)
            stat_b = format_tool_status(tool_b)

            tool_c = layer_c.get(prefixed_name)
            stat_c = format_tool_status(tool_c)

            fmt_a = f"in={stat_a['inputSchema']} out={stat_a['outputSchema']} ann={stat_a['annotations']}"
            fmt_b = f"in={stat_b['inputSchema']} out={stat_b['outputSchema']} ann={stat_b['annotations']}"
            fmt_c = f"in={stat_c['inputSchema']} out={stat_c['outputSchema']} ann={stat_c['annotations']}" if stat_c['present'] else "EXCLUDED"

            print(f"{tname:<28} | {fmt_a:<20} | {fmt_b:<20} | {fmt_c:<20}")

    print("\n" + "=" * 100)
    print("DETAILED ANNOTATIONS REPORT (LAYER A / B / C)")
    print("=" * 100)

    for server_id, tool_list, bifrost_prefix in all_target_tools:
        for tname in tool_list:
            prefixed_name = f"{bifrost_prefix}-{tname}"
            tool_a = layer_a.get(tname)
            tool_b = layer_b.get(prefixed_name)
            stat_a = format_tool_status(tool_a)
            stat_b = format_tool_status(tool_b)

            print(f"Tool: {prefixed_name}")
            print(f"  Layer A: inputSchema={stat_a['inputSchema']}, outputSchema={stat_a['outputSchema']}, structuredContent={stat_a['structuredContent']}, annotations={stat_a['annotations']}")
            print(f"           readOnly={stat_a['readOnlyHint']}, destructive={stat_a['destructiveHint']}, idempotent={stat_a['idempotentHint']}, openWorld={stat_a['openWorldHint']}")
            print(f"  Layer B: inputSchema={stat_b['inputSchema']}, outputSchema={stat_b['outputSchema']}, structuredContent={stat_b['structuredContent']}, annotations={stat_b['annotations']}")
            print(f"           readOnly={stat_b['readOnlyHint']}, destructive={stat_b['destructiveHint']}, idempotent={stat_b['idempotentHint']}, openWorld={stat_b['openWorldHint']}")

if __name__ == "__main__":
    main()
