#!/usr/bin/env python3
"""agent-dispatch: loopback HTTP MCP server (JSON-RPC over POST /mcp) for Bifrost.

Six tools front every local autonomous agent. Stdlib only; idle = one blocked
accept() thread. Authority: governance/proposals/2026-11-19-agent-dispatch.md.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from bifrost.session_identity import extract_project_header  # noqa: E402

from agent_dispatch import paperclip  # noqa: E402
from agent_dispatch.jobs import JobManager  # noqa: E402
from agent_dispatch.policy import WorkdirError  # noqa: E402

VERSION = "0.1.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = int(os.environ.get("AGENTCORE_DISPATCH_PORT", "18092"))
MAX_BODY = 256 * 1024

log = logging.getLogger("agent_dispatch")

_JOB = {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}
_TASK_PROPS = {
    "agent": {"type": "string", "description": "Name from agents_list, e.g. pi, openhands, opencode, codex, paperclip/<name>."},
    "task": {"type": "string", "description": "Self-contained instructions."},
    "workdir": {"type": "string", "description": "Enrolled repo or D:\\agentcore-worktrees path. Omit for a scratch dir."},
    "budget": {"type": "integer", "description": "Wall-clock minutes (capped per agent)."},
    "model": {"type": "string", "description": "Optional OmniRoute model; default deepseek/deepseek-v4.1-flash-1017."},
}
TOOLS = [
    {"name": "agents_list", "description": "List local sub-agents, what each is good at, and whether it is runnable.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "agent_run", "description": "Start one sub-agent job asynchronously. Returns job_id.",
     "inputSchema": {"type": "object", "properties": _TASK_PROPS, "required": ["agent", "task"]}},
    {"name": "agents_parallel", "description": "Start up to 8 sub-agent jobs at once (max 4 run concurrently). Returns one job_id.",
     "inputSchema": {"type": "object", "properties": {"tasks": {"type": "array", "items": {
         "type": "object", "properties": _TASK_PROPS, "required": ["agent", "task"]}}}, "required": ["tasks"]}},
    {"name": "job_status", "description": "Status, model, tokens/cost and timing for a job.", "inputSchema": _JOB},
    {"name": "job_result", "description": "Job outcome: <=300-word summary (default) or detail=full with log paths.",
     "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"},
                                                       "detail": {"type": "string", "enum": ["summary", "full"]}},
                     "required": ["job_id"]}},
    {"name": "job_cancel", "description": "Cancel a running or queued job (parallel jobs cancel all children).", "inputSchema": _JOB},
]

MANAGER: JobManager | None = None


def call_tool(name: str, args: dict, headers: dict) -> dict:
    caller = extract_project_header(headers)
    m = MANAGER
    if name == "agents_list":
        return {"agents": m.list_agents()}
    if name == "agent_run":
        job = m.submit(args.get("agent", ""), args.get("task", ""), args.get("workdir"), args.get("budget"),
                       args.get("model"), caller_project=caller)
        return {k: job.get(k) for k in ("job_id", "agent", "status", "model", "workdir", "paperclip_issue")}
    if name == "agents_parallel":
        return m.submit_parallel(args.get("tasks") or [], caller_project=caller)
    if name == "job_status":
        return m.status(str(args.get("job_id", "")))
    if name == "job_result":
        return m.result(str(args.get("job_id", "")), "full" if args.get("detail") == "full" else "summary")
    if name == "job_cancel":
        return m.cancel(str(args.get("job_id", "")))
    raise UnknownTool(name)


def handle(payload: dict, headers: dict) -> dict | None:
    mid, method, params = payload.get("id"), payload.get("method"), payload.get("params") or {}
    if method and method.startswith("notifications/"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": params.get("protocolVersion") or "2025-06-18",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "agent-dispatch", "version": VERSION}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        try:
            data, is_error = call_tool(name, args, headers), False
        except UnknownTool:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool: {name}"}}
        except KeyError as exc:
            data, is_error = {"error": str(exc).strip("'\"")}, True
        except (ValueError, WorkdirError, paperclip.PaperclipError) as exc:
            data, is_error = {"error": str(exc)}, True
        except Exception as exc:  # noqa: BLE001 - tool boundary returns an MCP error, never crashes the server
            log.exception("tool %s failed", name)
            data, is_error = {"error": f"internal: {type(exc).__name__}"}, True
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "content": [{"type": "text", "text": json.dumps(data, default=str)}],
            "structuredContent": data, "isError": is_error}}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}


class UnknownTool(Exception):
    pass


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        log.debug("%s %s", self.client_address[0], fmt % args)

    def _send(self, status: int, data=None) -> None:
        body = b"" if data is None else json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        if data is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/health", "/status"):
            self._send(200, {"status": "healthy", "service": "agent-dispatch", "version": VERSION,
                             "active_jobs": len(MANAGER.procs)})
        else:
            self._send(405 if self.path == "/mcp" else 404, {"error": "use POST /mcp"})

    def do_POST(self):
        if self.path not in ("/mcp", "/"):
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0 or length > MAX_BODY:
            return self._send(413 if length > MAX_BODY else 400, {"error": "bad body size"})
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._send(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"parse error: {exc}"}})
        headers = {k.lower(): v for k, v in self.headers.items()}
        if isinstance(payload, list):
            out = [r for r in (handle(p, headers) for p in payload if isinstance(p, dict)) if r is not None]
            return self._send(200, out) if out else self._send(202)
        res = handle(payload, headers) if isinstance(payload, dict) else None
        return self._send(200, res) if res is not None else self._send(202)


def preflight_inference(timeout: float = 3.0) -> str:
    """Fail loudly when the OmniRoute endpoint is unreachable.

    Every non-Codex backend sends model traffic to the loopback OmniRoute. Starting
    the dispatcher with that endpoint down only burns runs, so refuse to serve.
    """
    import urllib.error
    import urllib.request

    url = os.environ.get("AGENTCORE_DISPATCH_OMNIROUTE_HEALTH", "http://127.0.0.1:20128/v1/models")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return f"omniroute reachable ({r.status})"
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return f"omniroute reachable ({exc.code}: auth required, endpoint alive)"
        raise SystemExit(f"agent-dispatch preflight failed: {url} -> HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001 — any transport failure is fatal here
        raise SystemExit(f"agent-dispatch preflight failed: OmniRoute unreachable at {url} ({exc})")


def main() -> int:
    global MANAGER
    ap = argparse.ArgumentParser(description="AgentCore agent-dispatch MCP server")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--skip-preflight", action="store_true", help="start even if OmniRoute is down (debug only)")
    a = ap.parse_args()
    if a.host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("agent-dispatch is loopback-only")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [agent-dispatch] %(message)s")
    if not a.skip_preflight:
        log.info(preflight_inference())
    MANAGER = JobManager()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    srv.daemon_threads = True
    log.info("listening on http://%s:%s/mcp", a.host, a.port)
    try:
        srv.serve_forever(poll_interval=3600)
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
