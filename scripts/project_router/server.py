#!/usr/bin/env python3
"""AgentCore project router MCP server (stdio JSON-RPC).

Tools: project_list, project_activate, project_status, project_clear.
Roots and runtime state are installation-relative or environment-configured.
"""

from __future__ import annotations

import json
import ipaddress
import os
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SERVER_NAME = "agentcore-project-router"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
PROJECTS_ROOT = Path(os.environ.get("AGENTCORE_PROJECTS_ROOT", str(REPO_ROOT.parent)))
RUNTIME_ROOT = Path(os.environ.get("AGENTCORE_RUNTIME_ROOT", r"F:\AgentCore\runtime"))
BIFROST_BASE = os.environ.get("AGENTCORE_BIFROST_BASE", "http://127.0.0.1:8080").rstrip("/")
ADMIN_KEY_ENV = "BIFROST_ADMIN_KEY"
STATE_PATH = Path(
    os.environ.get(
        "AGENTCORE_PROJECT_ROUTER_STATE",
        str(RUNTIME_ROOT / "bifrost" / "state" / "active-project.json"),
    )
)
GITHUB_ROOT = PROJECTS_ROOT
ALWAYS_ALLOW = [
    REPO_ROOT,
    PROJECTS_ROOT / "memory-context-database",
]
REJECT_MARKERS = (
    "swarmrecall",
    "swarmvault",
    "agentswarm",
    "swarmclaw",
)
_reject_roots = os.environ.get(
    "AGENTCORE_PROJECT_REJECT_ROOTS",
    str(RUNTIME_ROOT.parent / "agentmemory"),
)
REJECT_PREFIXES = tuple(
    Path(item)
    for item in _reject_roots.split(os.pathsep)
    if item.strip()
)


def _log(msg: str) -> None:
    sys.stderr.write(f"[{SERVER_NAME}] {msg}\n")
    sys.stderr.flush()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _rejected_path(path: Path) -> str | None:
    resolved = path.resolve()
    text = str(resolved).lower().replace("/", "\\")
    for marker in REJECT_MARKERS:
        if marker in text:
            return f"rejected Swarm-related path marker: {marker}"
    for prefix in REJECT_PREFIXES:
        try:
            if resolved == prefix.resolve() or prefix.resolve() in resolved.parents or resolved in [prefix.resolve()]:
                return f"rejected path under {prefix}"
            # also reject if path is under prefix
            resolved.relative_to(prefix.resolve())
            return f"rejected path under {prefix}"
        except ValueError:
            continue
        except OSError:
            continue
    return None


def scan_registered_projects() -> list[dict[str, str]]:
    found: dict[str, Path] = {}
    for p in ALWAYS_ALLOW:
        if p.exists() and _is_git_repo(p) and not _rejected_path(p):
            found[str(p.resolve())] = p.resolve()

    if GITHUB_ROOT.exists():
        for child in sorted(GITHUB_ROOT.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("."):
                continue
            if not _is_git_repo(child):
                continue
            reason = _rejected_path(child)
            if reason:
                continue
            found[str(child.resolve())] = child.resolve()

    projects = []
    for path in sorted(found.values(), key=lambda x: str(x).lower()):
        projects.append(
            {
                "id": path.name,
                "path": str(path),
                "name": path.name,
            }
        )
    return projects


def load_state() -> dict[str, Any] | None:
    if not STATE_PATH.exists():
        return None
    try:
        with STATE_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return None
        return data
    except (OSError, json.JSONDecodeError):
        return None


def save_state(data: dict[str, Any] | None) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if data is None:
        if STATE_PATH.exists():
            STATE_PATH.unlink()
        return
    temp_path = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, STATE_PATH)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _read_user_env(name: str) -> str:
    value = os.environ.get(name, "")
    if value or os.name != "nt":
        return value
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value or "")
    except OSError:
        return ""


