"""LangGraph Studio (Agent Server) adapter for the AgentCore workflow.

Studio is a development / debugging surface only. It MUST NOT replace
production persistence.

Option A launcher posture (complete non-browser work first):

- Force ``LANGSMITH_TRACING=false`` and ``LANGGRAPH_CLI_NO_ANALYTICS=1`` for
  the Studio process. Refuse launch when tracing is already truthy unless
  ``--allow-dangerous-langsmith-tracing`` is passed.
- Bind ``127.0.0.1`` only (never ``0.0.0.0`` / LAN). Default port ``2024``.
- Abort on port collision (do not silently rebind).
- Print sanitized local API + hosted Studio URLs only (no secrets).
- Foreground-owned process with child-tree cleanup on Ctrl+C / exit.
- Topology fingerprint parity abort before ``langgraph dev``.
- Missing ``LANGSMITH_API_KEY`` is **not** a global stop. Attempt anonymous /
  local Studio connection first. If the hosted Studio browser requires auth,
  emit gate code ``LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED`` and ask the
  operator to set User-scope env var **name** ``LANGSMITH_API_KEY`` only
  (never paste the value into chat; never print the value).

Chrome 142 Private Network Access diagnostic
--------------------------------------------
If ``http://127.0.0.1:<port>/docs`` works but hosted Studio fails to fetch the
local Agent Server, open site info for ``https://smith.langchain.com`` and
allow **Local network access**. Do **not** bind LAN / tunnel as the first fix.

This module:
- locates the Studio application directory (``scripts/agentcore_workflow/studio``)
- validates ``langgraph.json`` against the current topology fingerprint
- launches the LangGraph CLI dev server (``langgraph dev``) on localhost

Authority: BLUEPRINT.md §10, PROJECT_ANCHOR.md §10, AGENTS.md (no .env,
no printed secrets).
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parents[2]
_STUDIO_DIR = _REPO_ROOT / "scripts" / "agentcore_workflow" / "studio"

GATE_BROWSER_CREDENTIAL_REQUIRED = "LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED"
DEFAULT_PORT = 2024
LOCAL_HOST = "127.0.0.1"

_PNA_HINT = (
    "Chrome 142+ Private Network Access: if http://127.0.0.1:<port>/docs works "
    "but Studio fails to fetch -> allow Local network access on "
    "smith.langchain.com site info; do not bind LAN/tunnel as first fix."
)


def studio_app_dir() -> Path:
    return _STUDIO_DIR


def studio_url(port: int) -> str:
    """Hosted Studio deep-link with localhost Agent Server baseUrl."""
    return f"https://smith.langchain.com/studio/?baseUrl=http://{LOCAL_HOST}:{int(port)}"


def local_api_url(port: int) -> str:
    return f"http://{LOCAL_HOST}:{int(port)}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def port_is_free(port: int, host: str = LOCAL_HOST) -> bool:
    """Return True if ``host:port`` can be bound (collision check)."""
    if host not in {LOCAL_HOST, "localhost"}:
        raise ValueError(f"Studio bind host must be {LOCAL_HOST!r}, got {host!r}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((LOCAL_HOST, int(port)))
            return True
        except OSError:
            return False


def check_fingerprint_parity() -> dict[str, Any]:
    """Verify Studio graph fingerprint matches production topology.

    Returns keys: ``ok``, ``studio_fp``, ``production_fp``.
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
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "studio_graph_parity", str(graph_py)
        )
        if spec is None or spec.loader is None:
            studio_fp = "ERROR: cannot load studio graph.py"
        else:
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


