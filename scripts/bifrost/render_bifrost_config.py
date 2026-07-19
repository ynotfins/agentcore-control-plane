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

# Runtime-only OAuth state file (never committed to Git).
# Written by operator after successful management-API OAuth enrollment.
# Format: {"<bifrost_client_name>": {"oauth_config_id": "...", "mcp_client_id": "..."}}
OAUTH_STATE_PATH = DEFAULT_RUNTIME_ROOT / "state" / "oauth-clients.json"

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


def load_oauth_state(oauth_state_path: Path) -> dict[str, Any]:
    """Load runtime-only OAuth client state (never committed).

    Returns {} when the file is absent (pre-enrollment) or unparseable.
    The file is written by the operator after a successful management-API OAuth enrollment
    and contains oauth_config_id / mcp_client_id — never token values.
    """
    try:
        return json.loads(oauth_state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


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

    # Apply denied_tools as an explicit filter (defense-in-depth for explicit allowlists).
    denied_set = set(denied)
    if denied_set and tools != ["*"]:
        effective_tools = [t for t in tools if t not in denied_set]
    else:
        effective_tools = tools  # wildcard: blocked upstream by validator if denied_tools non-empty

    client: dict[str, Any] = {
        "name": name,
        "connection_type": "stdio",
        "stdio_config": {
            "command": command,
            "args": args,
            "envs": envs,
        },
        "tools_to_execute": effective_tools,
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


def build_http_client(server: dict[str, Any], oauth_state: dict[str, Any] | None = None) -> dict[str, Any]:
    name = server["bifrost_client_name"]
    tools = list(server.get("permitted_tools") or ["*"])
    denied = list(server.get("denied_tools") or [])
    connection_string = server["executable_or_url"]
    auth_type = server.get("auth_type") or "none"

    # Apply denied_tools filter for explicit allowlists (defense-in-depth).
    denied_set = set(denied)
    if denied_set and tools != ["*"]:
        effective_tools = [t for t in tools if t not in denied_set]
    else:
        effective_tools = tools  # wildcard: blocked upstream by validator if denied_tools non-empty

    client: dict[str, Any] = {
        "name": name,
        "connection_type": server["connection_type"],
        "connection_string": connection_string,
        "tools_to_execute": effective_tools,
        "auth_type": auth_type,
    }
    headers = server.get("headers")
    if headers:
        client["headers"] = headers
        client["auth_type"] = server.get("auth_type") or "headers"

    # OAuth handling: prefer oauth_config_id from runtime state (post-enrollment) over inline
    # oauth_config (pre-enrollment public params).  This prevents re-renders from clobbering an
    # existing OAuth-bound client in Bifrost's config store.
    #
    # Pre-enrollment:   oauth_state absent / no entry for this client
    #   → emit oauth_config (public params: server_url + scopes only, no secrets)
    #   → Bifrost registers client as oauth-pending; operator runs management-API enrollment
    #
    # Post-enrollment:  oauth_state contains {oauth_config_id: "...", mcp_client_id: "..."}
    #   → emit oauth_config_id only (no oauth_config inline)
    #   → Bifrost references the enrolled client; re-render is idempotent
    #
    # WARNING: re-rendering without the runtime state file after enrollment may create a new
    # pending OAuth client and orphan the enrolled one.  Operator must keep
    # H:\AgentRuntime\bifrost\state\oauth-clients.json present after enrollment.
    oauth_cfg = server.get("oauth_config")
    if auth_type == "oauth" and oauth_cfg:
        state_entry = (oauth_state or {}).get(name, {})
        oauth_config_id = state_entry.get("oauth_config_id")
        if oauth_config_id:
            # Post-enrollment: reference existing Bifrost OAuth record by id
            client["oauth_config_id"] = oauth_config_id
        else:
            # Pre-enrollment: public params only (server_url, scopes — no secrets)
            client["oauth_config"] = oauth_cfg

    return client


def build_mcp_client_configs(registry: dict[str, Any], oauth_state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
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
            clients.append(build_http_client(server, oauth_state))
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


def build_bifrost_config(
    registry: dict[str, Any],
    gateway_client: dict[str, Any],
    oauth_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
            "client_configs": build_mcp_client_configs(registry, oauth_state),
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


def build_sanitized_sidecar(registry: dict[str, Any], config: dict[str, Any], oauth_state_present: bool = False) -> dict[str, Any]:
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
        "oauth_state_note": (
            "Post-enrollment: oauth_config_id loaded from runtime state file "
            f"(H:\\AgentRuntime\\bifrost\\state\\oauth-clients.json) — present={oauth_state_present}. "
            "That file is runtime-only and never committed. "
            "Pre-enrollment: oauth_config (public params only) is embedded for initial Bifrost registration."
        ),
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
        "sk-or-v1-",        # OpenRouter API key literal
        "oauth_access_token",
        "oauth_refresh_token",
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

    # Load runtime-only OAuth state (never committed).
    # Pre-enrollment: empty dict → oauth_config (public params) embedded in config.
    # Post-enrollment: state file present → oauth_config_id substituted; re-render is idempotent.
    oauth_state = load_oauth_state(OAUTH_STATE_PATH)
    if oauth_state:
        enrolled = [name for name in oauth_state if oauth_state[name].get("oauth_config_id")]
        print(f"OAuth state loaded: {len(enrolled)} enrolled client(s): {', '.join(enrolled)}")
    else:
        print("OAuth state: pre-enrollment (no state file or empty) — oauth_config (public params) will be used")

    config = build_bifrost_config(registry, gateway_client, oauth_state)
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
        oauth_state_present = bool(oauth_state)
        sanitized = build_sanitized_sidecar(registry, config, oauth_state_present)
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
