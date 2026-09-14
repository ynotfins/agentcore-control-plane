r"""Host-owned signer/client for Trust Class A Devin memory calls.

Reuses the Cursor DeviceIdentityManager enrollment (same device.json / keyring).
Does not write private keys or BIFROST_MCP_VIRTUAL_KEY into Devin MCP JSON.
Devin itself stays headerless on http://127.0.0.1:18082/mcp.

Invoke from the scripts directory:

    python -m agentcore_devin.signed_memory sign --tool session_open --project-key nfa-platform --project-root D:\agentcore-worktrees\nfa-platform\goal-staging-001

Or from the repo root:

    python scripts/devin_signed_memory.py sign --tool session_open --project-key nfa-platform --project-root D:\agentcore-worktrees\nfa-platform\goal-staging-001
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
MEMORY_ROOT = SCRIPTS_ROOT / "agentcore_memory"
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))

from agentcore_project_boundary import require_enrolled_path

CLIENT_KEY = "devin"
DEFAULT_AGENT_KEY = "devin-builder"
DEVIN_COMPAT_GATEWAY_URL = "http://127.0.0.1:18082/mcp"
HOST_DIRECT_GATEWAY_URL = "http://127.0.0.1:8080/mcp"
MEMORY_TOOL_PREFIXES = ("agentcore_memory-", "agentcore-memory-")
BARE_MEMORY_TOOLS = frozenset(
    {
        "session_open",
        "session_close",
        "startup_context",
        "retrieve_context",
        "expand_source",
        "docs_search",
        "append_event",
        "propose_fact",
        "build_handoff",
        "memory_status",
    }
)


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


def device_identity_manager():
    try:
        from agentcore_context_engine.config import EnginePaths
        from agentcore_context_engine.security import (
            DeviceIdentityManager,
            KeyringCredentialStore,
        )
    except ImportError as exc:
        raise RuntimeError(
            "agentcore-context-engine[security] is required for signed memory calls"
        ) from exc
    paths = EnginePaths.discover()
    return DeviceIdentityManager(
        paths.data / "device.json",
        KeyringCredentialStore(),
    )


def bare_memory_tool(name: str):
    for prefix in MEMORY_TOOL_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix) :]
    if name in BARE_MEMORY_TOOLS:
        return name
    return None


def gateway_tool_name(name: str) -> str:
    bare = bare_memory_tool(name)
    if bare is None:
        raise ValueError("unsupported_memory_tool:" + name)
    return "agentcore_memory-" + bare


def is_compat_gateway_url(url: str) -> bool:
    return "://127.0.0.1:18082" in url or "://localhost:18082" in url


def require_localhost_gateway(url: str) -> str:
    if not (url.startswith("http://127.0.0.1") or url.startswith("http://localhost")):
        raise RuntimeError("gateway URL must be localhost")
    return url


def sign_memory_arguments(name: str, arguments: dict, identity_manager=None) -> dict:
    signed = dict(arguments)
    bare_tool = bare_memory_tool(name)
    if not bare_tool:
        raise ValueError("unsupported_memory_tool:" + name)
    if bare_tool == "memory_status":
        return signed
    identity = identity_manager or device_identity_manager()
    enrollment = identity.initialize()
    if bare_tool == "session_open":
        signed.setdefault("device_id", enrollment.device_id)
        signed.setdefault("client_key", CLIENT_KEY)
        signed.setdefault("agent_key", DEFAULT_AGENT_KEY)
    assertion = identity.sign_tool_call(
        target_tool=bare_tool,
        arguments=signed,
        project_key=(str(signed["project_key"]) if signed.get("project_key") else None),
        session_id=(str(signed["session_id"]) if signed.get("session_id") else None),
    )
    signed["device_assertion"] = assertion.as_dict()
    return signed


def default_session_open_arguments(project_key: str, project_root: str, extra=None) -> dict:
    enrolled = require_enrolled_path(project_root)
    if enrolled.get("project_key") != project_key:
        raise ValueError("project_identity_mismatch")
    args = {
        "project_key": project_key,
        "project_name": project_key,
        "project_root": project_root,
        "canonical_repo_path": project_root,
        "worktree_path": project_root,
        "repo_key": project_key,
        "client_key": CLIENT_KEY,
        "agent_key": DEFAULT_AGENT_KEY,
        "context_profile": "standard-context",
    }
    if extra:
        args.update({key: value for key, value in extra.items() if value is not None})
    return args


class HostSignedMemoryClient:
    """Host-owned signer and optional host-side memory caller.

    Devin MCP JSON stays on :18082 with no Authorization header.
    Host call uses in-process agentcore-memory or the header-capable :8080
    route with a User-scope virtual key that is never written to disk.
    """

    def __init__(self, timeout: float = 90.0, identity_manager=None) -> None:
        self.timeout = timeout
        self._identity_manager = identity_manager
        self.session = None
        self._id = 0

    def sign(self, name: str, arguments: dict) -> dict:
        return sign_memory_arguments(
            name, arguments, identity_manager=self._identity_manager
        )

    def call_inprocess(self, name: str, arguments: dict):
        import server as memory_server

        signed = self.sign(name, arguments)
        return memory_server.call_tool(bare_memory_tool(name) or name, signed)

    def call_gateway(self, name: str, arguments: dict, url: str = HOST_DIRECT_GATEWAY_URL):
        target = require_localhost_gateway(url)
        if self.session is None and not is_compat_gateway_url(target):
            self.initialize(url=target)
        signed = self.sign(name, arguments)
        self._id += 1
        parsed = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._id,
                "method": "tools/call",
                "params": {"name": gateway_tool_name(name), "arguments": signed},
            },
            url=target,
        )
        return parse_tool_result(parsed)

    def initialize(self, url: str = HOST_DIRECT_GATEWAY_URL) -> None:
        target = require_localhost_gateway(url)
        self._id += 1
        self._post(
            {
                "jsonrpc": "2.0",
                "id": self._id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "agentcore-devin-host-signer", "version": "1.0.0"},
                },
            },
            url=target,
        )
        body = json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        ).encode("utf-8")
        req = urllib.request.Request(
            target, data=body, headers=self._headers(url=target), method="POST"
        )
        try:
            urllib.request.urlopen(req, timeout=self.timeout).read()
        except Exception:
            pass

    def _headers(self, url: str) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if is_compat_gateway_url(url):
            if self.session:
                headers["Mcp-Session-Id"] = self.session
            return headers
        vk = read_user_env("BIFROST_MCP_VIRTUAL_KEY")
        if not vk:
            raise RuntimeError("BIFROST_MCP_VIRTUAL_KEY missing from process/User env")
        headers["Authorization"] = "Bearer " + vk
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        return headers

    def _post(self, payload: dict, url: str):
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers=self._headers(url=url), method="POST"
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
            raise RuntimeError("gateway non-JSON response: " + raw[:200]) from exc
        if isinstance(parsed, dict) and parsed.get("error"):
            raise RuntimeError("gateway error: " + str(parsed["error"]))
        return parsed


def parse_tool_result(parsed):
    result = parsed.get("result") if isinstance(parsed, dict) else parsed
    if isinstance(result, dict) and "content" in result:
        texts = [
            block.get("text", "")
            for block in result.get("content", [])
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        joined = "\n".join(text for text in texts if text)
        if joined:
            try:
                return json.loads(joined)
            except json.JSONDecodeError:
                if joined.lstrip().lower().startswith("tool execution failed:"):
                    return {"ok": False, "error": "gateway_tool_error", "detail": joined}
                return {"ok": False, "error": "unstructured_gateway_result", "detail": joined}
    return result


def inspect_devin_mcp_config(path=None) -> dict:
    config_path = Path(
        path
        or os.environ.get(
            "AGENTCORE_DEVIN_MCP_CONFIG",
            r"C:\Users\ynotf\AppData\Roaming\devin\mcp_config.json",
        )
    )
    if not config_path.is_file():
        return {"ok": False, "error": "devin_mcp_config_missing", "path_exists": False}
    raw = config_path.read_text(encoding="utf-8")
    lowered = raw.lower()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "error": "devin_mcp_config_invalid_json"}
    urls = []
    has_authorization = False
    has_vk_literal = "bifrost_mcp_virtual_key" in lowered or "bearer " in lowered

    def walk(node) -> None:
        nonlocal has_authorization
        if isinstance(node, dict):
            for key, value in node.items():
                key_l = str(key).lower()
                if key_l == "authorization":
                    has_authorization = True
                if key_l == "headers" and isinstance(value, dict):
                    if any(str(item).lower() == "authorization" for item in value):
                        has_authorization = True
                if key_l in {"url", "serverurl", "href"} and isinstance(value, str):
                    urls.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return {
        "ok": True,
        "path_exists": True,
        "urls": urls,
        "uses_compat_18082": any(is_compat_gateway_url(url) for url in urls),
        "has_authorization_header": has_authorization,
        "has_vk_literal": has_vk_literal,
    }


def load_extra_args(args: argparse.Namespace) -> dict:
    extra = {}
    if args.args_json:
        loaded = json.loads(args.args_json)
        if not isinstance(loaded, dict):
            raise ValueError("args_json_must_be_object")
        extra.update(loaded)
    if args.args_file:
        loaded = json.loads(Path(args.args_file).read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("args_file_must_be_object")
        extra.update(loaded)
    for field in (
        "session_id",
        "session_key",
        "branch_name",
        "head_commit",
        "milestone",
        "agent_key",
        "client_key",
    ):
        value = getattr(args, field, None)
        if value:
            extra[field] = value
    return extra


def build_arguments(args: argparse.Namespace) -> dict:
    extra = load_extra_args(args)
    if bare_memory_tool(args.tool) == "session_open" or args.tool.endswith("session_open"):
        return default_session_open_arguments(
            project_key=args.project_key,
            project_root=args.project_root,
            extra=extra,
        )
    built = {"project_key": args.project_key, "project_root": args.project_root}
    built.update(extra)
    return built


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Host-owned Devin signed-memory helper. Never writes secrets to Devin MCP JSON."
    )
    parser.add_argument("action", choices=("sign", "call"))
    parser.add_argument("--tool", required=True)
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--args-json")
    parser.add_argument("--args-file")
    parser.add_argument("--session-id")
    parser.add_argument("--session-key")
    parser.add_argument("--branch-name")
    parser.add_argument("--head-commit")
    parser.add_argument("--milestone")
    parser.add_argument("--client-key", default=CLIENT_KEY)
    parser.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    parser.add_argument("--via-gateway", action="store_true")
    parser.add_argument("--gateway-url", default=HOST_DIRECT_GATEWAY_URL)
    parsed = parser.parse_args(argv)
    arguments = build_arguments(parsed)
    client = HostSignedMemoryClient()
    if parsed.action == "sign":
        print(json.dumps(client.sign(parsed.tool, arguments), indent=2, sort_keys=True))
        return 0
    if parsed.via_gateway:
        if is_compat_gateway_url(parsed.gateway_url):
            raise SystemExit(
                "host call must not use :18082 with a helper-owned bearer"
            )
        result = client.call_gateway(parsed.tool, arguments, url=parsed.gateway_url)
    else:
        result = client.call_inprocess(parsed.tool, arguments)
    print(json.dumps(result, indent=2, default=str))
    if isinstance(result, dict) and result.get("ok", True):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
