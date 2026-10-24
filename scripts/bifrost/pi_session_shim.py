#!/usr/bin/env python3
"""Pi HTTP Session Shim for AgentCore Bifrost Gateway.

Provides a multi-IDE, concurrent-safe HTTP MCP endpoint on 127.0.0.1:18091/mcp.
Bifrost connects to this shim as an HTTP MCP client with allowed_extra_headers.

The shim binds caller headers (x-agentcore-project, x-bf-session-id, x-session-id)
or reserved tool args (agentcore_project / project_key) to enrolled project roots from
contracts/agentcore-project-enrollment.json (default-deny; Swarm refuse). Per enrolled
project it starts an isolated Pi mcp-bridge child with cwd=enrolled primary path.
Caller cwd is validated then overwritten to that enrolled root. Missing or unknown
identity returns PROJECT_NOT_ENROLLED. Never sticky STDIO and never uses Bifrost
runtime working directory as a project root.

Authority: AUTH-2026-10-23-PI-BIFROST-HTTP-SHIM
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

from bifrost.session_identity import (
    ERROR_NOT_ENROLLED,
    EnrollmentRegistry,
    load_enrollment_contract,
    resolve_request_identity,
    sanitize_tool_args_for_upstream,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENROLLMENT_CONTRACT = REPO_ROOT / "contracts" / "agentcore-project-enrollment.json"

DEFAULT_PORT = int(os.environ.get("AGENTCORE_PI_SHIM_PORT", "18091"))
DEFAULT_HOST = os.environ.get("AGENTCORE_PI_SHIM_HOST", "127.0.0.1")

NODE_EXE = os.environ.get(
    "AGENTCORE_PI_NODE_EXE",
    r"C:\Program Files\nodejs\node.exe" if sys.platform == "win32" else "node",
)
PI_BRIDGE = os.environ.get(
    "AGENTCORE_PI_BRIDGE",
    r"C:\Users\ynotf\.pi\agent\mcp-bridge\server.mjs"
    if sys.platform == "win32"
    else str(Path.home() / ".pi" / "agent" / "mcp-bridge" / "server.mjs"),
)

ERROR_CWD_OUT_OF_ENROLLMENT = "cwd_out_of_enrollment"

FORBIDDEN_WRITE_PREFIXES = (
    r"f:\postgresql18",
    r"f:\agentcore",
    r"h:",
    r"e:\agentcore",
    r"e:\swarm",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [pi-shim] %(message)s",
)
logger = logging.getLogger("pi_session_shim")

def _normalize_root(raw):
    return str(Path(raw).resolve()).lower()


def is_forbidden_write_root(candidate):
    try:
        norm = _normalize_root(str(candidate))
    except (OSError, ValueError):
        return True
    for prefix in FORBIDDEN_WRITE_PREFIXES:
        if prefix == r"h:":
            if norm.startswith("h:"):
                return True
            continue
        if norm == prefix or norm.startswith(prefix + os.sep) or norm.startswith(prefix + "\\"):
            return True
    return False


def bind_enrolled_cwd(tool_args, enrolled_path):
    enrolled = enrolled_path.resolve()
    if is_forbidden_write_root(enrolled):
        return None, ERROR_CWD_OUT_OF_ENROLLMENT
    enrolled_norm = str(enrolled).lower()
    raw = tool_args.get("cwd")
    if isinstance(raw, str) and raw.strip():
        try:
            requested = Path(raw.strip()).resolve()
        except (OSError, ValueError):
            return None, ERROR_CWD_OUT_OF_ENROLLMENT
        requested_norm = str(requested).lower()
        if is_forbidden_write_root(requested):
            return None, ERROR_CWD_OUT_OF_ENROLLMENT
        if requested_norm != enrolled_norm and not requested_norm.startswith(enrolled_norm + os.sep):
            return None, ERROR_CWD_OUT_OF_ENROLLMENT
    bound = dict(tool_args)
    bound["cwd"] = str(enrolled)
    return bound, None


def prepare_pi_tool_args(tool_args, enrolled_path):
    sanitized = sanitize_tool_args_for_upstream(tool_args, enrolled_path)
    return bind_enrolled_cwd(sanitized, enrolled_path)

class PiProjectRegistry:
    def __init__(self, contract=None):
        self._inner = EnrollmentRegistry(contract=contract or load_enrollment_contract())

    def is_swarm_refused(self, candidate):
        return self._inner.is_swarm_refused(candidate)

    def resolve_project(self, project_key=None, candidate_path=None):
        result = self._inner.resolve(project_key=project_key, candidate_path=candidate_path)
        return result.project_key, result.primary_path, result.error


class PiChildProcess:
    def __init__(self, project_key, project_path):
        self.project_key = project_key
        self.project_path = project_path
        self.proc = None
        self._lock = threading.Lock()
        self._response_queues = {}
        self._reader_thread = None
        self._running = False
        self._initialized = False

    def start(self):
        with self._lock:
            if self.proc and self.proc.poll() is None:
                return True
            cmd = [NODE_EXE, PI_BRIDGE]
            logger.info("Starting Pi child for %s at %s: %s", self.project_key, self.project_path, " ".join(cmd))
            try:
                env = dict(os.environ)
                self.proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_path),
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
            except Exception as exc:
                logger.error("Failed to start Pi child for %s: %s", self.project_key, exc)
                self.proc = None
                return False
            self._running = True
            self._initialized = False
            self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self._reader_thread.start()
            threading.Thread(target=self._drain_stderr, daemon=True).start()
            return True

    def _ensure_mcp_initialized(self, timeout_sec=30.0):
        if self._initialized:
            return None
        init_payload = {
            "jsonrpc": "2.0",
            "id": "pi-init-%s-%s" % (self.project_key, int(time.time() * 1000)),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "agentcore-pi-session-shim", "version": "1.0.0"},
            },
        }
        init_resp = self.call_jsonrpc(init_payload, timeout_sec=timeout_sec, _internal=True)
        if "error" in init_resp:
            return init_resp
        self.call_jsonrpc({"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout_sec=timeout_sec, _internal=True)
        self._initialized = True
        return None

    def call_jsonrpc(self, payload, timeout_sec=30.0, _internal=False):
        msg_id = payload.get("id")
        if not self.start():
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": "Pi process failed to start for project %s" % self.project_key}}
        method = str(payload.get("method") or "")
        if not _internal and method not in ("initialize", "notifications/initialized"):
            init_err = self._ensure_mcp_initialized(timeout_sec=timeout_sec)
            if init_err is not None:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": "Pi child MCP initialize failed: %s" % ((init_err.get("error") or {}).get("message") or init_err)}}
        q = queue.Queue(maxsize=1)
        if msg_id is not None:
            self._response_queues[msg_id] = q
        try:
            line = json.dumps(payload) + "\n"
            with self._lock:
                if not self.proc or self.proc.stdin is None or self.proc.poll() is not None:
                    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": "Pi child terminated unexpectedly"}}
                self.proc.stdin.write(line)
                self.proc.stdin.flush()
            if msg_id is None:
                return {"jsonrpc": "2.0"}
            return q.get(timeout=timeout_sec)
        except queue.Empty:
            logger.warning("Timeout waiting for Pi child response (id=%s) on %s", msg_id, self.project_key)
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": "Timeout waiting for Pi (%ss)" % timeout_sec}}
        except Exception as exc:
            logger.error("Error communicating with Pi child %s: %s", self.project_key, exc)
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(exc)}}
        finally:
            if msg_id is not None:
                self._response_queues.pop(msg_id, None)

    def stop(self):
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
            self._initialized = False

    def _read_stdout(self):
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
                logger.debug("Error handling Pi stdout line: %s", exc)
        self._running = False

    def _drain_stderr(self):
        if not self.proc or not self.proc.stderr:
            return
        for line in self.proc.stderr:
            clean = line.strip()
            if clean:
                logger.debug("[%s:stderr] %s", self.project_key, clean)

CACHED_PI_TOOLS = [
    {"name": "pi_list_agents", "description": "List available Pi parallel subagent roles on this workstation.", "inputSchema": {"type": "object", "properties": {"cwd": {"type": "string"}}}},
    {"name": "pi_run_agent", "description": "Run one Pi subagent role against an enrolled project cwd.", "inputSchema": {"type": "object", "properties": {"agent": {"type": "string"}, "prompt": {"type": "string"}, "cwd": {"type": "string"}}, "required": ["agent", "prompt"]}},
    {"name": "pi_parallel_agents", "description": "Run several Pi subagents in parallel against one enrolled project.", "inputSchema": {"type": "object", "properties": {"agents": {"type": "array", "items": {"type": "string"}}, "prompt": {"type": "string"}, "cwd": {"type": "string"}}, "required": ["agents", "prompt"]}},
    {"name": "pi_chain_workflow", "description": "Run a sequenced Pi workflow on one enrolled project.", "inputSchema": {"type": "object", "properties": {"steps": {"type": "array"}, "cwd": {"type": "string"}}, "required": ["steps"]}},
]


class PiShimManager:
    def __init__(self):
        self.registry = PiProjectRegistry()
        self.session_bindings = {}
        self.children = {}
        self._lock = threading.Lock()

    def bind_session(self, session_id, project_key):
        pkey, _, err = self.registry.resolve_project(project_key=project_key)
        if err or not pkey:
            return False, err or ERROR_NOT_ENROLLED
        with self._lock:
            self.session_bindings[session_id] = pkey
        return True, pkey

    def get_child_for_request(self, headers, args):
        resolved = resolve_request_identity(self.registry._inner, headers, args=args, session_bindings=self.session_bindings)
        if not resolved.ok:
            return None, resolved.error or ERROR_NOT_ENROLLED
        pkey = resolved.project_key
        primary_path = resolved.primary_path
        if is_forbidden_write_root(primary_path):
            return None, ERROR_CWD_OUT_OF_ENROLLMENT
        with self._lock:
            if pkey not in self.children:
                self.children[pkey] = PiChildProcess(pkey, primary_path)
            return self.children[pkey], None

    def stop_all(self):
        with self._lock:
            for child in self.children.values():
                child.stop()
            self.children.clear()


SHIM_MANAGER = PiShimManager()

class PiShimHTTPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        logger.debug("%s - %s", self.client_address[0], format % args)

    def do_GET(self):
        if self.path in ("/health", "/status"):
            status_data = {
                "status": "healthy",
                "service": "pi-session-shim",
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

    def do_POST(self):
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
        if self.path in ("/mcp", "/"):
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception as exc:
                self._send_json(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error: %s" % exc}})
                return
            self._send_json(200, self._handle_mcp_request(payload))
            return
        self.send_response(404)
        self.end_headers()

    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_mcp_request(self, payload):
        msg_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params") or {}
        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "pi-session-shim", "version": "1.4.0"}}}
        if method == "notifications/initialized":
            return {"jsonrpc": "2.0"}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": CACHED_PI_TOOLS}}
        if method == "tools/call":
            tool_args = params.get("arguments") or {}
            headers_map = {k.lower(): v for k, v in self.headers.items()}
            child, err = SHIM_MANAGER.get_child_for_request(headers_map, tool_args)
            if err:
                if "swarm" in err:
                    code = -32001
                elif err == ERROR_CWD_OUT_OF_ENROLLMENT:
                    code = -32003
                else:
                    code = -32002
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": "Pi session routing error: %s" % err}}
            if not child:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32002, "message": "Failed to resolve Pi child for project"}}
            prepared, cwd_err = prepare_pi_tool_args(tool_args, child.project_path)
            if cwd_err or prepared is None:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32003, "message": "Pi session routing error: %s" % (cwd_err or ERROR_CWD_OUT_OF_ENROLLMENT)}}
            forward_payload = dict(payload)
            forward_params = dict(params)
            forward_params["arguments"] = prepared
            forward_payload["params"] = forward_params
            return child.call_jsonrpc(forward_payload)
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method '%s' not implemented by Pi shim" % method}}


def run_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    server = ThreadingHTTPServer((host, port), PiShimHTTPHandler)
    logger.info("Pi HTTP Session Shim listening on http://%s:%s/mcp", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping Pi HTTP Session Shim...")
    finally:
        server.server_close()
        SHIM_MANAGER.stop_all()


def main():
    parser = argparse.ArgumentParser(description="Pi HTTP Session Shim for AgentCore Bifrost")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
