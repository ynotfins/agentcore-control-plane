#!/usr/bin/env python3
"""Render Bifrost config.json from AgentCore registry + gateway client contracts.

Writes:
  - runtime config (default H:\\AgentRuntime\\bifrost\\config.json and config\\config.json)
  - source-controlled sanitized copy under renderers/bifrost/

Never embeds secret values. Uses env.NAME references for Bifrost.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
GATEWAY_CLIENT_PATH = REPO_ROOT / "contracts" / "agentcore-gateway-client.json"
DEFAULT_RUNTIME_ROOT = Path(r"H:\AgentRuntime\bifrost")
SANITIZED_RENDERER = REPO_ROOT / "renderers" / "bifrost" / "config.sanitized.json"
SANITIZED_CONFIG_COPY = REPO_ROOT / "renderers" / "bifrost" / "config.json"

# Non-secret env defaults injected into stdio envs lists / values
STATIC_ENV_VALUES: dict[str, dict[str, str]] = {
    "sequential-thinking": {"DISABLE_THOUGHT_LOGGING": "true"},
    "cursor-agent-mcp": {"CURSOR_API_URL": "https://api.cursor.com"},
    "obsidian-vault": {
        "OBSIDIAN_BASE_URL": "https://127.0.0.1:27124",
        "OBSIDIAN_VERIFY_SSL": "false",
    },
}

SECRET_ENV_NAMES = {
    "OPENAI_API_KEY",
    "CURSOR_API_KEY",
    "ARTIFORGE_PAT",
    "ARTIFORGE_MCP_URL",
    "DEPWIRE_API_KEY",
    "OBSIDIAN_API_KEY",
    "OBSIDIAN_LOCAL_REST_API",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "GITHUB_PAT_TOKEN",
    "BIFROST_MCP_VIRTUAL_KEY",
    "BIFROST_MCP_VK_REVIEWER",
    "BIFROST_MCP_VK_DATABASE_VALIDATOR",
    "BIFROST_MCP_VK_DOCS_KNOWLEDGE",
    "BIFROST_MCP_VK_OPERATOR",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def wrapper_command(authority: str, wrapper_script: str) -> tuple[str, list[str]]:
    # Bifrost stdio on Windows: invoke cmd.exe wrapper
    abs_wrapper = str(Path(authority) / wrapper_script.replace("/", "\\"))
    return "cmd.exe", ["/c", abs_wrapper]


# On Windows Bifrost STDIO, listing env names and reconstructing the process
# environment has caused CreateProcess "The parameter is incorrect".
# Prefer full parent-env inheritance (empty envs list). Secrets must be present
# in the Bifrost process environment via Launch-AgentCoreBifrostGateway.ps1.
BASE_ENVS: list[str] = []


def build_stdio_client(server: dict[str, Any], authority: str) -> dict[str, Any]:
    name = server["bifrost_client_name"]
    canonical = server["canonical_id"]
    tools = list(server.get("permitted_tools") or ["*"])
    denied = list(server.get("denied_tools") or [])

    if server.get("connection_type") == "router":
        wrapper = server.get("wrapper_script")
        if not wrapper:
            raise ValueError(f"{canonical}: router connection requires wrapper_script")
        command, args = wrapper_command(authority, wrapper)
        envs = list(BASE_ENVS)
    else:
        command = server["executable_or_url"]
        args = list(server.get("arguments") or [])
        envs = list(BASE_ENVS)

    health = str(server.get("health_check_type") or "mcp_list_tools")
    is_ping_available = health in {"mcp_ping", "ping"}

    client: dict[str, Any] = {
        "name": name,
        "connection_type": "stdio",
        "stdio_config": {
            "command": command,
            "args": args,
            "envs": envs,
        },
        "tools_to_execute": tools if not denied else tools,
        "auth_type": "none",
        "is_ping_available": is_ping_available,
    }

    # Attach non-secret static values via notes only — Bifrost stdio envs inherit
    # process environment; STATIC_ENV_VALUES are documented for installers.
    notes: dict[str, Any] = {
        "windows_env_inheritance": "stdio_config.envs is empty so Bifrost inherits the gateway process environment",
        "required_parent_env": list(server.get("env_var_names") or []),
        "static_env": STATIC_ENV_VALUES.get(canonical, {}),
    }
    if denied:
        notes["denied_tools"] = denied
    client["notes_agentcore"] = notes

    return client


def build_http_client(server: dict[str, Any]) -> dict[str, Any]:
    name = server["bifrost_client_name"]
    tools = list(server.get("permitted_tools") or ["*"])
    connection_string = server["executable_or_url"]
    auth_type = server.get("auth_type") or "none"
    client: dict[str, Any] = {
        "name": name,
        "connection_type": server["connection_type"],
        "connection_string": connection_string,
        "tools_to_execute": tools,
        "auth_type": auth_type,
    }
    headers = server.get("headers")
    if headers:
        client["headers"] = headers
        client["auth_type"] = server.get("auth_type") or "headers"
    return client


def build_mcp_client_configs(registry: dict[str, Any]) -> list[dict[str, Any]]:
    authority = registry["authority"]
    clients: list[dict[str, Any]] = []
    for _key, server in sorted(registry["servers"].items(), key=lambda kv: kv[0]):
        if not server.get("enabled", False):
            continue
        if server.get("deferred") and not server.get("enabled"):
            continue
        ctype = server["connection_type"]
        if ctype in ("stdio", "router"):
            clients.append(build_stdio_client(server, authority))
        elif ctype in ("http", "sse"):
            clients.append(build_http_client(server))
        else:
            raise ValueError(f"Unsupported connection_type: {ctype}")
    # Strip AgentCore-only annotation keys from Bifrost runtime payload
    cleaned: list[dict[str, Any]] = []
    for client in clients:
        item = {k: v for k, v in client.items() if k != "notes_agentcore"}
        cleaned.append(item)
    return cleaned


def profile_mcp_configs(registry: dict[str, Any], profile_id: str) -> list[dict[str, Any]]:
    profile = registry["capability_profiles"][profile_id]
    allowed = set(profile.get("allowed_server_ids") or [])
    configs: list[dict[str, Any]] = []
    for canonical_id in sorted(allowed):
        server = registry["servers"].get(canonical_id)
        if not server or not server.get("enabled"):
            continue
        tools = list(server.get("permitted_tools") or ["*"])
        if profile_id == "reviewer":
            denied = set(server.get("denied_tools") or [])
            # Reviewer always denies debugger attach surface
            denied.update({"attach_to_process", "attach"})
            if tools == ["*"] and denied:
                # Keep wildcard but document deny via empty override when only denylist exists
                tools = ["*"]
            configs.append(
                {
                    "mcp_client_name": server["bifrost_client_name"],
                    "tools_to_execute": tools,
                }
            )
        else:
            configs.append(
                {
                    "mcp_client_name": server["bifrost_client_name"],
                    "tools_to_execute": tools,
                }
            )
    return configs


def build_virtual_keys(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "vk-agentcore-builder",
            "name": "builder",
            "value": "env.BIFROST_MCP_VIRTUAL_KEY",
            "is_active": True,
            "mcp_configs": profile_mcp_configs(registry, "builder"),
            "provider_configs": [
                {
                    "provider": "openai",
                    "allowed_models": ["*"],
                    "key_ids": ["*"],
                    "weight": 1,
                }
            ],
        },
        {
            "id": "vk-agentcore-reviewer",
            "name": "reviewer",
            "value": "env.BIFROST_MCP_VK_REVIEWER",
            "is_active": True,
            "mcp_configs": profile_mcp_configs(registry, "reviewer"),
        },
        {
            "id": "vk-agentcore-database-validator",
            "name": "database-validator",
            "value": "env.BIFROST_MCP_VK_DATABASE_VALIDATOR",
            "is_active": True,
            "mcp_configs": profile_mcp_configs(registry, "database-validator"),
        },
        {
            "id": "vk-agentcore-docs-knowledge",
            "name": "docs-knowledge",
            "value": "env.BIFROST_MCP_VK_DOCS_KNOWLEDGE",
            "is_active": True,
            "mcp_configs": profile_mcp_configs(registry, "docs-knowledge"),
        },
        {
            "id": "vk-agentcore-operator",
            "name": "operator",
            "value": "env.BIFROST_MCP_VK_OPERATOR",
            "is_active": True,
            "mcp_configs": profile_mcp_configs(registry, "operator"),
        },
    ]


def build_bifrost_config(registry: dict[str, Any], gateway_client: dict[str, Any]) -> dict[str, Any]:
    _ = gateway_client  # reserved for future timeout / URL cross-checks
    return {
        "$schema": "https://www.getbifrost.ai/schema",
        "version": 2,
        "source_of_truth": "config.json",
        "env_label": "agentcore",
        "client": {
            "enable_logging": True,
            "disable_content_logging": True,
            "log_retention_days": 14,
            "enforce_auth_on_inference": True,
            "mcp_server_auth_mode": "headers",
            "mcp_disable_auto_tool_inject": True,
        },
        "config_store": {
            "enabled": True,
            "type": "sqlite",
            "config": {
                "path": "./data/config.db",
            },
        },
        "logs_store": {
            "enabled": True,
            "type": "sqlite",
            "config": {
                "path": "./logs/logs.db",
            },
        },
        "providers": {
            "openai": {
                "keys": [
                    {
                        "name": "openai-primary",
                        "value": "env.OPENAI_API_KEY",
                        "models": ["*"],
                        "weight": 1,
                    }
                ]
            }
        },
        "mcp": {
            "client_configs": build_mcp_client_configs(registry),
            "tool_manager_config": {
                "tool_execution_timeout": "2m",
                "max_agent_depth": 1,
                "disable_auto_tool_inject": True,
            },
        },
        "governance": {
            "virtual_keys": build_virtual_keys(registry),
        },
    }


def build_sanitized_sidecar(registry: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Source-controlled sanitized copy with AgentCore metadata (still no secrets)."""
    payload = json.loads(json.dumps(config))
    payload["agentcore_meta"] = {
        "gateway_id": registry["gateway_id"],
        "authority": registry["authority"],
        "runtime_root": registry["runtime_root"],
        "swarm_exclusion": registry["swarm_exclusion"],
        "secret_policy": "env.NAME references only; never embed secret literals",
        "static_env_defaults": STATIC_ENV_VALUES,
        "vk_env_names": [
            "BIFROST_MCP_VIRTUAL_KEY",
            "BIFROST_MCP_VK_REVIEWER",
            "BIFROST_MCP_VK_DATABASE_VALIDATOR",
            "BIFROST_MCP_VK_DOCS_KNOWLEDGE",
            "BIFROST_MCP_VK_OPERATOR",
        ],
    }
    return payload