def prepare_studio_env(
    *,
    allow_dangerous_langsmith_tracing: bool = False,
    extra: dict[str, str] | None = None,
) -> tuple[dict[str, str], str | None]:
    """Build Studio child env. Returns ``(env, refuse_reason_or_None)``.

    Forces tracing off and analytics off. Missing ``LANGSMITH_API_KEY`` is
    allowed (anonymous / local connection first).
    """
    env = os.environ.copy()
    existing_tracing = env.get("LANGSMITH_TRACING")
    if _is_truthy(existing_tracing) and not allow_dangerous_langsmith_tracing:
        return env, (
            "LANGSMITH_TRACING is truthy; refusing Studio launch. "
            "Unset it or pass --allow-dangerous-langsmith-tracing "
            "(sends AgentCore application data to LangSmith)."
        )

    if allow_dangerous_langsmith_tracing and _is_truthy(existing_tracing):
        env["LANGSMITH_TRACING"] = "true"
    else:
        env["LANGSMITH_TRACING"] = "false"

    env["LANGGRAPH_CLI_NO_ANALYTICS"] = "1"
    env["LANGGRAPH_ANALYTICS"] = "false"  # legacy alias still respected by some CLIs
    env["LANGGRAPH_HOST"] = LOCAL_HOST

    # Ensure scripts/ is importable for graph.py factory.
    scripts = str(_REPO_ROOT / "scripts")
    pp = env.get("PYTHONPATH", "")
    if scripts not in pp.split(os.pathsep):
        env["PYTHONPATH"] = scripts + (os.pathsep + pp if pp else "")

    if extra:
        env.update(extra)
    return env, None


def langsmith_api_key_present() -> bool:
    """Presence-only check; never returns or prints the value."""
    return bool((os.environ.get("LANGSMITH_API_KEY") or "").strip())


def emit_browser_credential_gate(stream=sys.stderr) -> None:
    """Emit the exact gate code + env var NAME only (never the secret)."""
    print(GATE_BROWSER_CREDENTIAL_REQUIRED, file=stream)
    print(
        "Hosted Studio browser auth may be required. Set Windows User-scope "
        "environment variable NAME: LANGSMITH_API_KEY "
        "(do not paste the value into chat; do not create a .env file).",
        file=stream,
    )


def build_langgraph_dev_cmd(
    *,
    port: int,
    host: str = LOCAL_HOST,
    no_reload: bool = False,
    langgraph_cli: str | None = None,
) -> list[str]:
    if host not in {LOCAL_HOST, "localhost"}:
        raise ValueError(
            f"Refusing non-localhost bind {host!r}; Studio must use {LOCAL_HOST}"
        )
    cli = langgraph_cli or shutil.which("langgraph")
    if not cli:
        raise FileNotFoundError("langgraph CLI not on PATH")
    cmd = [
        cli,
        "dev",
        "--host", LOCAL_HOST,
        "--port", str(int(port)),
        "--no-browser",
        "--config", "./langgraph.json",
    ]
    if no_reload:
        cmd.append("--no-reload")
    return cmd


