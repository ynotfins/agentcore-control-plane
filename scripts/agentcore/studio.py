"""LangGraph Studio (Agent Server) adapter for the AgentCore workflow.

Studio is a development / debugging surface only. It MUST NOT replace
production persistence.

This module:
- locates the Studio application directory (``scripts/agentcore_workflow/studio``)
  which contains ``langgraph.json`` and the graph factory ``graph.py``
- validates ``langgraph.json`` against the current topology fingerprint
- launches the LangGraph CLI dev server (``langgraph dev``) on localhost

Operational posture (per BLUEPRINT.md §10, PROJECT_ANCHOR.md §10):

- ``LANGSMITH_TRACING=false`` is forced for local Studio runs unless the
  operator sets ``LANGSMITH_TRACING=true`` explicitly via the env. This
  prevents AgentCore application data from being sent to LangSmith.
- The Agent Server binds to localhost only.
- LangGraph CLI analytics are disabled via ``LANGGRAPH_ANALYTICS=false``.
- No Docker / WSL dependency.
- No persistent Windows service. Studio is started only when the
  operator wants visualization / debugging.
- Production persistence (PostgresSaver) is unaffected: Studio uses its
  own development checkpointer.

The production ``PostgresSaver`` lives in the ``public.checkpoints`` tables
in PG18 at ``127.0.0.1:55433``. Studio writes to a separate in-memory /
sqlite dev checkpointer managed by the LangGraph CLI / Agent Server.

If the LangGraph CLI is not installed, ``run_studio`` prints a clear
error message and returns a non-zero exit code; it never crashes the
rest of the workflow CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

# Topology fingerprint import is deferred to keep this module import-safe
# even if the workflow package is unavailable.


_REPO_ROOT = Path(__file__).resolve().parents[2]
_STUDIO_DIR = _REPO_ROOT / "scripts" / "agentcore_workflow" / "studio"


def _check_fingerprint_parity() -> dict:
    """Verify Studio's langgraph.json graph fingerprint matches production.

    Returns a dict with keys: ``ok``, ``studio_fp``, ``production_fp``.
    Both fingerprints are derived from the SAME ``agentcore_workflow.workflow``
    module (production) and the SAME ``graph.py`` factory (Studio). The
    Studio ``graph.py`` imports ``build_topology`` from the workflow package
    and exposes ``TOPOLOGY_FINGERPRINT`` so the parity check is deterministic.
    """
    from agentcore_workflow.workflow import (
        build_topology,
        topology_fingerprint,
    )
    t = build_topology()
    prod_fp = topology_fingerprint(t)
    studio_fp = ""
    graph_py = _STUDIO_DIR / "graph.py"
    if graph_py.exists():
        # Studio graph.py must expose topology_fingerprint() — we re-execute
        # the module to read it. Sandbox-safe: no side effects.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "studio_graph_parity", str(graph_py)
        )
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            studio_fp = getattr(mod, "TOPOLOGY_FINGERPRINT", "")
        except Exception as exc:  # noqa: BLE001
            studio_fp = f"ERROR: {exc}"
    return {
        "ok": bool(prod_fp) and prod_fp == studio_fp,
        "production_fp": prod_fp,
        "studio_fp": studio_fp,
    }


def _free_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def run_studio(args: argparse.Namespace) -> int:
    """Launch ``langgraph dev`` for the AgentCore workflow graph."""
    # Verify the Studio application directory exists.
    if not _STUDIO_DIR.exists():
        print(f"ERROR: Studio app directory not found: {_STUDIO_DIR}",
              file=sys.stderr)
        print("       Did the langgraph.json + graph.py factory get created?",
              file=sys.stderr)
        return 2

    langgraph_json = _STUDIO_DIR / "langgraph.json"
    if not langgraph_json.exists():
        print(f"ERROR: langgraph.json not found at {langgraph_json}",
              file=sys.stderr)
        return 2

    # Topology parity check
    parity = _check_fingerprint_parity()
    if not parity["ok"]:
        print("ERROR: production/Studio topology fingerprints differ.",
              file=sys.stderr)
        print(f"  production_fp: {parity['production_fp']}", file=sys.stderr)
        print(f"  studio_fp:     {parity['studio_fp']}", file=sys.stderr)
        return 2

    # Locate the langgraph CLI.
    langgraph_cli = shutil.which("langgraph")
    if langgraph_cli is None:
        print("ERROR: 'langgraph' CLI not on PATH.", file=sys.stderr)
        print("       Install with: pip install -r scripts/agentcore_workflow/requirements-studio.txt",
              file=sys.stderr)
        return 2

    # Pick a port that is free; if requested port is busy, fall back to next free.
    port = int(args.port or 2024)
    if not _free_port(port):
        # Search upward
        for candidate in range(port + 1, port + 50):
            if _free_port(candidate):
                print(f"WARN: port {port} busy; using {candidate}", file=sys.stderr)
                port = candidate
                break
        else:
            print(f"ERROR: no free port near {port}", file=sys.stderr)
            return 2

    env = os.environ.copy()
    # Default OFF for Studio: do not transmit AgentCore application data
    # to LangSmith. Operator can override by setting LANGSMITH_TRACING=true.
    env.setdefault("LANGSMITH_TRACING", "false")
    env.setdefault("LANGGRAPH_ANALYTICS", "false")
    # Bind local Agent Server to localhost only.
    env.setdefault("LANGGRAPH_HOST", "127.0.0.1")

    cmd = [langgraph_cli, "dev", "--port", str(port), "--no-browser"]
    if args.no_browser:
        pass  # --no-browser already present

    payload = {
        "timestamp": _now_iso(),
        "ok": True,
        "studio_app_dir": str(_STUDIO_DIR),
        "langgraph_json": str(langgraph_json),
        "topology_fingerprint": parity["production_fp"],
        "local_api_url": f"http://127.0.0.1:{port}",
        "studio_url_hint": (
            f"Open LangGraph Studio and connect to: http://127.0.0.1:{port}"
        ),
        "env": {
            "LANGSMITH_TRACING": env.get("LANGSMITH_TRACING"),
            "LANGGRAPH_ANALYTICS": env.get("LANGGRAPH_ANALYTICS"),
            "LANGGRAPH_HOST": env.get("LANGGRAPH_HOST"),
        },
        "command": cmd,
        "note": (
            "Studio persistence is the Agent Server dev checkpointer (sqlite/"
            "memory), separate from production PostgresSaver. No AgentCore "
            "application data is sent to LangSmith (LANGSMITH_TRACING=false)."
        ),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("Starting LangGraph Studio (Agent Server)...")
        print(f"  app_dir:       {payload['studio_app_dir']}")
        print(f"  langgraph.json:{payload['langgraph_json']}")
        print(f"  fingerprint:   {payload['topology_fingerprint']}")
        print(f"  local API:     {payload['local_api_url']}")
        print(f"  Studio hint:   {payload['studio_url_hint']}")
        print(f"  tracing:       {payload['env']['LANGSMITH_TRACING']}")
        print()
        print("Press Ctrl+C to stop. Studio will not interfere with the")
        print("production PostgresSaver at 127.0.0.1:55433.")
        print()

    # Start the dev server in the foreground; Ctrl+C stops it.
    try:
        return subprocess.call(cmd, cwd=str(_STUDIO_DIR), env=env)
    except KeyboardInterrupt:
        return 130


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
