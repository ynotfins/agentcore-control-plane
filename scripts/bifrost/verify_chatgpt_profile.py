#!/usr/bin/env python3
"""Verification script for Bifrost ChatGPT Profile and Output-Schema Acceptance.

Tests:
1. Direct Health endpoint (8080/health) -> 200
2. Proxy Health endpoint (18081/healthz) -> 200
3. ChatGPT profile existence in runtime config
4. Normalized permission set verification (no wildcards)
5. Environment variable inheritance (BIFROST_MCP_VK_CHATGPT)
6. MCP authentication with actual ChatGPT key
7. tools/list filtering (no builder/operator fallback)
8. Exact surface validation (21 approved tools)
9. Output-schema status at Layer A, Layer B, Layer C
"""

import json
import os
import urllib.request
import urllib.error
import winreg
from pathlib import Path
from typing import Any

BIFROST_URL = "http://127.0.0.1:8080"
PROXY_URL = "http://127.0.0.1:18081"
RUNTIME_CONFIG = Path(r"H:\AgentRuntime\bifrost\config.json")

EXPECTED_APPROVED_TOOLS = {
    # agentcore_memory (9)
    "agentcore_memory-memory_status",
    "agentcore_memory-startup_context",
    "agentcore_memory-retrieve_context",
    "agentcore_memory-expand_source",
    "agentcore_memory-docs_search",
    "agentcore_memory-session_open",
    "agentcore_memory-append_event",
    "agentcore_memory-build_handoff",
    "agentcore_memory-session_close",
    # agentcore_project_router (3)
    "agentcore_project_router-project_list",
    "agentcore_project_router-project_status",
    "agentcore_project_router-project_activate",
    # skills_hub (3)
    "skills_hub-search_skills",
    "skills_hub-get_skill_detail",
    "skills_hub-list_installed_skills",
    # arabold_docs (5)
    "arabold_docs-search_docs",
    "arabold_docs-fetch_url",
    "arabold_docs-list_libraries",
    "arabold_docs-find_version",
    "arabold_docs-get_job_info",
    # sequential_thinking (1)
    "sequential_thinking-sequentialthinking",
}

EXCLUDED_PROHIBITED_TOOLS = {
    "agentcore_project_router-project_clear",
    "agentcore_memory-propose_fact",
    "filesystem-read_file",
    "filesystem-write_file",
    "filesystem-edit_file",
    "playwright-browser_click",
    "playwright-browser_navigate",
    "serena-find_declaration",
    "serena-replace_symbol_body",
    "depwire-connect_repo",
    "depwire-impact_analysis",
    "tentra-analyze_codebase",
    "skills_hub-install_skill",
}


def get_chatgpt_vk() -> str:
    vk = os.environ.get("BIFROST_MCP_VK_CHATGPT")
    if vk:
        return vk
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        vk, _ = winreg.QueryValueEx(key, "BIFROST_MCP_VK_CHATGPT")
        winreg.CloseKey(key)
        return vk
    except Exception:
        return ""


