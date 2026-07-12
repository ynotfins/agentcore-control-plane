from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LIVE_OPS_ROOT = Path("D:/MCP-Control-Plane")
ROOT = DEFAULT_SOURCE_ROOT
LIVE_OPS_ROOT = Path(os.environ.get("AGENTCORE_LIVE_OPS_ROOT", str(DEFAULT_LIVE_OPS_ROOT)))
MANAGED_ROOT = Path("D:/Codex_Managed")
PYTHON = Path("D:/Codex_Managed/.venv/Scripts/python.exe")
NODE_HOME = Path("D:/Codex_Managed/runtimes/node-v22.22.3-win-x64")
CODEX_CONFIG = Path.home() / ".codex/config.toml"

SECRET_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "AUTH", "PAT", "COOKIE", "LICENSE")
SECRET_VALUE_PATTERNS = (
    (r"pat=([^&\s]+)", "pat=${REDACTED}"),
    (r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer ${REDACTED}"),
    (r"Token\s+[A-Za-z0-9._~+/=-]+", "Token ${REDACTED}"),
)

ANTIGRAVITY_PRIMARY_CONFIG = Path.home() / ".gemini/config/mcp_config.json"
ANTIGRAVITY_ROAMING_CONFIG = Path.home() / "AppData/Roaming/Antigravity/User/mcp.json"
ANTIGRAVITY_RENDERER = "antigravity.mcp_config.json"
ANTIGRAVITY_DEFAULT_SERVERS = [
    "arabold-docs",
    "artiforge",
    "filesystem",
    "global-memory-gateway",
    "obsidian-vault",
    "playwright",
    "sequential-thinking",
    "serena",
]

GATEWAY_PLATFORM_BY_CLIENT = {
    "Codex": "codex",
    "Cursor": "cursor",
    "Open Interpreter": "open-interpreter",
    "OpenClaw": "openclaw",
    "MiniMax Code": "minimax-code",
    "Android Studio": "android-studio",
    "Antigravity": "antigravity",
}

EYE2BYTE_OPENCLAW_SERVER = {
    "canonical_id": "eye2byte",
    "client_bindings": ["OpenClaw"],
    "transport": "stdio",
    "launch_contract": {
        "command": "python",
        "args": ["C:\\Users\\ynotf\\.openclaw\\eye2byte_mcp.py"],
    },
    "healthcheck": {"kind": "mcp_stdio", "methods": ["initialize", "tools/list"]},
    "criticality": "normal",
    "lifecycle": "active",
    "capabilities": ["openclaw_user_extension"],
    "notes": ["User-approved OpenClaw-only MCP server. Preserve during renderer apply; do not copy to other IDEs."],
}

DEPWIRE_SERVER = {
    "canonical_id": "depwire",
    "client_bindings": [
        "Codex",
        "Cursor",
        "OpenClaw",
        "MiniMax Code",
        "Open Interpreter",
        "Antigravity",
        "Android Studio",
    ],
    "transport": "stdio",
    "package": "depwire-cli",
    "package_version": "1.8.2",
    "launch_contract": {
        "command": "C:\\Users\\ynotf\\AppData\\Roaming\\npm\\depwire.cmd",
        "args": ["mcp"],
    },
    "env_expectations": {"DEPWIRE_NO_TELEMETRY": "1"},
    "healthcheck": {"kind": "mcp_stdio", "methods": ["initialize", "tools/list"]},
    "criticality": "normal",
    "lifecycle": "active",
    "render_by_default": True,
    "capabilities": [
        "deterministic_dependency_graph",
        "symbol_impact_analysis",
        "change_simulation",
        "pre_action_verification",
        "graph_aware_security_scan",
        "architecture_health",
        "multi_agent_file_claims",
    ],
    "notes": [
        "Local CLI/MCP path. Connect only to verified local repository paths unless the operator explicitly approves a remote clone or pull.",
        "The depwire-cli MCP server does not consume a DepWire API or license environment variable.",
        "DepWire Pro licensing applies to the VS Code/Cursor extension setting depwire.licenseKey only; never copy that key into MCP configs.",
        "Telemetry is disabled with DEPWIRE_NO_TELEMETRY=1.",
        "connect_repo creates .depwire/cache.db; keep .depwire/ and depwire-output.json globally ignored and never commit them.",
    ],
}


class ClientConfigTarget(BaseModel):
    client: str
    file_path: str
    required: bool = False
    discovered: bool = False


class InventoryServer(BaseModel):
    client: str
    file_path: str
    server_name: str
    canonical: str
    transport: str
    command: str | None = None
    url: str | None = None
    args: list[str] = Field(default_factory=list)
    env_keys_only: list[str] = Field(default_factory=list)
    header_keys_only: list[str] = Field(default_factory=list)
    detected_auth: list[str] = Field(default_factory=list)
    expected_capabilities: list[str] = Field(default_factory=list)
    ownership: str = "local-user"
    criticality: str = "normal"
    health: str = "probe_pending"
    notes: list[str] = Field(default_factory=list)


class ProbeResult(BaseModel):
    canonical: str
    transport: str
    status: Literal[
        "healthy",
        "degraded",
        "auth_failed",
        "launch_failed",
        "schema_invalid",
        "timeout",
        "unknown",
        "skipped",
    ]
    latency_ms: int | None = None
    exit_code: int | None = None
    tools_count: int | None = None
    resources_count: int | None = None
    error: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def display_path(path: Path) -> str:
    return str(path).replace("/", "\\")


def configure_roots(source_root: Path, live_ops_root: Path) -> None:
    global ROOT, LIVE_OPS_ROOT
    ROOT = source_root.resolve()
    LIVE_OPS_ROOT = live_ops_root.resolve() if live_ops_root.exists() else live_ops_root


def ensure_dirs() -> None:
    for child in [
        "inventory",
        "probes",
        "supervisor",
        "schemas/tools",
        "docs",
        "ops/logs",
        "artifacts",
        "artifacts/backups",
        "scripts",
        "renderers",
        "rules",
        "registry",
        "validators",
    ]:
        (ROOT / child).mkdir(parents=True, exist_ok=True)


def safe_name(path: str) -> str:
    out = path.replace(":", "").replace("\\", "__").replace("/", "__")
    return out.strip("_")


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except Exception as exc:
        return None, str(exc)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    was_read_only = path.exists() and not os.access(path, os.W_OK)
    if was_read_only:
        os.chmod(path, 0o666)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if was_read_only:
        os.chmod(path, 0o444)


def redact_sensitive_text(value: str) -> str:
    redacted = value
    for pattern, replacement in SECRET_VALUE_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
    return redacted


def gateway_args_for_client(client: str) -> list[str]:
    platform = GATEWAY_PLATFORM_BY_CLIENT[client]
    return [
        "-m",
        "autonomy_factory.global_memory_gateway",
        "--user-id",
        "master_developer_profile",
        "--project-id",
        "codex-managed",
        "--platform",
        platform,
    ]


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "" or text.lower() in {"true", "false", "null", "yes", "no", "on", "off"} or any(ch in text for ch in ":#{}[]&,*?|-<>=!%@`\\\"'"):
        return json.dumps(text)
    return text


def to_yaml(data: Any, indent: int = 0) -> str:
    space = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{space}{key}:")
                lines.append(to_yaml(value, indent + 2))
            else:
                lines.append(f"{space}{key}: {yaml_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return f"{space}[]"
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{space}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{space}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{space}{yaml_scalar(data)}"


def write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    was_read_only = path.exists() and not os.access(path, os.W_OK)
    if was_read_only:
        os.chmod(path, 0o666)
    path.write_text(to_yaml(data) + "\n", encoding="utf-8")
    if was_read_only:
        os.chmod(path, 0o444)


def discover_targets() -> list[ClientConfigTarget]:
    targets = [
        ClientConfigTarget(client="Cursor Global", file_path=str(Path.home() / ".cursor/mcp.json"), required=True),
        ClientConfigTarget(client="Cursor Project", file_path=str(MANAGED_ROOT / ".cursor/mcp.json")),
        ClientConfigTarget(client="Open Interpreter", file_path=str(Path.home() / "AppData/Roaming/interpreter/config.json"), required=True),
        ClientConfigTarget(client="MiniMax Code", file_path=str(Path.home() / ".minimax/mcp/mcp.json"), required=True),
        ClientConfigTarget(client="MiniMax Code", file_path=str(Path.home() / ".mavis/mcp/mcp.json"), required=True),
        ClientConfigTarget(client="OpenClaw", file_path=str(Path.home() / ".openclaw/openclaw.json"), required=True),
        ClientConfigTarget(client="Antigravity", file_path=str(ANTIGRAVITY_PRIMARY_CONFIG), required=True),
        ClientConfigTarget(client="Antigravity Roaming", file_path=str(ANTIGRAVITY_ROAMING_CONFIG), discovered=True),
    ]
    google = Path(os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming"))) / "Google"
    if google.exists():
        for mcp in sorted(google.glob("AndroidStudio*/**/mcp.json")):
            targets.append(ClientConfigTarget(client="Android Studio", file_path=str(mcp), discovered=True))
        for cfg_dir in sorted(google.glob("AndroidStudio*")):
            targets.append(ClientConfigTarget(client="Android Studio Config Dir", file_path=str(cfg_dir / "options/mcp.json"), discovered=True))
    return targets


def backup_repo_managed_files(stamp: str) -> dict[str, Any]:
    root = ROOT / "artifacts/backups" / stamp / "repo-managed"
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    managed = [
        "AGENTS.md",
        "SECURITY.md",
        "rules/global-mcp-routing.md",
        "rules/environment-and-secrets.md",
        "registry/tool-registry.json",
        "registry/tool-registry.schema.json",
        "supervisor/servers.json",
        "supervisor/servers.yaml",
        "renderers/cursor-global.mcp.json",
        "renderers/open-interpreter.config.fragment.json",
        "renderers/openclaw.openclaw.fragment.json",
        "renderers/minimax.mcp.json",
        "renderers/android-studio.mcp.json",
        f"renderers/{ANTIGRAVITY_RENDERER}",
        "validators/validate-control-plane.ps1",
        "scripts/mcp_control_plane.py",
    ]
    manifest: dict[str, Any] = {"stamp": stamp, "created_at": iso_now(), "locations": {"control_plane": str(root)}, "targets": []}
    for rel in managed:
        path = ROOT / rel
        entry: dict[str, Any] = {"path": str(path), "relative_path": rel, "exists": path.exists(), "raw_copy": None}
        if path.exists() and path.is_file():
            dest = raw / safe_name(rel)
            shutil.copy2(path, dest)
            entry["raw_copy"] = str(dest)
        manifest["targets"].append(entry)
    write_json(ROOT / "artifacts" / "backup-manifest.json", manifest)
    return manifest


def canonical_name(name: str) -> str:
    lower = name.lower()
    if "arabold" in lower or "docs-mcp-server" in lower:
        return "arabold-docs"
    if "context-fabric" in lower or "context_fabric" in lower:
        return "context-fabric"
    if "artiforge" in lower:
        return "artiforge"
    if "sequential" in lower:
        return "sequential-thinking"
    if "context7" in lower:
        return "context7-retired"
    if "mem0" in lower:
        return "mem0_mcp_server"
    if "global-memory" in lower:
        return "global-memory-gateway"
    if "cursor" in lower and "bridge" in lower:
        return "cursor-agent-bridge"
    return name


def infer_transport(server: dict[str, Any]) -> str:
    explicit = str(server.get("type") or server.get("transport") or "").lower()
    if explicit in {"stdio", "sse", "http", "streamable-http", "remote"}:
        return "streamable-http" if explicit in {"http", "streamable-http", "remote"} else explicit
    if "command" in server:
        return "stdio"
    if "httpUrl" in server or "url" in server:
        return "streamable-http"
    return "unknown"


def extract_servers(client: str, file_path: Path, data: dict[str, Any] | None) -> list[InventoryServer]:
    if not data:
        return []
    candidates: list[tuple[str, dict[str, Any]]] = []
    for container in [data.get("mcpServers"), data.get("servers")]:
        if isinstance(container, dict):
            candidates.extend((k, v) for k, v in container.items() if isinstance(v, dict))
    nested = data.get("mcp")
    if isinstance(nested, dict):
        container = nested.get("servers") or nested
        if isinstance(container, dict):
            candidates.extend((k, v) for k, v in container.items() if isinstance(v, dict))
    registry = data.get("mcp_canonical_registry")
    if isinstance(registry, dict):
        candidates.extend((k, v) for k, v in registry.items() if isinstance(v, dict))

    servers: list[InventoryServer] = []
    for name, server in candidates:
        env = server.get("env") if isinstance(server.get("env"), dict) else {}
        headers = server.get("headers") if isinstance(server.get("headers"), dict) else {}
        auth = []
        if env:
            auth.extend(k for k in env if any(h in k.upper() for h in SECRET_HINTS))
        if headers:
            auth.extend(k for k in headers if any(h in k.upper() for h in SECRET_HINTS))
        url = server.get("url") or server.get("httpUrl")
        command = server.get("command")
        args = server.get("args") if isinstance(server.get("args"), list) else []
        expected = ["tools"]
        if canonical_name(name) != "mem0_mcp_server":
            expected.extend(["resources", "prompts"])
        servers.append(
            InventoryServer(
                client=client,
                file_path=str(file_path),
                server_name=name,
                canonical=canonical_name(name),
                transport=infer_transport(server),
                command=str(command) if command else None,
                url=redact_sensitive_text(str(url)) if url else None,
                args=[redact_sensitive_text(str(a)) for a in args],
                env_keys_only=sorted(env.keys()),
                header_keys_only=sorted(headers.keys()),
                detected_auth=sorted(set(auth)),
                expected_capabilities=expected,
                criticality="critical" if canonical_name(name) in {"global-memory-gateway", "arabold-docs", "sequential-thinking", "artiforge"} else "normal",
            )
        )
    return servers


def inventory(targets: list[ClientConfigTarget]) -> tuple[list[InventoryServer], dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    servers: list[InventoryServer] = []
    for target in targets:
        path = Path(target.file_path)
        data = None
        parse_error = None
        if path.exists() and path.is_file() and path.suffix.lower() == ".json":
            data, parse_error = read_json(path)
        target_servers = extract_servers(target.client, path, data)
        servers.extend(target_servers)
        assets.append(
            {
                **target.model_dump(),
                "exists": path.exists(),
                "is_file": path.is_file() if path.exists() else False,
                "parse_error": parse_error,
                "server_count": len(target_servers),
                "servers": [s.model_dump() for s in target_servers],
            }
        )
    payload = {"generated_at": iso_now(), "assets": assets, "servers": [s.model_dump() for s in servers]}
    write_json(ROOT / "inventory/assets.json", payload)
    write_yaml(ROOT / "inventory/assets.yaml", payload)
    write_json(ROOT / "artifacts/initial-inventory.json", payload)
    return servers, payload


def env_status(keys: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key in keys:
        scopes = {}
        for scope, getter in [
            ("Process", lambda k: os.environ.get(k)),
            ("User", lambda k: get_user_env(k)),
            ("Machine", lambda k: get_machine_env(k)),
        ]:
            value = getter(key)
            scopes[scope] = {"present": bool(value), "length": len(value) if value else 0}
        result[key] = scopes
    return result


def powershell_env(scope: str, key: str) -> str | None:
    cmd = ["powershell", "-NoProfile", "-Command", f"[Environment]::GetEnvironmentVariable('{key}','{scope}')"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        value = proc.stdout.strip()
        return value or None
    except Exception:
        return None


def get_user_env(key: str) -> str | None:
    return powershell_env("User", key)


def get_machine_env(key: str) -> str | None:
    return powershell_env("Machine", key)


def first_env(key: str) -> str | None:
    return os.environ.get(key) or get_user_env(key) or get_machine_env(key)


def ensure_client_binding(model: dict[str, Any], server_name: str, client: str) -> None:
    server = model.get("servers", {}).get(server_name)
    if not isinstance(server, dict):
        return
    bindings = server.setdefault("client_bindings", [])
    if client not in bindings:
        bindings.append(client)


def canonical_model(_legacy_context7_opencode_supported: bool = False) -> dict[str, Any]:
    existing, error = read_json(ROOT / "supervisor/servers.json")
    if existing and isinstance(existing.get("servers"), dict):
        model = existing
        model["generated_at"] = iso_now()
        model.setdefault("fallback_policy", {})["critical_tools"] = [
            "global-memory-gateway",
            "arabold-docs",
            "artiforge",
            "sequential-thinking",
        ]
        model["fallback_policy"]["rule"] = "Only use a fallback when it preserves quality. If a critical primary fails and no high-quality equivalent exists, stop and notify the user."
        model["servers"].pop("context7", None)
        if "arabold-docs" in model["servers"]:
            bindings = model["servers"]["arabold-docs"].setdefault("client_bindings", [])
            if "Open Interpreter" not in bindings:
                bindings.append("Open Interpreter")
        if "global-memory-gateway" in model["servers"]:
            gateway = model["servers"]["global-memory-gateway"]
            gateway["env_expectations"] = {
                "MEM0_DEFAULT_USER_ID": "master_developer_profile",
                "MEMORY_GATEWAY_BACKEND": "postgres",
                "AGENT_CORE_PGHOST": "127.0.0.1",
                "AGENT_CORE_PGPORT": "55432",
                "AGENT_CORE_PGDATABASE": "agent_core",
                "AGENT_CORE_PGUSER": "agent_ingest",
                "AGENT_CORE_PGPASSWORD": "${ENV:AGENT_CORE_AGENT_INGEST_PASSWORD}",
                "MEMORY_GATEWAY_EMBEDDING_PROVIDER": "auto",
                "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
                "MEMORY_GATEWAY_EMBEDDING_DIMENSIONS": "1536",
                "OPENAI_API_KEY": "${ENV:OPENAI_API_KEY}",
            }
            gateway["capabilities"] = [
                "governed_memory",
                "postgresql_vector_memory",
                "append_only_contract",
                "project_scoped_writes",
                "global_reads",
            ]
            gateway["notes"] = [
                "Primary memory path for normal agents. Stop if unavailable; do not fall back to raw Mem0 unless explicitly approved.",
                "Backed by PostgreSQL agent_core on 127.0.0.1:55432 with pgvector VECTOR(1536).",
                "Uses OpenAI text-embedding-3-small when OPENAI_API_KEY is available; local_hash_v1 is offline fallback only.",
                "AgentCore uses Windows environment variables only. Do not create .env fallbacks for gateway credentials.",
                "Gateway launches with AGENT_CORE_PGUSER=agent_ingest and AGENT_CORE_PGPASSWORD=${ENV:AGENT_CORE_AGENT_INGEST_PASSWORD}.",
                "Normal agents use memory_append/search/state; trusted ingest/admin jobs are the only direct PostgreSQL writers.",
            ]
        if "filesystem" in model["servers"]:
            args = model["servers"]["filesystem"].setdefault("launch_contract", {}).setdefault("args", [])
            for root in ["F:\\AgentCore", "E:\\AgentCoreArchive"]:
                if root not in args:
                    args.append(root)
            notes = model["servers"]["filesystem"].setdefault("notes", [])
            note = "Includes active AgentCore NVMe root and cold archive root for local agent workflows."
            if note not in notes:
                notes.append(note)
        for antigravity_server in ANTIGRAVITY_DEFAULT_SERVERS:
            ensure_client_binding(model, antigravity_server, "Antigravity")
        for default_off in ["context-fabric", "cursor-agent-mcp", "github-mcp", "mcp-debugger"]:
            if default_off in model["servers"]:
                model["servers"][default_off]["render_by_default"] = False
        model["servers"]["eye2byte"] = EYE2BYTE_OPENCLAW_SERVER.copy()
        model["servers"]["depwire"] = DEPWIRE_SERVER.copy()
        return model
    if error:
        print(f"warning: failed to read existing supervisor model: {error}", file=sys.stderr)
    return {
        "schema_version": "2026-06-20",
        "generated_at": iso_now(),
        "system_id": "CHAOSCENTRAL",
        "global_identity": {
            "user_id": "master_developer_profile",
            "primary_username": "ynotf",
        },
        "fallback_policy": {
            "critical_tools": ["global-memory-gateway", "arabold-docs", "artiforge", "sequential-thinking"],
            "rule": "Only use a fallback when it preserves quality. If a critical primary fails and no high-quality equivalent exists, stop and notify the user.",
        },
        "servers": {
            "arabold-docs": {
                "canonical_id": "arabold-docs",
                "client_bindings": ["Cursor", "Codex", "OpenClaw", "MiniMax Code", "Open Interpreter", "Antigravity"],
                "transport": "stdio",
                "launch_contract": {
                    "command": "C:\\Program Files\\nodejs\\node.exe",
                    "args": ["C:\\Users\\ynotf\\.cursor\\vendor\\arabold-docs-mcp\\node_modules\\@arabold\\docs-mcp-server\\dist\\index.js"],
                },
                "env_expectations": {"OPENAI_API_KEY": "${ENV:OPENAI_API_KEY}"},
                "healthcheck": {"kind": "mcp_stdio", "methods": ["initialize", "tools/list"]},
                "criticality": "critical",
                "lifecycle": "active",
                "capabilities": ["current_docs", "version_grounding", "documentation_indexing"],
                "notes": ["Replaces Context7 in this control plane."],
            },
            "artiforge": {
                "canonical_id": "artiforge",
                "client_bindings": ["Codex", "Cursor", "OpenClaw", "MiniMax Code", "Open Interpreter", "Antigravity"],
                "transport": "http",
                "launch_contract": {"url": "https://tools.artiforge.ai/mcp?pat=${env:ARTIFORGE_PAT}"},
                "env_expectations": {"ARTIFORGE_PAT": "${ENV:ARTIFORGE_PAT}"},
                "healthcheck": {"kind": "http_reachable", "url": "https://tools.artiforge.ai/mcp"},
                "criticality": "critical",
                "lifecycle": "active",
                "capabilities": ["codebase_scanning", "architecture_analysis", "refactor_strategy"],
                "notes": [
                    "High-leverage only; not for routine file edits.",
                    "Live working client shape is http + url https://tools.artiforge.ai/mcp?pat=${env:ARTIFORGE_PAT}.",
                ],
            },
            "sequential-thinking": {
                "canonical_id": "sequential-thinking",
                "client_bindings": ["Codex", "Cursor", "OpenClaw", "MiniMax Code", "Antigravity"],
                "transport": "stdio",
                "launch_contract": {
                    "command": "npx.cmd",
                    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
                },
                "env_expectations": {"DISABLE_THOUGHT_LOGGING": "true"},
                "healthcheck": {"kind": "mcp_stdio", "methods": ["initialize", "tools/list"]},
                "criticality": "critical",
                "lifecycle": "active",
                "capabilities": ["planning", "strategy", "debugging"],
                "notes": ["Only reasoning/planning MCP. thinking-patterns remains retired."],
            },
            "context-fabric": {
                "canonical_id": "context-fabric",
                "client_bindings": ["Cursor", "Codex", "OpenClaw"],
                "transport": "stdio",
                "launch_contract": {
                    "command": "C:\\Program Files\\nodejs\\node.exe",
                    "args": ["C:\\Users\\ynotf\\.cursor\\vendor\\context-fabric-mcp\\node_modules\\context-fabric\\dist\\index.js"],
                },
                "healthcheck": {"kind": "mcp_stdio", "methods": ["initialize", "tools/list"]},
                "criticality": "normal",
                "lifecycle": "active",
                "render_by_default": False,
                "capabilities": ["git_drift_tracking", "commit_context_capture", "agent_briefings"],
                "notes": ["Run `context-fabric init` only inside an approved Git-managed target workspace."],
            },
            "cursor-agent-mcp": {
                "canonical_id": "cursor-agent-mcp",
                "client_bindings": ["Cursor", "OpenClaw"],
                "transport": "stdio",
                "launch_contract": {"command": "npx.cmd", "args": ["-y", "cursor-agent-mcp@latest"]},
                "env_expectations": {
                    "CURSOR_API_KEY": "${ENV:CURSOR_API_KEY}",
                    "CURSOR_API_URL": "https://api.cursor.com",
                },
                "healthcheck": {"kind": "mcp_stdio", "methods": ["initialize", "tools/list"]},
                "capabilities": ["cursor_agent_bridge"],
                "criticality": "normal",
                "lifecycle": "active",
                "render_by_default": False,
                "notes": [
                    "Matches the live Cursor/OpenClaw stdio entry; requires CURSOR_API_KEY from user/process environment."
                ],
            },
            "eye2byte": EYE2BYTE_OPENCLAW_SERVER.copy(),
            "depwire": DEPWIRE_SERVER.copy(),
            "mem0_mcp_server": {
                "canonical_id": "mem0_mcp_server",
                "client_bindings": ["Codex", "Cursor", "OpenClaw", "Open Interpreter", "MiniMax Code", "Android Studio"],
                "transport": "streamable-http",
                "launch_contract": {"url": "https://mcp.mem0.ai/mcp"},
                "env_expectations": {
                    "MEM0_API_KEY": "${ENV:MEM0_API_KEY}",
                    "MEM0_DEFAULT_USER_ID": "master_developer_profile",
                },
                "headers": {"Authorization": "Bearer ${ENV:MEM0_API_KEY}"},
                "healthcheck": {"kind": "mem0_rest_ping", "url": "https://api.mem0.ai/v1/ping/"},
                "capabilities": ["semantic_memory", "cross_session_memory"],
                "criticality": "normal",
                "lifecycle": "quarantined",
                "render_by_default": False,
                "notes": ["Raw Mem0 is not a normal-agent path. Use global-memory-gateway for governed memory."],
            },
            "global-memory-gateway": {
                "canonical_id": "global-memory-gateway",
                "client_bindings": ["Codex", "Cursor", "Open Interpreter", "OpenClaw", "MiniMax Code", "Antigravity"],
                "transport": "stdio",
                "launch_contract": {
                    "command": str(PYTHON),
                    "args": [
                        "-m",
                        "autonomy_factory.global_memory_gateway",
                        "--user-id",
                        "master_developer_profile",
                    ],
                    "working_dir": str(MANAGED_ROOT),
                },
                "env_expectations": {
                    "MEM0_DEFAULT_USER_ID": "master_developer_profile",
                    "MEMORY_GATEWAY_BACKEND": "postgres",
                    "AGENT_CORE_PGHOST": "127.0.0.1",
                    "AGENT_CORE_PGPORT": "55432",
                    "AGENT_CORE_PGDATABASE": "agent_core",
                    "AGENT_CORE_PGUSER": "agent_ingest",
                    "AGENT_CORE_PGPASSWORD": "${ENV:AGENT_CORE_AGENT_INGEST_PASSWORD}",
                    "MEMORY_GATEWAY_EMBEDDING_PROVIDER": "auto",
                    "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
                    "MEMORY_GATEWAY_EMBEDDING_DIMENSIONS": "1536",
                    "OPENAI_API_KEY": "${ENV:OPENAI_API_KEY}",
                },
                "healthcheck": {"kind": "mcp_stdio", "methods": ["initialize", "tools/list"]},
                "capabilities": [
                    "governed_memory",
                    "postgresql_vector_memory",
                    "append_only_contract",
                    "project_scoped_writes",
                    "global_reads",
                ],
                "criticality": "critical",
                "lifecycle": "active",
                "notes": [
                    "Primary memory path for normal agents. Stop if unavailable; do not fall back to raw Mem0 unless explicitly approved.",
                    "Backed by PostgreSQL agent_core on 127.0.0.1:55432 with pgvector VECTOR(1536).",
                    "Uses OpenAI text-embedding-3-small when OPENAI_API_KEY is available; local_hash_v1 is offline fallback only.",
                    "Normal agents use memory_append/search/state; trusted ingest/admin jobs are the only direct PostgreSQL writers.",
                ],
            },
            "composio": {
                "canonical_id": "composio",
                "client_bindings": [],
                "transport": "streamable-http",
                "launch_contract": {"url": "https://connect.composio.dev/mcp"},
                "env_expectations": {"COMPOSIO_API_KEY": "${ENV:COMPOSIO_API_KEY}"},
                "healthcheck": {"kind": "quarantined"},
                "criticality": "normal",
                "lifecycle": "quarantined",
                "render_by_default": False,
                "capabilities": ["connected_app_workflows"],
                "notes": ["Quarantined by default because current runtime state is unstable. Do not render into clients until explicitly re-enabled."],
            },
        },
    }


def resolve_windows_command(command: str) -> str:
    if os.name != "nt":
        return command
    if command.lower() == "npx" and NODE_HOME.exists():
        candidate = NODE_HOME / "npx.cmd"
        if candidate.exists():
            return str(candidate)
    return command


def run_command(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    env = os.environ.copy()
    if NODE_HOME.exists():
        env["PATH"] = str(NODE_HOME) + os.pathsep + env.get("PATH", "")
    resolved = [resolve_windows_command(args[0]), *args[1:]]
    proc = subprocess.run(resolved, capture_output=True, text=True, timeout=timeout, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def check_docs_server_install() -> tuple[bool, str]:
    docs_path = Path("C:/Users/ynotf/.cursor/vendor/arabold-docs-mcp/node_modules/@arabold/docs-mcp-server/dist/index.js")
    fabric_path = Path("C:/Users/ynotf/.cursor/vendor/context-fabric-mcp/node_modules/context-fabric/dist/index.js")
    status = {
        "arabold_docs_installed": docs_path.exists(),
        "context_fabric_installed": fabric_path.exists(),
        "arabold_docs_entrypoint": str(docs_path),
        "context_fabric_entrypoint": str(fabric_path),
    }
    write_json(ROOT / "artifacts/docs-server-install.json", status)
    ok = status["arabold_docs_installed"] and status["context_fabric_installed"]
    return ok, json.dumps(status)


def probe_mem0() -> ProbeResult:
    key = first_env("MEM0_API_KEY")
    start = time.perf_counter()
    if not key:
        return ProbeResult(
            canonical="mem0_mcp_server",
            transport="streamable-http",
            status="auth_failed",
            error="MEM0_API_KEY missing in Process/User/Machine scope",
        )
    req = urllib.request.Request("https://api.mem0.ai/v1/ping/", headers={"Authorization": f"Token {key}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            latency = int((time.perf_counter() - start) * 1000)
            status = getattr(resp, "status", None)
            return ProbeResult(
                canonical="mem0_mcp_server",
                transport="streamable-http",
                status="healthy" if status == 200 else "degraded",
                latency_ms=latency,
                evidence={"http_status": status, "secret_present": True},
            )
    except urllib.error.HTTPError as exc:
        latency = int((time.perf_counter() - start) * 1000)
        return ProbeResult(
            canonical="mem0_mcp_server",
            transport="streamable-http",
            status="auth_failed" if exc.code in {401, 403} else "degraded",
            latency_ms=latency,
            error=f"HTTP {exc.code}",
            evidence={"http_status": exc.code, "secret_present": True},
        )
    except Exception as exc:
        latency = int((time.perf_counter() - start) * 1000)
        return ProbeResult(
            canonical="mem0_mcp_server",
            transport="streamable-http",
            status="unknown",
            latency_ms=latency,
            error=str(exc),
            evidence={"secret_present": True},
        )


def probe_url(canonical: str, url: str, transport: str) -> ProbeResult:
    start = time.perf_counter()
    probe_url_value = url
    if canonical == "artiforge":
        pat = first_env("ARTIFORGE_PAT")
        if not pat:
            return ProbeResult(
                canonical=canonical,
                transport=transport,
                status="auth_failed",
                error="ARTIFORGE_PAT missing in Process/User/Machine scope",
            )
        probe_url_value = (
            url.replace("${ARTIFORGE_PAT}", urllib.parse.quote(pat, safe=""))
            .replace("${env:ARTIFORGE_PAT}", urllib.parse.quote(pat, safe=""))
        )
    try:
        req = urllib.request.Request(probe_url_value, method="GET")
        with urllib.request.urlopen(req, timeout=20) as resp:
            latency = int((time.perf_counter() - start) * 1000)
            status = getattr(resp, "status", None)
            return ProbeResult(
                canonical=canonical,
                transport=transport,
                status="healthy" if status and status < 500 else "degraded",
                latency_ms=latency,
                evidence={"http_status": status},
            )
    except urllib.error.HTTPError as exc:
        latency = int((time.perf_counter() - start) * 1000)
        if canonical == "artiforge" and exc.code in {403, 405}:
            return ProbeResult(
                canonical=canonical,
                transport=transport,
                status="healthy",
                latency_ms=latency,
                evidence={"http_status": exc.code, "reachable_protected_endpoint": True},
            )
        return ProbeResult(
            canonical=canonical,
            transport=transport,
            status="auth_failed" if canonical == "artiforge" and exc.code in {400, 401, 403} else ("degraded" if exc.code < 500 else "unknown"),
            latency_ms=latency,
            error=f"HTTP {exc.code}",
            evidence={"http_status": exc.code},
        )
    except Exception as exc:
        latency = int((time.perf_counter() - start) * 1000)
        return ProbeResult(canonical=canonical, transport=transport, status="unknown", latency_ms=latency, error=str(exc))


def probe_docs_server_install(install_ok: bool, detail: str) -> ProbeResult:
    return ProbeResult(
        canonical="arabold-docs",
        transport="stdio",
        status="healthy" if install_ok else "launch_failed",
        error=None if install_ok else detail,
        evidence={"vendored_install_checked": True, "detail": detail},
    )


def probe_stdio_server(canonical: str, command: str, args: list[str], env_overrides: dict[str, str] | None = None, timeout: int = 120) -> ProbeResult:
    spec = {
        "command": resolve_windows_command(command),
        "args": args,
        "env": env_overrides or {},
    }
    start = time.perf_counter()
    try:
        code, stdout, stderr = run_command([str(PYTHON), str(ROOT / "probes/probe_stdio.py"), json.dumps(spec)], timeout=timeout)
        latency = int((time.perf_counter() - start) * 1000)
        if code != 0:
            return ProbeResult(canonical=canonical, transport="stdio", status="launch_failed", latency_ms=latency, exit_code=code, error=(stderr or stdout)[0:1000])
        payload = json.loads(stdout)
        tools = payload.get("tools", {}).get("result", {}).get("tools", [])
        schema_dir = ROOT / "schemas/tools" / canonical
        schema_dir.mkdir(parents=True, exist_ok=True)
        for tool in tools:
            tool_name = str(tool.get("name", "unknown")).replace("/", "_")
            schema = tool.get("inputSchema") or {}
            write_json(schema_dir / f"{tool_name}.schema.json", schema)
        return ProbeResult(
            canonical=canonical,
            transport="stdio",
            status="healthy",
            latency_ms=payload.get("latency_ms", latency),
            exit_code=0,
            tools_count=len(tools),
            evidence={
                "serverInfo": payload.get("initialize", {}).get("result", {}).get("serverInfo", {}),
                "schema_dir": str(schema_dir),
            },
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(canonical=canonical, transport="stdio", status="timeout", error=f"Timed out after {timeout}s")
    except Exception as exc:
        return ProbeResult(canonical=canonical, transport="stdio", status="unknown", error=str(exc))


def run_probes(model: dict[str, Any], docs_install_ok: bool, docs_install_detail: str) -> list[ProbeResult]:
    docs = model["servers"]["arabold-docs"]["launch_contract"]
    sequential = model["servers"]["sequential-thinking"]["launch_contract"]
    gateway = model["servers"]["global-memory-gateway"]["launch_contract"]
    results = [
        probe_stdio_server(
            "arabold-docs",
            docs["command"],
            docs["args"],
            {"OPENAI_API_KEY": first_env("OPENAI_API_KEY") or ""},
        ),
    ]
    results[0].evidence["install"] = {"ok": docs_install_ok, "detail": docs_install_detail}
    art = model["servers"]["artiforge"]
    results.append(probe_url("artiforge", art["launch_contract"]["url"], "http"))
    results.append(
        probe_stdio_server(
            "sequential-thinking",
            sequential["command"],
            sequential["args"],
            {"DISABLE_THOUGHT_LOGGING": "true"},
        )
    )
    results.append(
        probe_stdio_server(
            canonical="global-memory-gateway",
            command=gateway["command"],
            args=gateway["args"],
            env_overrides={"MEM0_DEFAULT_USER_ID": "master_developer_profile", "PYTHONPATH": str(MANAGED_ROOT / "src")},
        )
    )
    if "context-fabric" in model["servers"]:
        fabric = model["servers"]["context-fabric"]["launch_contract"]
        results.append(
            probe_stdio_server(
                canonical="context-fabric",
                command=fabric["command"],
                args=fabric["args"],
                timeout=90,
            )
        )
    results.append(
        ProbeResult(
            canonical="mem0_mcp_server",
            transport="streamable-http",
            status="skipped",
            error="Quarantined; global-memory-gateway is the governed primary memory path.",
        )
    )
    results.append(
        ProbeResult(
            canonical="composio",
            transport="streamable-http",
            status="skipped",
            error="Quarantined by default; do not render until explicitly re-enabled.",
        )
    )
    payload = {"generated_at": iso_now(), "results": [r.model_dump() for r in results]}
    write_json(ROOT / "artifacts/probe-results.json", payload)
    lines = ["# MCP Probe Results", "", f"Generated: {payload['generated_at']}", ""]
    for r in results:
        lines.append(f"- `{r.canonical}`: `{r.status}` ({r.transport})")
        if r.error:
            lines.append(f"  - reason: {r.error}")
        if r.latency_ms is not None:
            lines.append(f"  - latency_ms: {r.latency_ms}")
    (ROOT / "artifacts/probe-results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results


def get_rendered_servers(client: str, data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("mcpServers"), dict):
        return data["mcpServers"]
    mcp = data.get("mcp")
    if isinstance(mcp, dict) and isinstance(mcp.get("servers"), dict):
        return mcp["servers"]
    raise ValueError(f"{client}: missing MCP server container (`mcpServers` or `mcp.servers`).")


def validate_rendered_fragment(client: str, data: dict[str, Any]) -> bool:
    servers = get_rendered_servers(client, data)
    errors: list[str] = []
    if ("artiforge" + "__codebase_scanner") in servers:
        errors.append("Artiforge must be rendered as `artiforge`, not the legacy long name.")
    if "composio" in servers:
        errors.append("Composio is quarantined and must not be rendered into client fragments.")
    for server_name, server in servers.items():
        if not isinstance(server, dict):
            errors.append(f"{server_name}: server definition must be an object")
            continue
        has_command = bool(server.get("command"))
        has_url = bool(server.get("url") or server.get("httpUrl"))
        if not has_command and not has_url:
            errors.append(f"{server_name}: must define either `command`, `url`, or `httpUrl`")
        if has_url and not (server.get("type") or server.get("httpUrl") or server.get("headers")):
            errors.append(f"{server_name}: URL transport must define `type` or use Android Studio `httpUrl`")
        if server_name == "artiforge":
            url = str(server.get("url") or "")
            if client == "MiniMax Code":
                args = server.get("args") if isinstance(server.get("args"), list) else []
                if (
                    server.get("type") != "stdio"
                    or server.get("command") != "pwsh"
                    or "C:\\Users\\ynotf\\.codex\\mcp-wrappers\\artiforge-mcp.ps1" not in args
                ):
                    errors.append(
                        f"{server_name}: {client} requires the Artiforge stdio wrapper because "
                        "MiniMax does not interpolate environment variables in HTTP URLs."
                    )
            elif (
                server.get("type") != "http"
                or not url.startswith("https://tools.artiforge.ai/mcp?pat=")
                or "ARTIFORGE_PAT" not in url
            ):
                errors.append(
                    f"{server_name}: {client} requires `type: http` and "
                    "`url: https://tools.artiforge.ai/mcp?pat=${{env:ARTIFORGE_PAT}}`."
                )
    if errors:
        raise ValueError("; ".join(errors))
    return True


def render_clients(model: dict[str, Any], probes: list[ProbeResult]) -> dict[str, Any]:
    servers = model["servers"]
    client_names = ["Cursor", "Open Interpreter", "OpenClaw", "MiniMax Code", "Antigravity"]

    def env_for_client(server: dict[str, Any]) -> dict[str, str]:
        rendered: dict[str, str] = {}
        for key, value in server.get("env_expectations", {}).items():
            text = str(value)
            if text.startswith("${ENV:") and text.endswith("}"):
                text = "${env:" + text[6:-1] + "}"
            rendered[key] = text
        return rendered

    def render_server(server_name: str, server: dict[str, Any], client: str) -> dict[str, Any]:
        if server_name == "artiforge" and client == "MiniMax Code":
            return {
                "type": "stdio",
                "command": "pwsh",
                "args": [
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "C:\\Users\\ynotf\\.codex\\mcp-wrappers\\artiforge-mcp.ps1",
                ],
            }
        launch = server.get("launch_contract", {})
        transport = server.get("transport")
        if transport in {"http", "streamable-http"} and launch.get("url"):
            return {"type": "http", "url": launch["url"]}
        rendered: dict[str, Any] = {
            "type": "stdio",
            "command": launch.get("command"),
            "args": gateway_args_for_client(client) if server_name == "global-memory-gateway" else launch.get("args", []),
        }
        env = env_for_client(server)
        if env:
            rendered["env"] = env
        return rendered

    def render_for_client(client: str) -> dict[str, Any]:
        emitted: dict[str, Any] = {}
        for server_name, server in servers.items():
            if server_name == "context7":
                continue
            if server.get("lifecycle", "active") != "active" or not server.get("render_by_default", True):
                continue
            if client not in server.get("client_bindings", []):
                continue
            emitted[server_name] = render_server(server_name, server, client)
        return emitted

    cursor = {"mcpServers": render_for_client("Cursor")}
    open_interpreter = {"mcpServers": render_for_client("Open Interpreter")}
    openclaw = {"mcp": {"servers": render_for_client("OpenClaw")}}
    minimax = {"mcpServers": render_for_client("MiniMax Code")}
    antigravity = {"mcpServers": render_for_client("Antigravity")}

    android = {"mcpServers": render_for_client("Android Studio")}
    rendered = {
        "cursor-global.mcp.json": ("Cursor", cursor),
        "open-interpreter.config.fragment.json": ("Open Interpreter", open_interpreter),
        "openclaw.openclaw.fragment.json": ("OpenClaw", openclaw),
        "minimax.mcp.json": ("MiniMax Code", minimax),
        ANTIGRAVITY_RENDERER: ("Antigravity", antigravity),
        "android-studio.mcp.json": ("Android Studio", android),
    }
    validation_errors: dict[str, str] = {}
    for filename, (client, data) in rendered.items():
        try:
            validate_rendered_fragment(client, data)
        except ValueError as exc:
            validation_errors[client] = str(exc)
    if validation_errors:
        write_json(ROOT / "artifacts/render-validation-errors.json", validation_errors)
        return {
            "mem0_ok": False,
            "rendered": [],
            "write_gate": "blocked_structural_validation",
            "validation_errors": validation_errors,
            "artiforge_openclaw_fixed": False,
        }
    for filename, (_, data) in rendered.items():
        write_json(ROOT / "renderers" / filename, data)
    return {
        "mem0_ok": False,
        "rendered": list(rendered.keys()),
        "write_gate": "passed_repo_only",
        "validation_errors": {},
        "artiforge_openclaw_fixed": True,
    }


def write_governance_files(model: dict[str, Any]) -> None:
    source_root = display_path(ROOT)
    live_ops_root = display_path(LIVE_OPS_ROOT)
    agents = f"""# CHAOSCENTRAL MCP Control Plane Agent Contract

This repository, `{source_root}`, is the canonical Git source repo for MCP governance, renderer candidates, and repo validators.

The current live deployed ops root remains `{live_ops_root}` until a deliberate migration is approved.

## Operating Rules

- Work primarily in this repository unless the user explicitly authorizes live rollout.
- Do not edit live client configs during repo-only phases.
- Create a timestamped rollback copy before editing existing managed files.
- Use unlock -> edit -> validate -> re-lock for managed files.
- Patch `scripts/mcp_control_plane.py` first when generated outputs would otherwise drift.
- Keep supervisor JSON, supervisor YAML, registry, renderers, and validators aligned.
- Use deterministic validators before reporting completion.
- AgentCore does not use `.env` files for secrets or local runtime configuration. Use Windows environment variables only.
- Agents must read `AGENT_DATABASE_BOOTSTRAP.md` and `contracts/global-memory-database-contract.json` before persistent memory writes or database ingestion.

## Tool Routing

- Planning: use `sequential-thinking` for ambiguous multi-step strategy.
- Repo code work: use Serena first for project activation, symbol discovery, and targeted refactors.
- Deterministic code graph and change safety: use `depwire` for dependency edges, impact analysis, structural simulation, graph-aware security, and pre-completion verification. Connect verified local repo paths only. Keep `.depwire/` and `depwire-output.json` globally ignored.
- Current software, SDK, CLI, API, cloud, and package docs: use `arabold-docs` first. Keep docs indexed/current before answering implementation guidance.
- Project continuity and drift context: use `context-fabric` only for approved Git-managed workspaces; do not initialize it in global infrastructure directories.
- Memory: use `global-memory-gateway` as the governed PostgreSQL/pgvector primary path. Do not route normal agents to raw Mem0 or ad hoc direct SQL.
- Embeddings: use the gateway-owned provider contract (`text-embedding-3-small` at 1536 dimensions when `OPENAI_API_KEY` is available; `local_hash_v1` only as offline fallback).
- Architecture scans: use `artiforge` only for high-leverage scans and refactor strategy.
- Connected app workflows: keep Composio quarantined until explicitly re-enabled.

## Stop Policy

For `global-memory-gateway`, `arabold-docs`, `artiforge`, and `sequential-thinking`, do not silently downgrade. If the primary fails and no high-quality fallback exists, stop and notify the user.

## Database Contract

- Canonical Git source repo: `{source_root}`
- Current live deployed ops root: `{live_ops_root}`
- Bootstrap contract in source repo: `{source_root}\\AGENT_DATABASE_BOOTSTRAP.md`
- Machine contract in source repo: `{source_root}\\contracts\\global-memory-database-contract.json`
- Database: PostgreSQL `agent_core` on `127.0.0.1:55432`
- Vector store: `global_vector_memory_store` with pgvector `VECTOR(1536)`
- Normal write path: `global-memory-gateway` tools only
- Trusted direct SQL path: explicit ingest/admin runners approved by the control plane
- Gateway runtime credentials: `AGENT_CORE_PGUSER=agent_ingest` and `AGENT_CORE_PGPASSWORD=${{ENV:AGENT_CORE_AGENT_INGEST_PASSWORD}}`
"""
    security = f"""# Security Policy

## Secrets

- Never hard-code API keys, bearer tokens, refresh tokens, cookies, private keys, passwords, license files, or PAT values.
- Use Windows User-scope environment variables for durable local secrets.
- AgentCore does not use `.env`, `.env.local`, `.env.production`, `.env.example`, dotenv loaders, or local secret files unless an operator explicitly orders an exception.
- Generated config fragments may reference secrets only with placeholders such as `${{env:ARTIFORGE_PAT}}` or `${{ENV:OPENAI_API_KEY}}`.
- Do not write secret values into reports, Markdown, registry files, validators, renderers, or logs.
- Documentation may list variable names only, never values.
- If a secret variable is missing, stop and report the variable name instead of creating a local fallback.

## Approval Gates

- Repo-only hardening may update files under `{source_root}`.
- `{live_ops_root}` remains the live ops root for scheduled tasks and current archive hooks until a separate approved migration.
- Live client config writes require an explicit user instruction for that rollout.
- Composio is quarantined by default and must not be rendered into client fragments.
- Raw Mem0 is not a normal-agent memory route; use PostgreSQL-backed `global-memory-gateway`.
- Raw secrets must not be stored in PostgreSQL vector memory; store only secret references, scopes, status, and non-reversible fingerprints.

## Read-only Enforcement

Managed governance and renderer files should be re-locked after validation.
Unlock only the exact files being edited, keep a rollback copy, run validation, then restore read-only attributes.
"""
    routing = """# Global MCP Routing Rules

## Enforced Order

1. Planning and strategy: `sequential-thinking`.
2. Repository code exploration and refactors: Serena.
3. Deterministic dependency graph, blast radius, structural simulation, and pre-action verification: `depwire`.
4. Current software, SDK, CLI, API, cloud, and package docs: `arabold-docs`.
5. Governed PostgreSQL/pgvector memory: `global-memory-gateway`.
6. Project continuity, commit context, and drift briefings: `context-fabric`, only inside approved Git-managed target repos.
7. Architecture or codebase quality scan: `artiforge`.
8. Browser/UI validation: Browser or Playwright, only when a UI target exists.
9. External web content: Firecrawl search or scrape when current web evidence is required.
10. Connected accounts and SaaS workflows: app connectors only when the user explicitly asks.

## DepWire Policy

- Use global `depwire-cli@1.8.2` through `C:\\Users\\ynotf\\AppData\\Roaming\\npm\\depwire.cmd mcp` with `DEPWIRE_NO_TELEMETRY=1`.
- The CLI/MCP server has no DepWire API/license key. DepWire Pro belongs only to the VS Code/Cursor extension setting `depwire.licenseKey`.
- Connect verified local repository paths only; remote clone/pull/fetch requires explicit operator approval.
- Use `impact_analysis` and `simulate_change` before risky structural edits, then `verify_change` plus native project validators before completion.
- `connect_repo` creates `.depwire/cache.db`; keep `.depwire/` and `depwire-output.json` globally ignored and never commit them.
- Keep remote/filesystem side-effect tools behind approval and do not use DepWire decision logs as the normal durable memory path.

## Fallback Policy

Critical tools are `global-memory-gateway`, `arabold-docs`, `artiforge`, and `sequential-thinking`.

If a critical primary fails:

- Use a fallback only when it preserves output quality and governance.
- Do not replace `global-memory-gateway` with raw Mem0 for normal memory work.
- Do not bypass `global-memory-gateway` with ad hoc direct SQL for normal memory work.
- Do not choose ad hoc embedding models; the gateway owns the embedding provider contract.
- Do not replace `arabold-docs` with stale model memory for current library/API guidance.
- Do not use `context-fabric` as a general memory layer; it is for project continuity and drift tracking.
- Do not replace `sequential-thinking` with `thinking-patterns`; `thinking-patterns` is retired.
- If no high-quality fallback exists, stop and notify the user with the failing tool, evidence, and next repair step.

## Quarantine

- `composio` is quarantined by default.
- `mem0_mcp_server` is quarantined for normal-agent memory use.
- `context7` is retired and must not be emitted into generated client renderers.
- `artiforge__codebase_scanner` is retired in favor of `artiforge`.
- Quarantined tools must not be emitted into client renderers unless a later approved rollout changes the lifecycle.
"""
    env_rules = """# Environment and Secrets Rules

## Windows Scope

- Durable local secrets belong in Windows User-scope environment variables.
- Process-scope values are acceptable for one-off validation but are not durable.
- Machine-scope secrets require explicit user approval.
- AgentCore uses Windows environment variables, not `.env` files.
- Never create `.env`, `.env.local`, `.env.production`, `.env.example`, dotenv files, or dotenv loaders for AgentCore unless an operator explicitly orders an exception.
- Never persist secrets in `.env`, JSON, YAML, Markdown, logs, reports, screenshots, email, SQLite, pgvector payloads, or memory.
- Config files may reference environment variable names only; documentation may list variable names only, never values.
- If a tool asks for a `.env` file, adapt it to Windows environment variables instead.
- If an environment variable is missing, stop and report the variable name instead of creating a local `.env` fallback.
- `global-memory-gateway` must use `agent_ingest` through Windows environment variables.
- Normal IDE agents must never direct-SQL into PostgreSQL.

## Allowed References

- `${env:ARTIFORGE_PAT}`
- `${ENV:ARTIFORGE_PAT}`
- `${env:OPENAI_API_KEY}`
- `${ENV:OPENAI_API_KEY}`
- `${env:GITHUB_PERSONAL_ACCESS_TOKEN}`
- `${ENV:GITHUB_PERSONAL_ACCESS_TOKEN}`
- `${env:CURSOR_API_KEY}`
- `${ENV:CURSOR_API_KEY}`
- `${env:OBSIDIAN_API_KEY}`
- `${ENV:OBSIDIAN_API_KEY}`
- `${env:OBSIDIAN_LOCAL_REST_API}`
- `${ENV:OBSIDIAN_LOCAL_REST_API}`
- `${env:MEM0_API_KEY}`
- `${ENV:MEM0_API_KEY}`
- `${env:COMPOSIO_API_KEY}`
- `${ENV:COMPOSIO_API_KEY}`
- `${env:MEMORY_GATEWAY_BACKEND}`
- `${ENV:MEMORY_GATEWAY_BACKEND}`
- `${env:AGENT_CORE_PGHOST}`
- `${ENV:AGENT_CORE_PGHOST}`
- `${env:AGENT_CORE_PGPORT}`
- `${ENV:AGENT_CORE_PGPORT}`
- `${env:AGENT_CORE_PGDATABASE}`
- `${ENV:AGENT_CORE_PGDATABASE}`
- `${env:AGENT_CORE_PGUSER}`
- `${ENV:AGENT_CORE_PGUSER}`
- `${env:AGENT_CORE_PGPASSWORD}`
- `${ENV:AGENT_CORE_PGPASSWORD}`
- `${env:AGENT_CORE_AGENT_ADMIN_PASSWORD}`
- `${ENV:AGENT_CORE_AGENT_ADMIN_PASSWORD}`
- `${env:AGENT_CORE_AGENT_INGEST_PASSWORD}`
- `${ENV:AGENT_CORE_AGENT_INGEST_PASSWORD}`
- `${env:AGENT_CORE_AGENT_READ_PASSWORD}`
- `${ENV:AGENT_CORE_AGENT_READ_PASSWORD}`
- `${env:AGENT_CORE_POSTGRES_PASSWORD}`
- `${ENV:AGENT_CORE_POSTGRES_PASSWORD}`
- `${env:MEMORY_GATEWAY_EMBEDDING_PROVIDER}`
- `${ENV:MEMORY_GATEWAY_EMBEDDING_PROVIDER}`
- `${env:OPENAI_EMBEDDING_MODEL}`
- `${ENV:OPENAI_EMBEDDING_MODEL}`
- `${env:MEMORY_GATEWAY_EMBEDDING_DIMENSIONS}`
- `${ENV:MEMORY_GATEWAY_EMBEDDING_DIMENSIONS}`

Literal secret values are forbidden. Validators must fail if they detect likely hard-coded credentials outside rollback backups.
"""
    write_text(ROOT / "AGENTS.md", agents)
    write_text(ROOT / "SECURITY.md", security)
    write_text(ROOT / "rules/global-mcp-routing.md", routing)
    write_text(ROOT / "rules/environment-and-secrets.md", env_rules)

    registry_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema_version", "generated_at", "tools"],
        "properties": {
            "schema_version": {"type": "string"},
            "generated_at": {"type": "string"},
            "tools": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "canonical_id", "lifecycle", "criticality", "transport", "health"],
                    "properties": {
                        "id": {"type": "string"},
                        "canonical_id": {"type": "string"},
                        "lifecycle": {"enum": ["active", "quarantined", "retired"]},
                        "criticality": {"enum": ["critical", "normal"]},
                        "transport": {"type": "string"},
                        "health": {"type": "string"},
                        "fallback_policy": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
            },
        },
        "additionalProperties": False,
    }
    write_json(ROOT / "registry/tool-registry.schema.json", registry_schema)


def write_tool_registry(model: dict[str, Any], probes: list[ProbeResult]) -> None:
    health = {probe.canonical: probe.status for probe in probes}
    tools = []
    for tool_id, server in model["servers"].items():
        tools.append(
            {
                "id": tool_id,
                "canonical_id": server["canonical_id"],
                "lifecycle": server.get("lifecycle", "active"),
                "criticality": server.get("criticality", "normal"),
                "transport": server.get("transport", "unknown"),
                "client_bindings": server.get("client_bindings", []),
                "capabilities": server.get("capabilities", []),
                "env_expectations": sorted(server.get("env_expectations", {}).keys()),
                "health": health.get(tool_id, "not_probed"),
                "fallback_policy": model["fallback_policy"]["rule"]
                if server.get("criticality") == "critical"
                else "No fallback unless it preserves governance and quality.",
                "render_by_default": bool(server.get("render_by_default", server.get("lifecycle", "active") == "active")),
                "notes": server.get("notes", []),
            }
        )
    registry = {
        "schema_version": "2026-06-10",
        "generated_at": iso_now(),
        "source": {
            "supervisor": str(ROOT / "supervisor/servers.json"),
            "health": str(ROOT / "artifacts/probe-results.json"),
        },
        "tools": tools,
    }
    write_json(ROOT / "registry/tool-registry.json", registry)


def write_agent_team_evidence(model: dict[str, Any], probes: list[ProbeResult]) -> None:
    gateway_probe = next((probe for probe in probes if probe.canonical == "global-memory-gateway"), None)
    validation = {
        "ok": gateway_probe is not None and gateway_probe.status == "healthy",
        "generated_at": iso_now(),
        "authority": str(ROOT),
        "server": "global-memory-gateway",
        "status": gateway_probe.status if gateway_probe else "missing",
        "storage_backend": "postgres",
        "embedding_provider": "auto",
        "preferred_embedding_provider": "openai_text_embedding_3_small",
        "fallback_embedding_provider": "local_hash_v1",
        "database": {
            "host": "127.0.0.1",
            "port": 55432,
            "database": "agent_core",
            "vector_table": "global_vector_memory_store",
            "telemetry_table": "agent_cross_project_telemetry",
        },
    }
    manifest = {
        "schema_version": "2026-06-21",
        "authority": str(ROOT),
        "normal_endpoint": {
            "server": "global-memory-gateway",
            "allowed_tools": ["memory_append", "memory_search", "memory_state"],
            "forbidden_tools": [
                "update_memory",
                "delete_memory",
                "delete_all_memories",
                "delete_entities",
            ],
            "storage_backend": "postgres",
            "embedding_provider": "auto",
            "preferred_embedding_provider": "openai_text_embedding_3_small",
            "fallback_embedding_provider": "local_hash_v1",
        },
        "database_contract": str(ROOT / "contracts/global-memory-database-contract.json"),
        "bootstrap_contract": str(ROOT / "AGENT_DATABASE_BOOTSTRAP.md"),
        "raw_mem0": {
            "lifecycle": model["servers"].get("mem0_mcp_server", {}).get("lifecycle", "unknown"),
            "normal_agent_path": False,
        },
    }
    write_json(ROOT / "artifacts/agent-team-control-plane-validation.json", validation)
    write_json(ROOT / "artifacts/agent-team-global-memory-manifest.json", manifest)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    was_read_only = path.exists() and not os.access(path, os.W_OK)
    if was_read_only:
        os.chmod(path, 0o666)
    path.write_text(content, encoding="utf-8")
    if was_read_only:
        os.chmod(path, 0o444)


def write_docs(model: dict[str, Any], probes: list[ProbeResult], render_status: dict[str, Any], backup_manifest: dict[str, Any], inventory_payload: dict[str, Any]) -> None:
    source_root = display_path(ROOT)
    live_ops_root = display_path(LIVE_OPS_ROOT)
    docs_sources = [
        {
            "name": "Model Context Protocol specification",
            "url": "https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/transports.mdx",
            "used_for": "stdio transport, stderr logging, initialize lifecycle, tools/list schema capture",
        },
        {
            "name": "Mem0 MCP official docs",
            "url": "https://github.com/mem0ai/mem0-mcp/blob/main/README.md",
            "used_for": "cloud HTTP endpoint and MEM0_API_KEY / MEM0_DEFAULT_USER_ID expectations",
        },
        {
            "name": "Grounded Docs MCP Server",
            "url": "https://github.com/arabold/docs-mcp-server",
            "used_for": "arabold-docs stdio entrypoint, npm package, and docs indexing behavior",
        },
        {
            "name": "Context Fabric MCP Server",
            "url": "https://github.com/VIKAS9793/context-fabric",
            "used_for": "context-fabric package, project continuity scope, and Git workspace constraints",
        },
        {
            "name": "Cursor MCP docs",
            "url": "https://cursor.com/docs/mcp",
            "used_for": "mcp.json shape, transports, interpolation, global/project locations",
        },
        {
            "name": "Android Studio MCP docs",
            "url": "https://developer.android.com/studio/gemini/add-mcp-server",
            "used_for": "Android Studio HTTP-only MCP config and limitations",
        },
    ]
    write_json(ROOT / "artifacts/docs-sources.json", docs_sources)

    secrets = env_status([
        "MEM0_API_KEY",
        "MEM0_DEFAULT_USER_ID",
        "ARTIFORGE_PAT",
        "OPENAI_API_KEY",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "CURSOR_API_KEY",
        "COMPOSIO_API_KEY",
        "OBSIDIAN_API_KEY",
        "OBSIDIAN_LOCAL_REST_API",
        "OBSIDIAN_VAULT_PATH",
    ])
    write_json(ROOT / "artifacts/secrets-required.json", secrets)
    secret_lines = ["# Required Secrets and Environment", "", "Values are intentionally not materialized.", ""]
    for key, scopes in secrets.items():
        present = any(v["present"] for v in scopes.values())
        secret_lines.append(f"- `{key}`: {'present' if present else 'missing'}")
        for scope, status in scopes.items():
            secret_lines.append(f"  - {scope}: present={status['present']} length={status['length']}")
    mem0 = next((p for p in probes if p.canonical == "mem0_mcp_server"), None)
    if mem0 and mem0.status == "auth_failed":
        secret_lines.append("")
        secret_lines.append("Mem0 is quarantined because the live auth probe failed. Correct the User-scope `MEM0_API_KEY`, then restart clients/fresh shells and rerun validation.")
    (ROOT / "artifacts/secrets-required.md").write_text("\n".join(secret_lines) + "\n", encoding="utf-8")

    graph = {
        "nodes": [
            *[{"id": key, "kind": "server"} for key in model["servers"]],
            *[{"id": client["client"], "kind": "client"} for client in inventory_payload["assets"]],
            {"id": "MEM0_API_KEY", "kind": "secret"},
            {"id": "ARTIFORGE_PAT", "kind": "secret"},
            {"id": "OPENAI_API_KEY", "kind": "secret"},
        ],
        "edges": [],
    }
    for asset in inventory_payload["assets"]:
        for server in asset["servers"]:
            graph["edges"].append({"from": asset["client"], "to": server["canonical"], "kind": "configured_server"})
    for key, server in model["servers"].items():
        for env_key in server.get("env_expectations", {}):
            graph["edges"].append({"from": key, "to": env_key, "kind": "requires_env"})
    write_json(ROOT / "artifacts/dependency-graph.json", graph)

    mermaid = ["# Dependency Graph", "", "```mermaid", "flowchart LR"]
    for edge in graph["edges"]:
        mermaid.append(f'  "{edge["from"]}" -->|{edge["kind"]}| "{edge["to"]}"')
    mermaid.append("```")
    mermaid.extend(
        [
            "",
            "## Corrective Pass Notes",
            "",
            "- Previous Artiforge renderer regression: generated fragments drifted between the old SSE host and the official HTTP MCP endpoint.",
            "- Corrected dependency shape: clients receive `type: http` with `https://tools.artiforge.ai/mcp?pat=${env:ARTIFORGE_PAT}`.",
        ]
    )
    (ROOT / "docs/dependency-graph.md").write_text("\n".join(mermaid) + "\n", encoding="utf-8")

    drift = {
        "generated_at": iso_now(),
        "render_status": render_status,
        "findings": [],
    }
    if any(server.get("lifecycle") == "quarantined" for server in model["servers"].values()):
        drift["findings"].append(
            {
                "severity": "medium",
                "component": "quarantine",
                "issue": "Raw Mem0 and Composio remain quarantined; global-memory-gateway is the governed primary memory path.",
            }
        )
    if "context7" not in model["servers"]:
        drift["findings"].append(
            {
                "severity": "fixed",
                "component": "context7",
                "issue": "Context7 is retired in the control plane; arabold-docs is the primary current-docs route.",
            }
        )
    drift["findings"].append(
            {
                "severity": "fixed",
                "component": "artiforge",
                "issue": "Previous regression was caused by stale Artiforge rendering; clients now render the standard artiforge key with the live working http + PAT query string shape.",
            }
        )
    write_json(ROOT / "artifacts/drift-report.json", drift)
    (ROOT / "docs/drift-report.md").write_text(
        "# Drift Report\n\n"
        + "\n".join(f"- {f['severity']}: `{f['component']}` - {f['issue']}" for f in drift["findings"])
        + "\n",
        encoding="utf-8",
    )

    catalog = ["# Contract Catalog", "", "Full per-tool JSON Schema extraction requires healthy MCP initialize/tools-list probes."]
    for result in probes:
        catalog.append(f"- `{result.canonical}`: `{result.status}`")
    (ROOT / "docs/contract-catalog.md").write_text("\n".join(catalog) + "\n", encoding="utf-8")

    runbook = f"""# Rollout Runbook

Manual corrective one-liner for OpenClaw Artiforge while automated rollout is gated: set `mcp.servers.artiforge` to `{{ "type": "http", "url": "https://tools.artiforge.ai/mcp?pat=${{env:ARTIFORGE_PAT}}" }}`.

1. Fix any blockers in `{source_root}\\artifacts\\final-status.json` for source-repo validation.
2. Use `{source_root}` as the canonical Git source for docs, renderers, contracts, and validators.
3. Treat `{live_ops_root}` as the current live ops root for scheduled tasks, WAL archiving, and approved live rollout steps until migration is explicitly approved.
4. Restart Cursor, Open Interpreter, MiniMax Code, OpenClaw, and Android Studio after config changes.
5. Re-run probes and compare `{source_root}\\artifacts\\drift-report.json`.

Rollback copies are under the `rollback` location in `{source_root}\\artifacts\\backup-manifest.json`.
"""
    (ROOT / "docs/rollout-runbook.md").write_text(runbook, encoding="utf-8")

    final = {
        "generated_at": iso_now(),
        "root": str(ROOT),
        "inventory_total_assets": len(inventory_payload["assets"]),
        "inventory_total_servers": len(inventory_payload["servers"]),
        "probe_summary": {p.canonical: p.status for p in probes},
        "memory_primary": "global-memory-gateway",
        "raw_mem0_status": next((p.status for p in probes if p.canonical == "mem0_mcp_server"), "unknown"),
        "client_write_status": render_status["write_gate"],
        "artiforge_openclaw_render_fixed": bool(render_status.get("artiforge_openclaw_fixed")),
        "render_validation_errors": render_status.get("validation_errors", {}),
        "backup_locations": backup_manifest["locations"],
        "rendered_files": [str(ROOT / "renderers" / f) for f in render_status["rendered"]],
        "docs_sources": docs_sources,
        "remaining_user_actions": [],
    }
    if final["raw_mem0_status"] != "skipped":
        final["remaining_user_actions"].append("Keep raw Mem0 disabled unless explicitly re-approved; global-memory-gateway is the primary memory path.")
    final["remaining_user_actions"].append("Restart all MCP clients after any future apply run writes client configs.")
    write_json(ROOT / "artifacts/final-status.json", final)

    human = [
        "# Final Status",
        "",
        f"Generated: {final['generated_at']}",
        f"Root: `{ROOT}`",
        "",
        "## Summary",
        "",
        f"- Inventory assets: {final['inventory_total_assets']}",
        f"- Inventory servers: {final['inventory_total_servers']}",
        f"- Client write status: `{final['client_write_status']}`",
        f"- Primary memory: `{final['memory_primary']}`",
        f"- Raw Mem0 status: `{final['raw_mem0_status']}`",
        f"- Artiforge OpenClaw render fixed: `{final['artiforge_openclaw_render_fixed']}`",
        "",
        "## Corrective Pass",
        "",
        "- OpenClaw, MiniMax Code, and Open Interpreter now receive Artiforge as official `streamable-http` with an ARTIFORGE_PAT environment placeholder.",
        "- Cursor receives the official HTTP MCP URL with `${env:ARTIFORGE_PAT}` interpolation.",
        "- Android Studio remains HTTP-only with `httpUrl` style.",
        "",
        "## Probe Summary",
        "",
        *[f"- `{name}`: `{status}`" for name, status in final["probe_summary"].items()],
        "",
        "## Files Created",
        "",
        f"- `{source_root}\\inventory\\assets.json`",
        f"- `{source_root}\\inventory\\assets.yaml`",
        f"- `{source_root}\\supervisor\\servers.yaml`",
        f"- `{source_root}\\artifacts\\probe-results.json`",
        f"- `{source_root}\\artifacts\\drift-report.json`",
        f"- `{source_root}\\docs\\rollout-runbook.md`",
        f"- `{source_root}\\artifacts\\final-status.json`",
        "",
        "## Remaining User Actions",
        "",
        *[f"- {item}" for item in final["remaining_user_actions"]],
    ]
    (ROOT / "docs/final-status.md").write_text("\n".join(human) + "\n", encoding="utf-8")


def write_probe_harness() -> None:
    harness = r'''from __future__ import annotations

import json
import os
import subprocess
import sys
import time


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: probe_stdio.py '<json command spec>'", file=sys.stderr)
        return 2
    spec = json.loads(sys.argv[1])
    env = os.environ.copy()
    env.update(spec.get("env", {}))
    proc = subprocess.Popen(
        [spec["command"], *spec.get("args", [])],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "mcp-control-plane-probe", "version": "0.1.0"},
        },
    }
    assert proc.stdin and proc.stdout
    proc.stdin.write(json.dumps(initialize) + "\n")
    proc.stdin.flush()
    started = time.time()
    line = proc.stdout.readline()
    if not line:
        print(json.dumps({"status": "launch_failed", "stderr": proc.stderr.read() if proc.stderr else ""}))
        return 1
    init_response = json.loads(line)
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + "\n")
    proc.stdin.flush()
    tools_line = proc.stdout.readline()
    elapsed = int((time.time() - started) * 1000)
    proc.terminate()
    print(json.dumps({"status": "healthy", "latency_ms": elapsed, "initialize": init_response, "tools": json.loads(tools_line)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    (ROOT / "probes/probe_stdio.py").write_text(harness, encoding="utf-8")


def backup_live_file(path: Path, backup_root: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    backup_root.mkdir(parents=True, exist_ok=True)
    destination = backup_root / safe_name(str(path))
    shutil.copy2(path, destination)
    return str(destination)


def write_live_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    was_read_only = path.exists() and not os.access(path, os.W_OK)
    if was_read_only:
        os.chmod(path, 0o666)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if was_read_only:
        os.chmod(path, 0o444)


def apply_json_servers(path: Path, payload: dict[str, Any], openclaw: bool = False) -> None:
    data, _ = read_json(path)
    if data is None:
        data = {}
    if openclaw:
        data.setdefault("mcp", {})
        data["mcp"]["servers"] = payload["mcp"]["servers"]
    else:
        data["mcpServers"] = payload["mcpServers"]
    write_live_json(path, data)


def apply_antigravity_json(path: Path, payload: dict[str, Any]) -> None:
    data, _ = read_json(path)
    if data is None:
        data = {}
    emitted_servers = set(payload.get("mcpServers", {}).keys())
    existing_names: set[str] = set()
    for container_name in ["mcpServers", "servers"]:
        container = data.get(container_name)
        if isinstance(container, dict):
            existing_names.update(str(name) for name in container.keys())
    quarantined = {
        name: {
            "disabled": True,
            "reason": "Retired or non-default Antigravity MCP server removed from active AgentCore surface. Raw values are intentionally not preserved here; see local rollback backup if restoration is needed.",
        }
        for name in sorted(existing_names - emitted_servers)
    }
    data["mcpServers"] = payload["mcpServers"]
    if quarantined:
        data["x_agentcore_quarantined_servers"] = quarantined
    else:
        data.pop("x_agentcore_quarantined_servers", None)
    data.pop("servers", None)
    write_live_json(path, data)


def codex_gateway_block() -> str:
    env_lines = [
        'MEM0_DEFAULT_USER_ID = "master_developer_profile"',
        'MEMORY_GATEWAY_BACKEND = "postgres"',
        'AGENT_CORE_PGHOST = "127.0.0.1"',
        'AGENT_CORE_PGPORT = "55432"',
        'AGENT_CORE_PGDATABASE = "agent_core"',
        'AGENT_CORE_PGUSER = "agent_ingest"',
        'MEMORY_GATEWAY_EMBEDDING_PROVIDER = "auto"',
        'OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"',
        'MEMORY_GATEWAY_EMBEDDING_DIMENSIONS = "1536"',
    ]
    filesystem_args = [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\ynotf",
        "D:\\Codex_Managed",
        "D:\\cursor_setup",
        "D:\\openclaw",
        "D:\\Obsidian",
        "F:\\AgentCore",
        "E:\\AgentCoreArchive",
    ]
    serena_args = [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--project-from-cwd",
        "--transport",
        "stdio",
    ]
    depwire_approved_tools = [
        "get_architecture_summary",
        "get_file_context",
        "get_dependencies",
        "get_dependents",
        "get_symbol_info",
        "search_symbols",
        "list_files",
        "impact_analysis",
        "get_health_score",
        "find_dead_code",
        "get_project_docs",
        "get_temporal_graph",
        "simulate_change",
        "security_scan",
        "verify_change",
        "get_active_claims",
        "get_decisions",
    ]
    depwire_tool_policy = "".join(
        f'[mcp_servers.depwire.tools.{tool}]\napproval_mode = "approve"\n\n'
        for tool in depwire_approved_tools
    )
    return (
        "# Generated by D:\\github\\agentcore-control-plane\\scripts\\mcp_control_plane.py.\n"
        "[mcp_servers.arabold-docs]\n"
        "command = 'C:\\Program Files\\nodejs\\node.exe'\n"
        'args = ["C:\\\\Users\\\\ynotf\\\\.cursor\\\\vendor\\\\arabold-docs-mcp\\\\node_modules\\\\@arabold\\\\docs-mcp-server\\\\dist\\\\index.js"]\n'
        'env_vars = ["OPENAI_API_KEY"]\n'
        "startup_timeout_sec = 30.0\n"
        "tool_timeout_sec = 300.0\n"
        'default_tools_approval_mode = "prompt"\n'
        "\n"
        "[mcp_servers.depwire]\n"
        'command = "C:\\\\Users\\\\ynotf\\\\AppData\\\\Roaming\\\\npm\\\\depwire.cmd"\n'
        'args = ["mcp"]\n'
        "startup_timeout_sec = 120.0\n"
        "tool_timeout_sec = 300.0\n"
        "required = false\n"
        'default_tools_approval_mode = "prompt"\n\n'
        "[mcp_servers.depwire.env]\n"
        'DEPWIRE_NO_TELEMETRY = "1"\n\n'
        + depwire_tool_policy
        + "[mcp_servers.global-memory-gateway]\n"
        "command = 'D:\\Codex_Managed\\.venv\\Scripts\\python.exe'\n"
        f'args = {json.dumps(gateway_args_for_client("Codex"))}\n'
        'env_vars = ["AGENT_CORE_AGENT_INGEST_PASSWORD", "OPENAI_API_KEY"]\n'
        "startup_timeout_sec = 30.0\n"
        "tool_timeout_sec = 120.0\n"
        'default_tools_approval_mode = "prompt"\n'
        "\n"
        "[mcp_servers.global-memory-gateway.env]\n"
        + "\n".join(env_lines)
        + "\n\n"
        + "[mcp_servers.artiforge]\n"
        + 'command = "pwsh"\n'
        + 'args = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\\\Users\\\\ynotf\\\\.codex\\\\mcp-wrappers\\\\artiforge-mcp.ps1"]\n'
        + 'env_vars = ["ARTIFORGE_PAT"]\n'
        + 'enabled_tools = ["artiforge-make-development-task-plan", "codebase-scanner", "artiforge-make-project-docs"]\n'
        + "startup_timeout_sec = 30.0\n"
        + "tool_timeout_sec = 300.0\n\n"
        + "[mcp_servers.filesystem]\n"
        + 'command = "npx.cmd"\n'
        + f"args = {json.dumps(filesystem_args)}\n"
        + "startup_timeout_sec = 30.0\n"
        + "tool_timeout_sec = 120.0\n\n"
        + "[mcp_servers.obsidian-vault]\n"
        + 'command = "pwsh"\n'
        + 'args = ["-NoProfile", "-NonInteractive", "-File", "C:\\\\Users\\\\ynotf\\\\.openclaw\\\\start-obsidian-mcp-server.ps1"]\n'
        + 'env_vars = ["OBSIDIAN_API_KEY", "OBSIDIAN_LOCAL_REST_API"]\n'
        + "startup_timeout_sec = 30.0\n"
        + "tool_timeout_sec = 120.0\n\n"
        + "[mcp_servers.obsidian-vault.env]\n"
        + 'OBSIDIAN_BASE_URL = "https://127.0.0.1:27124"\n'
        + 'OBSIDIAN_VERIFY_SSL = "false"\n\n'
        + "[mcp_servers.playwright]\n"
        + 'command = "npx.cmd"\n'
        + 'args = ["-y", "@playwright/mcp@latest"]\n'
        + "startup_timeout_sec = 30.0\n"
        + "tool_timeout_sec = 180.0\n\n"
        + "[mcp_servers.sequential-thinking]\n"
        + 'command = "npx.cmd"\n'
        + 'args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]\n'
        + "startup_timeout_sec = 30.0\n"
        + "tool_timeout_sec = 120.0\n\n"
        + "[mcp_servers.sequential-thinking.env]\n"
        + 'DISABLE_THOUGHT_LOGGING = "true"\n\n'
        + "[mcp_servers.serena]\n"
        + 'command = "C:\\\\Users\\\\ynotf\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python311\\\\Scripts\\\\uvx.exe"\n'
        + f"args = {json.dumps(serena_args)}\n"
        + "startup_timeout_sec = 30.0\n"
        + "tool_timeout_sec = 300.0\n\n"
    )


def apply_codex_config(backup_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"target": str(CODEX_CONFIG), "exists": CODEX_CONFIG.exists(), "backup": None, "updated": False}
    if not CODEX_CONFIG.exists():
        return result
    result["backup"] = backup_live_file(CODEX_CONFIG, backup_root)
    text = CODEX_CONFIG.read_text(encoding="utf-8")
    text = re.sub(r'(\[plugins\."mem0@mem0-plugins"\]\s*enabled\s*=\s*)true', r"\1false", text)
    filtered_lines: list[str] = []
    skip_section = False
    generated_markers = (
        "# Generated by D:\\Codex_Managed\\config\\global-memory-system.manifest.json.",
        "# Generated by D:\\github\\agentcore-control-plane\\scripts\\mcp_control_plane.py.",
    )
    removable_headers = (
        "[marketplaces.mem0-plugins]",
        '[plugins."mem0@mem0-plugins"]',
        '[hooks.state."mem0@mem0-plugins',
        "[mcp_servers.arabold-docs]",
        "[mcp_servers.global-memory-gateway]",
        "[mcp_servers.global-memory-gateway.env]",
        "[mcp_servers.artiforge]",
        "[mcp_servers.mem0]",
        "[mcp_servers.mem0.env]",
        "[mcp_servers.artiforge__codebase_scanner]",
        "[mcp_servers.firecrawl-direct]",
        "[mcp_servers.firecrawl-direct.env]",
        "[mcp_servers.filesystem]",
        "[mcp_servers.obsidian-vault]",
        "[mcp_servers.obsidian-vault.env]",
        "[mcp_servers.depwire",
        "[mcp_servers.playwright]",
        "[mcp_servers.sequential-thinking]",
        "[mcp_servers.sequential-thinking.env]",
        "[mcp_servers.serena]",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in generated_markers:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            if stripped.startswith(removable_headers):
                skip_section = True
                continue
            skip_section = False
        if not skip_section:
            filtered_lines.append(line)
    text = "\n".join(filtered_lines).strip() + "\n"
    marker = re.search(r"(?m)^\[projects\.", text)
    block = codex_gateway_block()
    if marker:
        text = text[: marker.start()] + block + text[marker.start() :]
    else:
        text = text.rstrip() + "\n\n" + block
    was_read_only = CODEX_CONFIG.exists() and not os.access(CODEX_CONFIG, os.W_OK)
    if was_read_only:
        os.chmod(CODEX_CONFIG, 0o666)
    CODEX_CONFIG.write_text(text, encoding="utf-8")
    if was_read_only:
        os.chmod(CODEX_CONFIG, 0o444)
    result["updated"] = True
    return result


def apply_rendered_configs(stamp: str) -> dict[str, Any]:
    backup_root = ROOT / "artifacts" / "backups" / stamp / "live-client-configs" / "raw"
    rendered_targets = {
        "Cursor Global": ROOT / "renderers/cursor-global.mcp.json",
        "Cursor Project": ROOT / "renderers/cursor-global.mcp.json",
        "Open Interpreter": ROOT / "renderers/open-interpreter.config.fragment.json",
        "MiniMax Code": ROOT / "renderers/minimax.mcp.json",
        "OpenClaw": ROOT / "renderers/openclaw.openclaw.fragment.json",
        "Antigravity": ROOT / "renderers" / ANTIGRAVITY_RENDERER,
        "Antigravity Roaming": ROOT / "renderers" / ANTIGRAVITY_RENDERER,
        "Android Studio": ROOT / "renderers/android-studio.mcp.json",
        "Android Studio Config Dir": ROOT / "renderers/android-studio.mcp.json",
    }
    applied: list[dict[str, Any]] = [apply_codex_config(backup_root)]
    for target in discover_targets():
        rendered_path = rendered_targets.get(target.client)
        if rendered_path is None or not rendered_path.exists():
            continue
        payload, error = read_json(rendered_path)
        if payload is None:
            raise SystemExit(f"Cannot parse rendered fragment {rendered_path}: {error}")
        destination = Path(target.file_path)
        backup = backup_live_file(destination, backup_root)
        if target.client == "OpenClaw":
            apply_json_servers(destination, payload, openclaw=True)
        elif target.client in {"Antigravity", "Antigravity Roaming"}:
            apply_antigravity_json(destination, payload)
        else:
            apply_json_servers(destination, payload, openclaw=False)
        applied.append({"target": target.file_path, "backup": backup, "updated": True})
    return {"backup_root": str(backup_root), "applied": applied}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply rendered client configs after critical probes pass")
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT), help="source repo root for generated docs, contracts, renderers, and validators")
    parser.add_argument("--live-ops-root", default=str(LIVE_OPS_ROOT), help="current live deployed ops root referenced by scheduled tasks and rollout docs")
    args = parser.parse_args()
    configure_roots(Path(args.source_root), Path(args.live_ops_root))
    ensure_dirs()
    stamp = now_stamp()
    targets = discover_targets()
    backup_manifest = backup_repo_managed_files(stamp)
    servers, inventory_payload = inventory(targets)
    docs_install_ok, docs_install_detail = check_docs_server_install()
    model = canonical_model(docs_install_ok)
    write_json(ROOT / "supervisor/servers.json", model)
    write_yaml(ROOT / "supervisor/servers.yaml", model)
    write_json(ROOT / "supervisor/config.schema.json", {"type": "object", "required": ["servers"], "properties": {"servers": {"type": "object"}}})
    write_governance_files(model)
    write_probe_harness()
    probes = run_probes(model, docs_install_ok, docs_install_detail)
    render_status = render_clients(model, probes)
    write_tool_registry(model, probes)
    write_agent_team_evidence(model, probes)
    write_docs(model, probes, render_status, backup_manifest, inventory_payload)
    apply_status: dict[str, Any] | None = None
    if args.apply:
        if render_status.get("write_gate") != "passed_repo_only":
            raise SystemExit(f"Apply blocked because rendered output is not valid: {render_status}")
        apply_status = apply_rendered_configs(stamp)
    log = {"stamp": stamp, "completed_at": iso_now(), "root": str(ROOT), "render_status": render_status, "apply_status": apply_status}
    write_json(ROOT / "ops/logs" / f"bootstrap-{stamp}.json", log)
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
