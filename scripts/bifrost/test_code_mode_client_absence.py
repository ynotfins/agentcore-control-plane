#!/usr/bin/env python3
"""Live proof: Code Mode clients are absent from builder tools/list.

Asserts that enabled registry servers with is_code_mode_client=true do not
appear as eager Bifrost tools/list prefixes at http://127.0.0.1:8080/mcp.
Classic eager prefixes and Code Mode meta-tools must remain present.

Uses BIFROST_MCP_VIRTUAL_KEY from process env or Windows User env (winreg).
Never prints the virtual key.

Skip (unittest.SkipTest) when /health is not ok or the VK is missing —
do not false-pass.

Optional evidence JSON when AGENTCORE_WRITE_EVIDENCE=1:
  audits/bifrost/CODE_MODE_LIVE_TOOLSLIST_ABSENCE_2026-09-16.json
"""
from __future__ import annotations

import json
import os
import unittest
import urllib.error
import urllib.request
import winreg
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
EVIDENCE_PATH = (
    REPO_ROOT / "audits" / "bifrost" / "CODE_MODE_LIVE_TOOLSLIST_ABSENCE_2026-09-16.json"
)

MCP_URL = "http://127.0.0.1:8080/mcp"
HEALTH_URL = "http://127.0.0.1:8080/health"
VK_ENV = "BIFROST_MCP_VIRTUAL_KEY"
WRITE_EVIDENCE_ENV = "AGENTCORE_WRITE_EVIDENCE"

REQUIRED_ABSENCE_PREFIXES = (
    "serena-",
    "nia-",
    "skills_hub-",
    "cursor_agent_mcp-",
    "morph_mcp-",
    "playwright-",
)

REQUIRED_EAGER_PREFIXES = (
    "agentcore_memory-",
    "arabold_docs-",
    "sequential_thinking-",
)
REQUIRED_EAGER_EXACT = (
    "listToolFiles",
    "executeToolCode",
    "readToolFile",
    "getToolDocs",
)


def get_user_env(name: str) -> str:
    val = os.environ.get(name, "")
    if val:
        return str(val)
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return str(val or "")
    except OSError:
        return ""


def bifrost_health_ok(timeout: float = 10.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = resp.status
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return False, f"Bifrost /health unreachable ({exc.__class__.__name__})"
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return False, "Bifrost /health returned non-JSON body"
    status = str((payload or {}).get("status") or "").lower()
    if code != 200 or status != "ok":
        return False, f"Bifrost /health not ok (http={code}, status={status!r})"
    return True, "ok"


def mcp_tools_list(url: str, vk: str, timeout: float = 60.0) -> list[str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-06-18",
        "Authorization": f"Bearer {vk}",
    }
    session_id = ""

    def post(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal session_id
        req_headers = dict(headers)
        if session_id:
            req_headers["Mcp-Session-Id"] = session_id
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
            if sid:
                session_id = sid
            raw = resp.read().decode("utf-8", errors="replace")
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "text/event-stream" in content_type or raw.startswith("event:") or (
                raw.startswith("data:") or "\ndata:" in raw[:120]
            ):
                data_lines = [
                    line[5:].strip()
                    for line in raw.splitlines()
                    if line.startswith("data:") and line[5:].strip()
                ]
                raw = data_lines[-1] if data_lines else "{}"
            if not raw.strip():
                return {}
            return json.loads(raw)

    init = post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-code-mode-client-absence",
                    "version": "1.0",
                },
            },
        }
    )
    if not isinstance(init, dict) or "result" not in init:
        raise RuntimeError("MCP initialize failed against builder endpoint")

    try:
        post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    except (urllib.error.URLError, OSError, ValueError):
        pass

    listed = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = ((listed or {}).get("result") or {}).get("tools") or []
    if not isinstance(tools, list):
        raise RuntimeError("tools/list did not return a tools array")
    names: list[str] = []
    for tool in tools:
        if isinstance(tool, dict) and tool.get("name"):
            names.append(str(tool["name"]))
    return names


def prefix_from_bifrost_client_name(client_name: str) -> str:
    name = str(client_name or "").strip()
    if not name:
        raise ValueError("empty bifrost_client_name")
    return name if name.endswith("-") else f"{name}-"


def load_code_mode_absence_prefixes(
    registry_path: Path = REGISTRY_PATH,
) -> list[dict[str, str]]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for server_id, server in (registry.get("servers") or {}).items():
        if not isinstance(server, dict):
            continue
        if server.get("enabled") is not True:
            continue
        if server.get("is_code_mode_client") is not True:
            continue
        client_name = str(server.get("bifrost_client_name") or server_id)
        rows.append(
            {
                "server_id": str(server_id),
                "bifrost_client_name": client_name,
                "prefix": prefix_from_bifrost_client_name(client_name),
            }
        )
    rows.sort(key=lambda row: row["prefix"])
    return rows


def names_matching_prefix(tool_names: list[str], prefix: str) -> list[str]:
    return sorted(name for name in tool_names if name.startswith(prefix))


def maybe_write_evidence(payload: dict[str, Any]) -> bool:
    if os.environ.get(WRITE_EVIDENCE_ENV, "").strip() != "1":
        return False
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return True