def _validated_bifrost_base() -> str:
    parsed = urllib.parse.urlparse(BIFROST_BASE)
    host = parsed.hostname or ""
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise RuntimeError("Bifrost management base must be a loopback HTTP(S) URL")
    try:
        is_loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        is_loopback = host.lower() == "localhost"
    if not is_loopback:
        raise RuntimeError("Bifrost management base must remain loopback")
    return BIFROST_BASE


def _bifrost_admin_request(method: str, path: str) -> dict[str, Any]:
    admin_key = _read_user_env(ADMIN_KEY_ENV)
    if not admin_key:
        raise RuntimeError(f"{ADMIN_KEY_ENV} is unavailable")
    base = _validated_bifrost_base()
    request = urllib.request.Request(
        f"{base}{path}",
        data=b"" if method == "POST" else None,
        headers={
            "Authorization": f"Bearer {admin_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Bifrost {method} {path} failed: HTTP {exc.code}") from None


def _router_client_names() -> list[str]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(
        spec["bifrost_client_name"]
        for spec in (registry.get("servers") or {}).values()
        if spec.get("enabled") and spec.get("connection_type") == "router"
    )


def reconnect_router_clients() -> dict[str, Any]:
    """Reconnect only router-backed Bifrost upstreams after active-project change."""
    target_names = _router_client_names()
    if not target_names:
        return {"ok": True, "status": "not_required", "clients": []}
    try:
        payload = _bifrost_admin_request("GET", "/api/mcp/clients?limit=100")
        live_ids: dict[str, str] = {}
        for item in payload.get("clients") or []:
            config = item.get("config") or {}
            name = config.get("name")
            client_id = config.get("client_id")
            if name and client_id:
                live_ids[str(name)] = str(client_id)

        missing = [name for name in target_names if name not in live_ids]
        reconnected: list[str] = []
        failures: list[dict[str, str]] = []
        for name in target_names:
            client_id = live_ids.get(name)
            if not client_id:
                continue
            try:
                _bifrost_admin_request("POST", f"/api/mcp/client/{client_id}/reconnect")
                reconnected.append(name)
            except Exception as exc:  # noqa: BLE001
                failures.append({"client": name, "error": type(exc).__name__})

        ok = not missing and not failures
        return {
            "ok": ok,
            "status": "reconnected" if ok else "incomplete",
            "clients": reconnected,
            "missing": missing,
            "failures": failures,
        }
    except Exception as exc:  # noqa: BLE001
        _log(f"router-client reconnect unavailable: {type(exc).__name__}")
        return {
            "ok": False,
            "status": "unavailable",
            "clients": [],
            "error": type(exc).__name__,
        }


def tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "project_list",
            "title": "Project List",
            "description": "List registered project worktrees allowed for AgentCore project-scoped MCP servers.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "outputSchema": {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "projects": {"type": "array", "items": {"type": "object"}},
                    "active": {"type": ["string", "null"]},
                },
                "required": ["ok"],
                "additionalProperties": True,
            },
            "annotations": {
                "title": "Project List",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        },
        {
            "name": "project_activate",
            "title": "Project Activate",
            "description": "Activate a registered project by path or id for project-scoped upstream MCP servers.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute project path"},
                    "id": {"type": "string", "description": "Project folder name / id"},
                },
                "additionalProperties": False,
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "activated": {"type": "string"},
                    "project": {"type": "object"},
                    "active": {"type": ["object", "null"]},
                    "project_scoped_reconnect": {"type": "object"},
                    "rollback_reconnect": {"type": "object"},
                    "error": {"type": "string"},
                },
                "required": ["ok"],
                "additionalProperties": True,
            },
            "annotations": {
                "title": "Project Activate",
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        },
        {
            "name": "project_status",
            "title": "Project Status",
            "description": "Show the currently active project, if any.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "outputSchema": {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "active": {"type": ["string", "null"]},
                    "project": {"type": ["object", "null"]},
                },
                "required": ["ok"],
                "additionalProperties": True,
            },
            "annotations": {
                "title": "Project Status",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        },
        {
            "name": "project_clear",
            "title": "Project Clear",
            "description": "Clear the active project selection.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "outputSchema": {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "cleared": {"type": "string"},
                    "active": {"type": ["object", "null"]},
                    "project_scoped_reconnect": {"type": "object"},
                    "rollback_reconnect": {"type": "object"},
                    "error": {"type": "string"},
                },
                "required": ["ok"],
                "additionalProperties": True,
            },
            "annotations": {
                "title": "Project Clear",
                "readOnlyHint": False,
                "destructiveHint": True,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        },
    ]

