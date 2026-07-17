#!/usr/bin/env python3
"""AgentCore project router MCP server (stdio JSON-RPC).

Tools: project_list, project_activate, project_status, project_clear
State: H:\\AgentRuntime\\bifrost\\state\\active-project.json
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SERVER_NAME = "agentcore-project-router"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}

STATE_PATH = Path(r"H:\AgentRuntime\bifrost\state\active-project.json")
GITHUB_ROOT = Path(r"D:\github")
ALWAYS_ALLOW = [
    Path(r"D:\github\agentcore-control-plane"),
    Path(r"D:\github\memory-context-database"),
]
REJECT_MARKERS = (
    "swarmrecall",
    "swarmvault",
    "agentswarm",
    "swarmclaw",
)
REJECT_PREFIXES = (
    Path(r"F:\AgentCore\agentmemory"),
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
    with STATE_PATH.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "project_list",
            "description": "List registered project worktrees allowed for AgentCore project-scoped MCP servers.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "project_activate",
            "description": "Activate a registered project by path or id for project-scoped upstream MCP servers.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute project path"},
                    "id": {"type": "string", "description": "Project folder name / id"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "project_status",
            "description": "Show the currently active project, if any.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "project_clear",
            "description": "Clear the active project selection.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
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
        save_state(None)
        return {"ok": True, "active": None, "cleared_at": _now()}

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
        state = {
            "id": match["id"],
            "name": match["name"],
            "path": match["path"],
            "activated_at": _now(),
            "activated_by": SERVER_NAME,
        }
        save_state(state)
        return {"ok": True, "active": state}

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