def check_health(url: str, path: str = "/health") -> tuple[bool, str]:
    try:
        req = urllib.request.Request(f"{url}{path}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return resp.status == 200, body
    except Exception as e:
        return False, str(e)


def check_profile_config() -> tuple[bool, dict[str, Any], list[str]]:
    errors = []
    if not RUNTIME_CONFIG.exists():
        return False, {}, ["Runtime config missing at H:\\AgentRuntime\\bifrost\\config.json"]

    data = json.loads(RUNTIME_CONFIG.read_text(encoding="utf-8"))
    vks = data.get("governance", {}).get("virtual_keys") or []
    chatgpt_vk = None
    for vk in vks:
        if vk.get("name") == "chatgpt" or vk.get("id") == "vk-agentcore-chatgpt":
            chatgpt_vk = vk
            break

    if not chatgpt_vk:
        return False, {}, ["vk-agentcore-chatgpt not found in H:\\AgentRuntime\\bifrost\\config.json"]

    mcp_configs = chatgpt_vk.get("mcp_configs") or []
    found_clients = {}
    for mc in mcp_configs:
        cname = mc.get("mcp_client_name")
        tools = mc.get("tools_to_execute") or []
        found_clients[cname] = tools
        if "*" in tools:
            errors.append(f"Wildcard '*' found in chatgpt profile for client {cname}")

    expected_mem = {"memory_status", "startup_context", "retrieve_context", "expand_source", "docs_search", "session_open", "append_event", "build_handoff", "session_close"}
    expected_router = {"project_list", "project_status", "project_activate"}
    expected_skills = {"search_skills", "get_skill_detail", "list_installed_skills"}
    expected_arabold = {"search_docs", "fetch_url", "list_libraries", "find_version", "get_job_info"}
    expected_seq = {"sequentialthinking"}

    if set(found_clients.get("agentcore_memory", [])) != expected_mem:
        errors.append(f"agentcore_memory tool mismatch: got {found_clients.get('agentcore_memory')}")

    if set(found_clients.get("agentcore_project_router", [])) != expected_router:
        errors.append(f"agentcore_project_router tool mismatch: got {found_clients.get('agentcore_project_router')}")

    if set(found_clients.get("skills_hub", [])) != expected_skills:
        errors.append(f"skills_hub tool mismatch: got {found_clients.get('skills_hub')}")

    if set(found_clients.get("arabold_docs", [])) != expected_arabold:
        errors.append(f"arabold_docs tool mismatch: got {found_clients.get('arabold_docs')}")

    if set(found_clients.get("sequential_thinking", [])) != expected_seq:
        errors.append(f"sequential_thinking tool mismatch: got {found_clients.get('sequential_thinking')}")

    forbidden_servers = {"filesystem", "serena", "depwire", "playwright", "tentra", "cursor_agent_mcp", "context_fabric", "openrouter"}
    for fserver in forbidden_servers:
        if fserver in found_clients:
            errors.append(f"Forbidden server {fserver!r} found in chatgpt profile")

    return len(errors) == 0, chatgpt_vk, errors


def mcp_request(base_url: str, vk: str, payload: dict[str, Any], session_id: str | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
    url = f"{base_url}/mcp"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {vk}",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            resp_headers = dict(resp.headers)
            body = resp.read().decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {"raw_body": body}
            return status, data, resp_headers
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            data = json.loads(body)
        except Exception:
            data = {"raw_body": body}
        return e.code, data, dict(e.headers)
    except Exception as e:
        return 500, {"error": str(e)}, {}


def test_mcp_tools_list(base_url: str, vk: str) -> tuple[bool, list[dict[str, Any]], list[str]]:
    errors = []
    # 1. Initialize
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "verify-chatgpt-script", "version": "1.0.0"},
        },
    }
    status, res, headers = mcp_request(base_url, vk, init_payload)
    if status != 200 or "result" not in res:
        return False, [], [f"Initialize failed with status {status}: {res}"]

    session_id = headers.get("mcp-session-id") or headers.get("Mcp-Session-Id")

    # 2. Initialized notification
    notif_payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }
    mcp_request(base_url, vk, notif_payload, session_id=session_id)

    # 3. tools/list
    list_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }
    status, res, _ = mcp_request(base_url, vk, list_payload, session_id=session_id)
    if status != 200 or "result" not in res:
        return False, [], [f"tools/list failed with status {status}: {res}"]

    tools = res["result"].get("tools") or []
    tool_names = {t["name"] for t in tools}

    # Verify tool filtering
    if tool_names != EXPECTED_APPROVED_TOOLS:
        missing = EXPECTED_APPROVED_TOOLS - tool_names
        extra = tool_names - EXPECTED_APPROVED_TOOLS
        if missing:
            errors.append(f"Missing approved tools: {missing}")
        if extra:
            errors.append(f"Unexpected extra tools (potential fallback/leak): {extra}")

    # Explicit check for prohibited tools
    prohibited_found = tool_names & EXCLUDED_PROHIBITED_TOOLS
    if prohibited_found:
        errors.append(f"Prohibited tools found in tools/list: {prohibited_found}")

    return len(errors) == 0, tools, errors