def _match_project(projects: list[dict[str, str]], path: str | None, pid: str | None) -> dict[str, str] | None:
    if path:
        target = str(Path(path).resolve())
        for p in projects:
            if str(Path(p["path"]).resolve()) == target:
                return p
        return None
    if pid:
        matches = [p for p in projects if p["id"].lower() == pid.lower()]
        if len(matches) == 1:
            return matches[0]
    return None


def call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    arguments = arguments or {}
    projects = scan_registered_projects()

    if name == "project_list":
        return {
            "ok": True,
            "count": len(projects),
            "projects": projects,
            "rejected_policy": {
                "markers": list(REJECT_MARKERS),
                "prefixes": [str(p) for p in REJECT_PREFIXES],
            },
        }

    if name == "project_status":
        state = load_state()
        return {"ok": True, "active": state}

    if name == "project_clear":
        previous = load_state()
        save_state(None)
        reconnect = reconnect_router_clients()
        if not reconnect.get("ok"):
            save_state(previous)
            rollback_reconnect = reconnect_router_clients()
            return {
                "ok": False,
                "error": "project_scoped_reconnect_failed",
                "active": previous,
                "cleared_at": _now(),
                "project_scoped_reconnect": reconnect,
                "rollback_reconnect": rollback_reconnect,
            }
        return {
            "ok": True,
            "active": None,
            "cleared_at": _now(),
            "project_scoped_reconnect": reconnect,
        }

    if name == "project_activate":
        path = arguments.get("path")
        pid = arguments.get("id")
        if not path and not pid:
            return {"ok": False, "error": "Provide path or id"}
        match = _match_project(projects, path, pid)
        if not match:
            return {
                "ok": False,
                "error": "Project not in registered allow-list (or rejected by Swarm/agentmemory policy)",
                "requested": {"path": path, "id": pid},
            }
        reason = _rejected_path(Path(match["path"]))
        if reason:
            return {"ok": False, "error": reason}
        previous = load_state()
        state = {
            "id": match["id"],
            "name": match["name"],
            "path": match["path"],
            "activated_at": _now(),
            "activated_by": SERVER_NAME,
        }
        save_state(state)
        reconnect = reconnect_router_clients()
        if not reconnect.get("ok"):
            save_state(previous)
            rollback_reconnect = reconnect_router_clients()
            return {
                "ok": False,
                "error": "project_scoped_reconnect_failed",
                "active": previous,
                "requested": state,
                "project_scoped_reconnect": reconnect,
                "rollback_reconnect": rollback_reconnect,
            }
        return {
            "ok": True,
            "active": state,
            "project_scoped_reconnect": reconnect,
        }

    return {"ok": False, "error": f"Unknown tool: {name}"}


def handle_initialize(params: dict[str, Any] | None) -> dict[str, Any]:
    requested = str((params or {}).get("protocolVersion") or PROTOCOL_VERSION)
    version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
    return {
        "protocolVersion": version,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


def handle_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications have no id
    if req_id is None and method and method.startswith("notifications/"):
        return None

    try:
        if method == "initialize":
            result = handle_initialize(params)
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_defs()}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            payload = call_tool(tool_name, arguments)
            result = {
                "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
                "structuredContent": payload,
                "isError": not payload.get("ok", True),
            }
        elif method == "resources/list":
            result = {"resources": []}
        elif method == "prompts/list":
            result = {"prompts": []}
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception as exc:  # noqa: BLE001
        _log(f"error: {exc}")
        _log(traceback.format_exc())
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": "internal error (sanitized)"},
        }


def main() -> int:
    _log(f"starting stdio NDJSON server cwd={os.getcwd()}")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        response = handle_request(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

