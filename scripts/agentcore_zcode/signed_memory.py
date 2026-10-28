r"""Host-owned signer/client for Trust Class A ZCode memory calls.

Mirrors scripts/agentcore_devin/signed_memory.py and reuses the same
Cursor DeviceIdentityManager enrollment (same device.json / keyring).
Does not write private keys or BIFROST_MCP_VIRTUAL_KEY into ZCode MCP JSON.
ZCode itself stays headerless on http://127.0.0.1:18082/mcp; this host helper
exists because the ZCode MCP client cannot mint device assertions in-process.

Invoke from the scripts directory (repo runtime venv):

    python -m agentcore_zcode.signed_memory call --tool session_open \
        --project-key zcode-workspace --project-root "I:\LocalApps\ZCode\workspace\default"

Or from the repo root:

    python -m agentcore_zcode.signed_memory sign --tool append_event ...
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from agentcore_devin import signed_memory as _devin
from agentcore_project_boundary import require_enrolled_path

CLIENT_KEY = "zcode"
DEFAULT_AGENT_KEY = "zcode-builder"
ZCODE_COMPAT_GATEWAY_URL = "http://127.0.0.1:18082/mcp"
HOST_DIRECT_GATEWAY_URL = _devin.HOST_DIRECT_GATEWAY_URL
MEMORY_TOOL_PREFIXES = _devin.MEMORY_TOOL_PREFIXES
BARE_MEMORY_TOOLS = _devin.BARE_MEMORY_TOOLS

bare_memory_tool = _devin.bare_memory_tool
gateway_tool_name = _devin.gateway_tool_name
device_identity_manager = _devin.device_identity_manager
parse_tool_result = _devin.parse_tool_result
is_compat_gateway_url = _devin.is_compat_gateway_url
read_user_env = _devin.read_user_env


def sign_memory_arguments(name: str, arguments: dict, identity_manager=None) -> dict:
    """Sign one agentcore-memory tool call with the zcode client identity."""
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
        "client_key": CLIENT_KEY,
        "agent_key": DEFAULT_AGENT_KEY,
        "context_profile": "standard-context",
    }
    if extra:
        args.update({key: value for key, value in extra.items() if value is not None})
    return args


class HostSignedZCodeMemoryClient(_devin.HostSignedMemoryClient):
    """ZCode variant: signs with client_key=zcode.

    ZCode MCP JSON stays on :18082 with no Authorization header. Host calls
    use the in-process memory server or the header-capable :8080 route with
    a User-scope virtual key that is never written to disk — same contract as
    the Devin host signer.
    """

    def sign(self, name: str, arguments: dict) -> dict:
        return sign_memory_arguments(
            name, arguments, identity_manager=self._identity_manager
        )


def inspect_zcode_mcp_config(path=None) -> dict:
    """Sanitized inspection of the live ZCode MCP config (no secrets copied)."""
    config_path = Path(
        path
        or os.environ.get(
            "AGENTCORE_ZCODE_MCP_CONFIG",
            r"C:\Users\ynotf\.zcode\cli\config.json",
        )
    )
    if not config_path.is_file():
        return {"ok": False, "error": "zcode_mcp_config_missing", "path_exists": False}
    raw = config_path.read_text(encoding="utf-8")
    lowered = raw.lower()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "error": "zcode_mcp_config_invalid_json"}
    servers = (data.get("mcp") or {}).get("servers") or {}
    gateway = servers.get("agentcore-gateway") or {}
    return {
        "ok": True,
        "path_exists": True,
        "gateway_url": gateway.get("url"),
        "gateway_enabled": gateway.get("enabled"),
        "uses_compat_18082": is_compat_gateway_url(str(gateway.get("url") or "")),
        "has_authorization_header": "authorization" in lowered and "bearer" in lowered,
        "has_vk_literal": "bifrost_mcp_virtual_key" in lowered,
        "server_names": sorted(servers.keys()),
    }


def load_extra_args(args: argparse.Namespace) -> dict:
    extra = {}
    if getattr(args, "args_json", None):
        loaded = json.loads(args.args_json)
        if not isinstance(loaded, dict):
            raise ValueError("args_json_must_be_object")
        extra.update(loaded)
    if getattr(args, "args_file", None):
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
        description=(
            "Host-owned ZCode signed-memory helper. Never writes secrets to ZCode MCP JSON."
        )
    )
    parser.add_argument("action", choices=("sign", "call", "inspect"))
    parser.add_argument("--tool")
    parser.add_argument("--project-key")
    parser.add_argument("--project-root")
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

    if parsed.action == "inspect":
        print(json.dumps(inspect_zcode_mcp_config(), indent=2, sort_keys=True))
        return 0

    if not parsed.tool:
        parser.error("--tool is required for sign/call")
    if not (parsed.project_key and parsed.project_root):
        parser.error("--project-key and --project-root are required for sign/call")

    arguments = build_arguments(parsed)
    client = HostSignedZCodeMemoryClient()
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

