"""Thin Bifrost MCP HTTP client for Cursor lifecycle hooks (no secrets logged)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

GATEWAY_URL = os.environ.get("AGENTCORE_GATEWAY_MCP_URL", "http://127.0.0.1:8080/mcp")


def read_user_env(name: str) -> str:
    val = os.environ.get(name) or ""
    if val:
        return val
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                val, _ = winreg.QueryValueEx(key, name)
                return str(val or "")
        except OSError:
            return ""
    return ""


class GatewayClient:
    def __init__(self, timeout: float = 90.0) -> None:
        self.vk = read_user_env("BIFROST_MCP_VIRTUAL_KEY")
        if not self.vk:
            raise RuntimeError("BIFROST_MCP_VIRTUAL_KEY missing from process/User env")
        self.timeout = timeout
        self.session: str | None = None
        self._id = 0

    def _post(self, payload: dict[str, Any]) -> Any:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.vk}",
        }
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(
            GATEWAY_URL, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            hdrs = {k.lower(): v for k, v in exc.headers.items()}
        if hdrs.get("mcp-session-id"):
            self.session = hdrs["mcp-session-id"]
        if raw.startswith("event:") or "data:" in raw[:80]:
            data_lines = [
                line[5:].strip()
                for line in raw.splitlines()
                if line.startswith("data:")
            ]
            raw = data_lines[-1] if data_lines else raw
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"gateway non-JSON response: {raw[:200]}") from exc
        if isinstance(parsed, dict) and parsed.get("error"):
            raise RuntimeError(f"gateway error: {parsed['error']}")
        return parsed

    def initialize(self) -> None:
        self._id += 1
        self._post(
            {
                "jsonrpc": "2.0",
                "id": self._id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "agentcore-cursor-bootstrap", "version": "1.0.0"},
                },
            }
        )
        # notifications/initialized (no id)
        body = json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.vk}",
        }
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(
            GATEWAY_URL, data=body, headers=headers, method="POST"
        )
        try:
            urllib.request.urlopen(req, timeout=self.timeout).read()
        except Exception:  # noqa: BLE001
            pass

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if self.session is None:
            self.initialize()
        self._id += 1
        parsed = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        result = parsed.get("result") if isinstance(parsed, dict) else parsed
        if isinstance(result, dict) and "content" in result:
            texts = [
                block.get("text", "")
                for block in result.get("content", [])
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            joined = "\n".join(t for t in texts if t)
            if joined:
                try:
                    return json.loads(joined)
                except json.JSONDecodeError:
                    return {"ok": True, "text": joined}
        return result