def test_proxy_deny_paths() -> tuple[bool, list[str]]:
    errors = []
    denied_paths = [
        "/",
        "/api/v1/status",
        "/workspace/files",
        "/v1/chat/completions",
        "/logs",
        "/dashboard",
        "/ui/index.html",
    ]
    for path in denied_paths:
        try:
            req = urllib.request.Request(f"{PROXY_URL}{path}")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status != 403:
                    errors.append(f"Path {path} returned HTTP {resp.status}, expected 403 Forbidden")
        except urllib.error.HTTPError as e:
            if e.code != 403:
                errors.append(f"Path {path} returned HTTP {e.code}, expected 403 Forbidden")
        except Exception as e:
            errors.append(f"Path {path} threw unexpected error: {e}")

    return len(errors) == 0, errors


def main() -> None:
    vk = get_chatgpt_vk()
    print(f"ChatGPT Virtual Key retrieved from User env: {'PRESENT (len=' + str(len(vk)) + ')' if vk else 'MISSING'}")
    if not vk:
        print("FAIL: BIFROST_MCP_VK_CHATGPT is missing in User environment variables.")
        return

    # 1. Health check
    ok, body = check_health(BIFROST_URL, "/health")
    print(f"Bifrost Direct Health check (8080/health): {'PASS' if ok else 'FAIL'} -> {body.strip()}")

    ok_proxy, body_proxy = check_health(PROXY_URL, "/healthz")
    print(f"Proxy Health check (18081/healthz): {'PASS' if ok_proxy else 'FAIL'} -> {body_proxy.strip()}")

    # 2. Profile config check
    ok_cfg, vk_block, cfg_errs = check_profile_config()
    print(f"Profile config check in runtime config.json: {'PASS' if ok_cfg else 'FAIL'}")
    if cfg_errs:
        for err in cfg_errs:
            print(f"  - ERROR: {err}")

    # 3. Direct Bifrost actual key test
    ok_direct, tools_direct, errs_direct = test_mcp_tools_list(BIFROST_URL, vk)
    print(f"Direct Bifrost actual ChatGPT key tools/list (8080): {'PASS' if ok_direct else 'FAIL'} (tools count: {len(tools_direct)})")
    if errs_direct:
        for err in errs_direct:
            print(f"  - ERROR: {err}")

    # 4. Proxy actual key test
    ok_proxy_mcp, tools_proxy, errs_proxy = test_mcp_tools_list(PROXY_URL, vk)
    print(f"Proxy actual ChatGPT key tools/list (18081): {'PASS' if ok_proxy_mcp else 'FAIL'} (tools count: {len(tools_proxy)})")
    if errs_proxy:
        for err in errs_proxy:
            print(f"  - ERROR: {err}")

    # 5. Proxy path deny test
    ok_deny, deny_errs = test_proxy_deny_paths()
    print(f"Proxy path deny tests (403 Forbidden enforcement): {'PASS' if ok_deny else 'FAIL'}")
    if deny_errs:
        for err in deny_errs:
            print(f"  - ERROR: {err}")

    # 6. Print tools summary
    if tools_direct:
        print("\nApproved ChatGPT tools exposed:")
        for t in sorted(tools_direct, key=lambda x: x["name"]):
            has_input_schema = "inputSchema" in t and bool(t["inputSchema"])
            has_output_schema = "outputSchema" in t and bool(t["outputSchema"])
            has_annotations = "annotations" in t and bool(t["annotations"])
            print(f"  - {t['name']:<42} inputSchema={has_input_schema:<5} outputSchema={has_output_schema:<5} annotations={has_annotations}")

if __name__ == "__main__":
    main()
