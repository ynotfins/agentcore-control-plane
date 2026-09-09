#!/usr/bin/env python3
"""Serena HTTP Session Shim for AgentCore Bifrost Gateway.

Provides a multi-IDE, concurrent-safe HTTP MCP endpoint on 127.0.0.1:18090/mcp.
Bifrost connects to this shim as an HTTP MCP client with allowed_extra_headers.

The shim binds caller headers (x-agentcore-project, x-bf-session-id, x-session-id)
to enrolled project roots from contracts/agentcore-project-enrollment.json (default-deny;
Swarm refuse). Missing or unknown identity returns PROJECT_NOT_ENROLLED — never falls
back to agentcore-control-plane. For each enrolled project, an isolated Serena child
process is spawned with `--project <enrolled_path>`, preventing cross-project symbol
or file leakage.

Authority: docs/adr/ADR-2026-09-09-serena-http-session-shim.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from bifrost.session_identity import (  # noqa: E402
    ERROR_NOT_ENROLLED,
    EnrollmentRegistry,
    load_enrollment_contract,
    resolve_request_identity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENROLLMENT_CONTRACT = REPO_ROOT / "contracts" / "agentcore-project-enrollment.json"

DEFAULT_PORT = int(os.environ.get("AGENTCORE_SERENA_SHIM_PORT", "18090"))
DEFAULT_HOST = os.environ.get("AGENTCORE_SERENA_SHIM_HOST", "127.0.0.1")

SERENA_EXE = os.environ.get(
    "SERENA_EXE",
    r"C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe"
    if sys.platform == "win32"
    else "serena",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [serena-shim] %(message)s",
)
logger = logging.getLogger("serena_session_shim")


class SerenaProjectRegistry:
    """Default-deny project resolver (wrapper over shared EnrollmentRegistry)."""

    def __init__(self, contract: Optional[dict[str, Any]] = None):
        self._inner = EnrollmentRegistry(contract=contract or load_enrollment_contract())

    def is_swarm_refused(self, candidate: str) -> bool:
        return self._inner.is_swarm_refused(candidate)

    def resolve_project(
        self,
        project_key: Optional[str] = None,
        candidate_path: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[Path], Optional[str]]:
        """Returns (project_key, primary_path, error_reason). Never falls back."""
        result = self._inner.resolve(
            project_key=project_key, candidate_path=candidate_path
        )
        return result.project_key, result.primary_path, result.error


class SerenaChildProcess:
    """Manages an isolated Serena MCP subprocess running in stdio mode for a single project."""

    def __init__(self, project_key: str, project_path: Path):
        self.project_key = project_key
        self.project_path = project_path
        self.proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._response_queues: dict[Any, queue.Queue] = {}
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._initialized = False

    def start(self) -> bool:
        with self._lock:
            if self.proc and self.proc.poll() is None:
                return True

            serena_bin = SERENA_EXE
            if not Path(serena_bin).exists() and not sys.platform.startswith("win"):
                serena_bin = "serena"

            cmd = [
                serena_bin,
                "start-mcp-server",
                "--transport",
                "stdio",
                "--context",
                "ide",
                "--project",
                str(self.project_path),
            ]
            logger.info(f"Starting Serena child for '{self.project_key}' at {self.project_path}: {' '.join(cmd)}")
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_path),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    bufsize=1,
                )
                self._running = True
                self._reader_thread = threading.Thread(
                    target=self._read_stdout,
                    daemon=True,
                    name=f"serena-reader-{self.project_key}",
                )
                self._reader_thread.start()
                threading.Thread(
                    target=self._drain_stderr,
                    daemon=True,
                    name=f"serena-stderr-{self.project_key}",
                ).start()
                return True
            except Exception as exc:
                logger.error(f"Failed to spawn Serena child for '{self.project_key}': {exc}")
                self._running = False
                self.proc = None
                return False

    def _read_stdout(self) -> None:
        if not self.proc or not self.proc.stdout:
            return
        for line in self.proc.stdout:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                msg = json.loads(line_str)
                msg_id = msg.get("id")
                if msg_id is not None and msg_id in self._response_queues:
                    self._response_queues[msg_id].put(msg)
            except json.JSONDecodeError:
                pass
            except Exception as exc:
                logger.debug(f"Error handling Serena stdout line: {exc}")
        self._running = False

    def _drain_stderr(self) -> None:
        if not self.proc or not self.proc.stderr:
            return
        for line in self.proc.stderr:
            clean = line.strip()
            if clean:
                logger.debug(f"[{self.project_key}:stderr] {clean}")

    def call_jsonrpc(self, payload: dict[str, Any], timeout_sec: float = 30.0) -> dict[str, Any]:
        msg_id = payload.get("id")
        if not self.start():
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Serena process failed to start for project {self.project_key}"},
            }

        q: queue.Queue = queue.Queue(maxsize=1)
        if msg_id is not None:
            self._response_queues[msg_id] = q

        try:
            line = json.dumps(payload) + "\n"
            with self._lock:
                if not self.proc or self.proc.stdin is None or self.proc.poll() is not None:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32000, "message": "Serena child terminated unexpectedly"},
                    }
                self.proc.stdin.write(line)
                self.proc.stdin.flush()

            if msg_id is None:
                # Notification
                return {"jsonrpc": "2.0"}

            resp = q.get(timeout=timeout_sec)
            return resp
        except queue.Empty:
            logger.warning(f"Timeout waiting for Serena child response (id={msg_id}) on {self.project_key}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": f"Timeout waiting for Serena ({timeout_sec}s)"},
            }
        except Exception as exc:
            logger.error(f"Error communicating with Serena child {self.project_key}: {exc}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": str(exc)},
            }
        finally:
            if msg_id is not None:
                self._response_queues.pop(msg_id, None)

    def stop(self) -> None:
        with self._lock:
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.terminate()
                    self.proc.wait(timeout=3)
                except Exception:
                    try:
                        self.proc.kill()
                    except Exception:
                        pass
            self.proc = None
            self._running = False


# Embedded tool catalog matching Serena v1.5.4
CACHED_SERENA_TOOLS = [
    {
        "name": "replace_content",
        "description": "Replaces one or more occurrences of a given pattern in a file with new content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relative_path": {"type": "string", "description": "The relative path to the file."},
                "needle": {"type": "string", "description": "The string or regex pattern to search for."},
                "repl": {"type": "string", "description": "The replacement string."},
                "mode": {"type": "string", "enum": ["literal", "regex"], "description": "literal or regex"},
                "allow_multiple_occurrences": {"type": "boolean", "default": False},
            },
            "required": ["relative_path", "needle", "repl", "mode"],
        },
    },
    {
        "name": "replace_in_files",
        "description": "Replaces occurrences of a pattern across multiple files in ONE call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "needle": {"type": "string"},
                "repl": {"type": "string"},
                "mode": {"type": "string", "enum": ["literal", "regex"]},
                "relative_path": {"type": "string", "default": ""},
                "paths_include_glob": {"type": "string", "default": ""},
                "paths_exclude_glob": {"type": "string", "default": ""},
                "dry_run": {"type": "boolean", "default": False},
            },
            "required": ["needle", "repl", "mode"],
        },
    },
    {
        "name": "replace_symbol_body",
        "description": "Replaces the body of the given symbol.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path": {"type": "string"},
                "relative_path": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["name_path", "relative_path", "body"],
        },
    },
    {
        "name": "insert_after_symbol",
        "description": "Use this to insert code after a class/method/function definition.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path": {"type": "string"},
                "relative_path": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["name_path", "relative_path", "body"],
        },
    },
    {
        "name": "insert_before_symbol",
        "description": "Inserts the given content before the beginning of the definition of the given symbol.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path": {"type": "string"},
                "relative_path": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["name_path", "relative_path", "body"],
        },
    },
    {
        "name": "search_for_pattern",
        "description": "Searches for a regex pattern across project files, returning whole matched lines.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "substring_pattern": {"type": "string"},
                "context_lines_before": {"type": "integer", "default": 0},
                "context_lines_after": {"type": "integer", "default": 0},
                "paths_include_glob": {"type": "string", "default": ""},
                "paths_exclude_glob": {"type": "string", "default": ""},
                "relative_path": {"type": "string", "default": ""},
                "restrict_search_to_code_files": {"type": "boolean", "default": False},
            },
            "required": ["substring_pattern"],
        },
    },
    {
        "name": "get_symbols_overview",
        "description": "Use this tool to get a high-level understanding of the code symbols in a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relative_path": {"type": "string"},
                "depth": {"type": "integer", "default": -1},
            },
            "required": ["relative_path"],
        },
    },
    {
        "name": "find_symbol",
        "description": "Retrieves information on all symbols/code entities based on name path pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path_pattern": {"type": "string"},
                "depth": {"type": "integer", "default": 0},
                "relative_path": {"type": "string", "default": ""},
                "include_body": {"type": "boolean", "default": False},
                "include_info": {"type": "boolean", "default": False},
                "substring_matching": {"type": "boolean", "default": False},
            },
            "required": ["name_path_pattern"],
        },
    },
    {
        "name": "find_referencing_symbols",
        "description": "Finds references to the symbol at the given name_path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path": {"type": "string"},
                "relative_path": {"type": "string"},
            },
            "required": ["name_path", "relative_path"],
        },
    },
    {
        "name": "find_implementations",
        "description": "Finds implementations of the symbol at the given name_path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path": {"type": "string"},
                "relative_path": {"type": "string"},
            },
            "required": ["name_path", "relative_path"],
        },
    },
    {
        "name": "find_declaration",
        "description": "Finds the declaration of a symbol via regex pattern match.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relative_path": {"type": "string"},
                "regex": {"type": "string"},
                "include_body": {"type": "boolean", "default": False},
            },
            "required": ["relative_path", "regex"],
        },
    },
    {
        "name": "get_diagnostics_for_file",
        "description": "Gets LSP diagnostics for a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relative_path": {"type": "string"},
                "min_severity": {"type": "integer", "default": 4},
            },
            "required": ["relative_path"],
        },
    },
    {
        "name": "rename_symbol",
        "description": "Renames the symbol with the given name_path to new_name throughout the entire codebase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path": {"type": "string"},
                "relative_path": {"type": "string"},
                "new_name": {"type": "string"},
            },
            "required": ["name_path", "relative_path", "new_name"],
        },
    },
    {
        "name": "safe_delete_symbol",
        "description": "Deletes the symbol if it is safe to do so.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_path_pattern": {"type": "string"},
                "relative_path": {"type": "string"},
            },
            "required": ["name_path_pattern", "relative_path"],
        },
    },
    {
        "name": "write_memory",
        "description": "Write information about this project for future tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_name": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["memory_name", "content"],
        },
    },
    {
        "name": "read_memory",
        "description": "Read project-specific memory content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_name": {"type": "string"},
            },
            "required": ["memory_name"],
        },
    },
    {
        "name": "list_memories",
        "description": "Lists available memories, optionally filtered by topic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "default": ""},
            },
        },
    },
    {
        "name": "delete_memory",
        "description": "Delete a project memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_name": {"type": "string"},
            },
            "required": ["memory_name"],
        },
    },
    {
        "name": "rename_memory",
        "description": "Rename or move a memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "old_name": {"type": "string"},
                "new_name": {"type": "string"},
            },
            "required": ["old_name", "new_name"],
        },
    },
    {
        "name": "edit_memory",
        "description": "Replace content matching a regex in a memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_name": {"type": "string"},
                "needle": {"type": "string"},
                "repl": {"type": "string"},
                "mode": {"type": "string", "enum": ["literal", "regex"]},
            },
            "required": ["memory_name", "needle", "repl", "mode"],
        },
    },
    {
        "name": "open_dashboard",
        "description": "Opens the Serena web dashboard.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class SerenaShimManager:
    """Singleton managing project resolution, session bindings, and child processes."""

    def __init__(self):
        self.registry = SerenaProjectRegistry()
        self.session_bindings: dict[str, str] = {}  # session_id -> project_key
        self.children: dict[str, SerenaChildProcess] = {}
        self._lock = threading.Lock()

    def bind_session(self, session_id: str, project_key: str) -> tuple[bool, str]:
        pkey, _, err = self.registry.resolve_project(project_key=project_key)
        if err or not pkey:
            return False, err or ERROR_NOT_ENROLLED
        with self._lock:
            self.session_bindings[session_id] = pkey
        return True, pkey

    def get_child_for_request(
        self,
        headers: dict[str, str],
        args: dict[str, Any],
    ) -> tuple[Optional[SerenaChildProcess], Optional[str]]:
        resolved = resolve_request_identity(
            self.registry._inner,
            headers,
            args=args,
            session_bindings=self.session_bindings,
        )
        if not resolved.ok:
            return None, resolved.error or ERROR_NOT_ENROLLED

        pkey = resolved.project_key
        primary_path = resolved.primary_path
        assert pkey is not None and primary_path is not None

        with self._lock:
            if pkey not in self.children:
                self.children[pkey] = SerenaChildProcess(pkey, primary_path)
            return self.children[pkey], None

    def stop_all(self) -> None:
        with self._lock:
            for child in self.children.values():
                child.stop()
            self.children.clear()


SHIM_MANAGER = SerenaShimManager()


class SerenaShimHTTPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug(f"{self.client_address[0]} - {format % args}")

    def do_GET(self) -> None:
        if self.path in ("/health", "/status"):
            status_data = {
                "status": "healthy",
                "service": "serena-session-shim",
                "active_children": list(SHIM_MANAGER.children.keys()),
                "session_bindings_count": len(SHIM_MANAGER.session_bindings),
            }
            body = json.dumps(status_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        if self.path == "/session/bind":
            try:
                data = json.loads(raw_body.decode("utf-8"))
                sid = data.get("session_id")
                pkey = data.get("project_key")
                if not sid or not pkey:
                    self._send_json(400, {"ok": False, "error": "session_id and project_key required"})
                    return
                ok, res = SHIM_MANAGER.bind_session(sid, pkey)
                if not ok:
                    self._send_json(403, {"ok": False, "error": res})
                    return
                self._send_json(200, {"ok": True, "session_id": sid, "project_key": res})
            except Exception as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            return

        # MCP Endpoint (/mcp or /)
        if self.path in ("/mcp", "/"):
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception as exc:
                self._send_json(
                    400,
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {exc}"}},
                )
                return

            resp = self._handle_mcp_request(payload)
            self._send_json(200, resp)
            return

        self.send_response(404)
        self.end_headers()

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_mcp_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        msg_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params") or {}

        # 1. PING: intercept immediately
        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        # 2. INITIALIZE: synthetic capabilities
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "serena-session-shim", "version": "1.5.4"},
                },
            }

        # 3. NOTIFICATIONS
        if method == "notifications/initialized":
            return {"jsonrpc": "2.0"}

        # 4. TOOLS/LIST: cached tool catalogue
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": CACHED_SERENA_TOOLS},
            }

        # 5. TOOLS/CALL: session/project bound child execution
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}

            # Map incoming headers
            headers_map = {k.lower(): v for k, v in self.headers.items()}

            child, err = SHIM_MANAGER.get_child_for_request(headers_map, tool_args)
            if err:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32001 if "swarm" in err else -32002,
                        "message": f"Serena session routing error: {err}",
                    },
                }

            if not child:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32002, "message": "Failed to resolve Serena child for project"},
                }

            # Forward tools/call to isolated child
            return child.call_jsonrpc(payload)

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method '{method}' not implemented by Serena shim"},
        }


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), SerenaShimHTTPHandler)
    logger.info(f"Serena HTTP Session Shim listening on http://{host}:{port}/mcp")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping Serena HTTP Session Shim...")
    finally:
        server.server_close()
        SHIM_MANAGER.stop_all()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serena HTTP Session Shim for AgentCore Bifrost")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to bind (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