def terminate_process_tree(proc: subprocess.Popen | None, *, grace_sec: float = 15.0) -> None:
    """Terminate a Studio child and its descendants (Windows-safe)."""
    if proc is None or proc.poll() is not None:
        return
    pid = proc.pid
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        else:
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, AttributeError):
                proc.terminate()
        try:
            proc.wait(timeout=grace_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


def run_studio(args: argparse.Namespace) -> int:
    """Launch ``langgraph dev`` for the AgentCore workflow graph (foreground)."""
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

    parity = check_fingerprint_parity()
    if not parity["ok"]:
        print("ERROR: production/Studio topology fingerprints differ.",
              file=sys.stderr)
        print(f"  production_fp: {parity['production_fp']}", file=sys.stderr)
        print(f"  studio_fp:     {parity['studio_fp']}", file=sys.stderr)
        return 2

    allow_dangerous = bool(
        getattr(args, "allow_dangerous_langsmith_tracing", False)
    )
    env, refuse = prepare_studio_env(
        allow_dangerous_langsmith_tracing=allow_dangerous,
    )
    if refuse:
        print(f"ERROR: {refuse}", file=sys.stderr)
        return 2

    langgraph_cli = shutil.which("langgraph")
    if langgraph_cli is None:
        print("ERROR: 'langgraph' CLI not on PATH.", file=sys.stderr)
        print(
            "       Install with: pip install -r "
            "scripts/agentcore_workflow/requirements-studio.txt",
            file=sys.stderr,
        )
        return 2

    port = int(getattr(args, "port", None) or DEFAULT_PORT)
    if not port_is_free(port):
        print(
            f"ERROR: port {port} already in use on {LOCAL_HOST} "
            "(collision). Stop the other listener or choose a free --port.",
            file=sys.stderr,
        )
        return 2

    try:
        cmd = build_langgraph_dev_cmd(port=port, langgraph_cli=langgraph_cli)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    api = local_api_url(port)
    studio = studio_url(port)
    key_present = langsmith_api_key_present()

    payload = {
        "timestamp": _now_iso(),
        "ok": True,
        "studio_app_dir": str(_STUDIO_DIR),
        "langgraph_json": str(langgraph_json),
        "topology_fingerprint": parity["production_fp"],
        "bind_host": LOCAL_HOST,
        "port": port,
        "local_api_url": api,
        "studio_url": studio,
        "docs_url": f"{api}/docs",
        "langsmith_api_key_present": key_present,
        "anonymous_studio_attempt": not key_present,
        "gate_code_if_browser_auth_required": (
            GATE_BROWSER_CREDENTIAL_REQUIRED if not key_present else None
        ),
        "env": {
            "LANGSMITH_TRACING": env.get("LANGSMITH_TRACING"),
            "LANGGRAPH_CLI_NO_ANALYTICS": env.get("LANGGRAPH_CLI_NO_ANALYTICS"),
            "LANGGRAPH_ANALYTICS": env.get("LANGGRAPH_ANALYTICS"),
            "LANGGRAPH_HOST": env.get("LANGGRAPH_HOST"),
        },
        "command": cmd,
        "pna_hint": _PNA_HINT.replace("<port>", str(port)),
        "note": (
            "Studio persistence is the Agent Server dev checkpointer "
            "(sqlite/memory), separate from production PostgresSaver. "
            "Complete non-browser work first (--no-browser). "
            "Missing LANGSMITH_API_KEY is not a stop; anonymous/local "
            "connection is attempted first."
        ),
    }

    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print("Starting LangGraph Studio (Agent Server) - Option A...")
        print(f"  app_dir:       {payload['studio_app_dir']}")
        print(f"  langgraph.json:{payload['langgraph_json']}")
        print(f"  fingerprint:   {payload['topology_fingerprint']}")
        print(f"  bind:          {LOCAL_HOST}:{port}")
        print(f"  local API:     {api}")
        print(f"  docs:          {payload['docs_url']}")
        print(f"  Studio URL:    {studio}")
        print(f"  tracing:       {payload['env']['LANGSMITH_TRACING']}")
        print(f"  analytics:     LANGGRAPH_CLI_NO_ANALYTICS="
              f"{payload['env']['LANGGRAPH_CLI_NO_ANALYTICS']}")
        print()
        print("Anonymous/local Studio connection first "
              f"(LANGSMITH_API_KEY present: {key_present}).")
        if not key_present:
            emit_browser_credential_gate(sys.stdout)
        print()
        print(payload["pna_hint"])
        print()
        print("Press Ctrl+C to stop. Studio will not interfere with the")
        print("production PostgresSaver at 127.0.0.1:55433.")
        print()

    creationflags = 0
    popen_kwargs: dict[str, Any] = {
        "cwd": str(_STUDIO_DIR),
        "env": env,
    }
    if sys.platform == "win32":
        # New process group so taskkill /T can reap descendants.
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        popen_kwargs["creationflags"] = creationflags
    else:
        popen_kwargs["start_new_session"] = True

    proc: subprocess.Popen | None = None

    def _cleanup() -> None:
        terminate_process_tree(proc)

    atexit.register(_cleanup)
    try:
        proc = subprocess.Popen(cmd, **popen_kwargs)
        return int(proc.wait())
    except KeyboardInterrupt:
        terminate_process_tree(proc)
        return 130
    finally:
        terminate_process_tree(proc)
        try:
            atexit.unregister(_cleanup)
        except Exception:  # noqa: BLE001
            pass


# Back-compat aliases used by older callers / tests
_check_fingerprint_parity = check_fingerprint_parity
_free_port = port_is_free