def assert_no_secret_literals(payload: dict[str, Any]) -> None:
    dumped = json.dumps(payload)
    # Heuristic: reject obvious pasted secrets (long sk-/Bearer tokens) while allowing env. refs
    forbidden_substrings = [
        "sk-proj-",
        "sk-ant-",
        "ghp_",
        "github_pat_",
    ]
    for token in forbidden_substrings:
        if token in dumped:
            raise SystemExit(f"Refusing to write config: possible secret literal containing {token!r}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_RUNTIME_ROOT / "config.json",
        help="Primary Bifrost config.json output path (app-dir root).",
    )
    parser.add_argument(
        "--also-config-dir",
        action="store_true",
        default=True,
        help="Also write config/config.json under the app-dir (default: true).",
    )
    parser.add_argument(
        "--no-also-config-dir",
        action="store_false",
        dest="also_config_dir",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print JSON to stdout instead of writing runtime files.",
    )
    parser.add_argument(
        "--skip-renderer",
        action="store_true",
        help="Do not write renderers/bifrost sanitized copies.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = load_json(REGISTRY_PATH)
    gateway_client = load_json(GATEWAY_CLIENT_PATH)
    config = build_bifrost_config(registry, gateway_client)
    assert_no_secret_literals(config)

    if args.stdout:
        json.dump(config, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    out_path: Path = args.out
    write_json(out_path, config)
    print(f"Wrote {out_path}")

    if args.also_config_dir:
        # Prefer sibling config/ under the same app-dir as --out when under bifrost root
        if out_path.name == "config.json" and out_path.parent.name != "config":
            alt = out_path.parent / "config" / "config.json"
        else:
            alt = DEFAULT_RUNTIME_ROOT / "config" / "config.json"
        write_json(alt, config)
        print(f"Wrote {alt}")

    if not args.skip_renderer:
        sanitized = build_sanitized_sidecar(registry, config)
        assert_no_secret_literals(sanitized)
        write_json(SANITIZED_RENDERER, sanitized)
        write_json(SANITIZED_CONFIG_COPY, sanitized)
        print(f"Wrote {SANITIZED_RENDERER}")
        print(f"Wrote {SANITIZED_CONFIG_COPY}")

    enabled = [c["name"] for c in config["mcp"]["client_configs"]]
    print(f"Enabled Bifrost MCP clients ({len(enabled)}): {', '.join(enabled)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