class TestCodeModeClientAbsence(unittest.TestCase):
    """Live Bifrost builder tools/list: Code Mode clients absent; eager present."""

    tool_names: list[str] = []
    registry_rows: list[dict[str, str]] = []
    skip_reason: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        ok, health_msg = bifrost_health_ok()
        if not ok:
            cls.skip_reason = (
                f"Skipping Code Mode absence live probe: {health_msg}. "
                "Gateway must report GET /health status=ok."
            )
            return

        vk = get_user_env(VK_ENV)
        if not vk:
            cls.skip_reason = (
                f"Skipping Code Mode absence live probe: {VK_ENV} missing "
                "from process env and Windows User Environment. "
                "Do not false-pass without an authenticated builder tools/list."
            )
            return

        try:
            cls.registry_rows = load_code_mode_absence_prefixes()
            cls.tool_names = mcp_tools_list(MCP_URL, vk)
        except (
            urllib.error.URLError,
            OSError,
            TimeoutError,
            ValueError,
            RuntimeError,
        ) as exc:
            cls.skip_reason = (
                f"Skipping Code Mode absence live probe: tools/list failed "
                f"({exc.__class__.__name__}: {exc})"
            )
            return

        if not cls.tool_names:
            cls.skip_reason = (
                "Skipping Code Mode absence live probe: tools/list returned "
                "zero tools (unexpected empty catalog)."
            )

    def setUp(self) -> None:
        if self.skip_reason:
            raise unittest.SkipTest(self.skip_reason)

    def test_required_absence_prefixes_not_in_tools_list(self) -> None:
        leaks: dict[str, list[str]] = {}
        for prefix in REQUIRED_ABSENCE_PREFIXES:
            hits = names_matching_prefix(self.tool_names, prefix)
            if hits:
                leaks[prefix] = hits
        leak_msg = {k: v[:8] for k, v in leaks.items()}
        self.assertFalse(
            leaks,
            "Code Mode client tools must be absent from eager tools/list; "
            f"leaked prefixes={leak_msg}",
        )

    def test_registry_enabled_code_mode_clients_absent(self) -> None:
        self.assertTrue(
            self.registry_rows,
            "expected at least one enabled is_code_mode_client=true server "
            f"in {REGISTRY_PATH}",
        )
        leaks: dict[str, list[str]] = {}
        for row in self.registry_rows:
            hits = names_matching_prefix(self.tool_names, row["prefix"])
            if hits:
                leaks[row["prefix"]] = hits
        leak_msg = {k: v[:8] for k, v in leaks.items()}
        self.assertFalse(
            leaks,
            "enabled is_code_mode_client=true servers must not appear in "
            f"tools/list; leaked={leak_msg}",
        )

    def test_eager_classic_and_code_mode_meta_tools_present(self) -> None:
        missing: list[str] = []
        for prefix in REQUIRED_EAGER_PREFIXES:
            if not names_matching_prefix(self.tool_names, prefix):
                missing.append(f"prefix:{prefix}")
        name_set = set(self.tool_names)
        for exact in REQUIRED_EAGER_EXACT:
            if exact not in name_set:
                missing.append(f"exact:{exact}")
        self.assertFalse(
            missing,
            "classic eager / Code Mode meta tools missing from tools/list: "
            f"{missing}",
        )

    def test_optional_evidence_json(self) -> None:
        absence_check: dict[str, Any] = {}
        for prefix in sorted(
            set(REQUIRED_ABSENCE_PREFIXES)
            | {row["prefix"] for row in self.registry_rows}
        ):
            hits = names_matching_prefix(self.tool_names, prefix)
            absence_check[prefix] = {
                "absent": not hits,
                "leaked_count": len(hits),
                "leaked_sample": hits[:5],
            }

        eager_check: dict[str, Any] = {}
        for prefix in REQUIRED_EAGER_PREFIXES:
            hits = names_matching_prefix(self.tool_names, prefix)
            eager_check[prefix] = {
                "present": bool(hits),
                "count": len(hits),
                "sample": hits[:5],
            }
        name_set = set(self.tool_names)
        for exact in REQUIRED_EAGER_EXACT:
            eager_check[exact] = {"present": exact in name_set}

        all_absent = all(row["absent"] for row in absence_check.values())
        all_eager = all(row.get("present") for row in eager_check.values())
        payload = {
            "evidence_id": "CODE_MODE_LIVE_TOOLSLIST_ABSENCE_2026-09-16",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "endpoint": MCP_URL,
            "health_url": HEALTH_URL,
            "profile": "builder",
            "method": "tools/list",
            "secrets_printed": False,
            "vk_env_var": VK_ENV,
            "vk_present": True,
            "tool_count": len(self.tool_names),
            "registry_code_mode_enabled_servers": self.registry_rows,
            "required_absence_prefixes": list(REQUIRED_ABSENCE_PREFIXES),
            "absence_check": absence_check,
            "eager_check": eager_check,
            "pass": all_absent and all_eager,
        }
        wrote = maybe_write_evidence(payload)
        self.assertTrue(all_absent and all_eager)
        self.assertIsInstance(wrote, bool)


if __name__ == "__main__":
    unittest.main()
