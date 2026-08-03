#!/usr/bin/env python3
"""Spawn/reuse project-scoped MCP child processes and proxy stdio.

Usage:
  python child_launcher.py --server serena|depwire|tentra|context-fabric|filesystem
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
RUNTIME_ROOT = Path(os.environ.get("AGENTCORE_RUNTIME_ROOT", r"F:\AgentCore\runtime"))
STATE_PATH = Path(
    os.environ.get(
        "AGENTCORE_PROJECT_ROUTER_STATE",
        str(RUNTIME_ROOT / "bifrost" / "state" / "active-project.json"),
    )
)
PROCESS_REGISTRY = Path(
    os.environ.get(
        "AGENTCORE_PROJECT_PROCESS_REGISTRY",
        str(RUNTIME_ROOT / "mcp-processes" / "registry.json"),
    )
)
PROCESS_REGISTRY_LOCK = PROCESS_REGISTRY.with_suffix(PROCESS_REGISTRY.suffix + ".lock")
TENTRA_DATA = Path(
    os.environ.get("TENTRA_DATA_DIR", str(RUNTIME_ROOT / "tentra" / "data"))
)
IDLE_TIMEOUT_SECONDS = 30 * 60

REJECT_MARKERS = ("swarmrecall", "swarmvault", "agentswarm", "swarmclaw")
REJECT_PREFIXES = (Path(r"F:\AgentCore\agentmemory"),)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str) -> None:
    sys.stderr.write(f"[child_launcher] {msg}\n")
    sys.stderr.flush()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(
        f"{path.name}.tmp.{os.getpid()}.{threading.get_ident()}"
    )
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


@contextmanager
def process_registry_lock():
    PROCESS_REGISTRY_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with PROCESS_REGISTRY_LOCK.open("a+b") as lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"0")
            lock_file.flush()
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def load_active_project() -> dict[str, Any]:
    if not STATE_PATH.exists():
        raise SystemExit("No active project. Call agentcore-project-router project_activate first.")
    state = load_json(STATE_PATH)
    path = Path(state["path"])
    if not path.exists():
        raise SystemExit(f"Active project path missing: {path}")
    text = str(path.resolve()).lower()
    for marker in REJECT_MARKERS:
        if marker in text:
            raise SystemExit(f"Active project rejected (Swarm marker): {marker}")
    for prefix in REJECT_PREFIXES:
        try:
            path.resolve().relative_to(prefix.resolve())
            raise SystemExit(f"Active project rejected under {prefix}")
        except ValueError:
            pass
        except OSError:
            pass
    return state


def load_server_spec(server_key: str) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    # Accept either hyphenated canonical id or bifrost underscore name
    servers = registry["servers"]
    if server_key in servers:
        return servers[server_key]
    for _cid, spec in servers.items():
        if spec.get("bifrost_client_name") == server_key or spec.get("canonical_id") == server_key:
            return spec
    raise SystemExit(f"Unknown server: {server_key}")


def build_command(spec: dict[str, Any], project: dict[str, Any]) -> tuple[list[str], dict[str, str], Path]:
    cwd = Path(project["path"])
    command = spec["executable_or_url"]
    args = list(spec.get("arguments") or [])
    env = os.environ.copy()
    canonical = spec["canonical_id"]

    if canonical == "filesystem":
        # Limit roots to the active project worktree only.
        package_args = args[:2] if len(args) >= 2 and args[0] == "-y" else []
        args = package_args + [str(cwd)]
    if canonical == "tentra":
        TENTRA_DATA.mkdir(parents=True, exist_ok=True)
        env["TENTRA_DATA_DIR"] = str(TENTRA_DATA)
        env["TENTRA_PROJECT_ROOT"] = str(cwd)
    if canonical == "serena":
        # Prefer project-from-cwd semantics when launched from project root
        if "--project-from-cwd" not in args:
            # Keep ide context; child cwd is the project
            pass
    if canonical == "depwire":
        # Explicitly do NOT set DEPWIRE_NO_TELEMETRY
        env.pop("DEPWIRE_NO_TELEMETRY", None)

    # Non-secret static defaults
    if canonical == "sequential-thinking":
        env["DISABLE_THOUGHT_LOGGING"] = "true"

    cmd = [command] + args
    return cmd, env, cwd


def load_process_registry() -> dict[str, Any]:
    if not PROCESS_REGISTRY.exists():
        return {"processes": {}, "updated_at": None}
    try:
        return load_json(PROCESS_REGISTRY)
    except (OSError, json.JSONDecodeError):
        return {"processes": {}, "updated_at": None}


def update_process_registry(server: str, pid: int, project_path: str, cmd: list[str]) -> None:
    with process_registry_lock():
        reg = load_process_registry()
        processes = reg.setdefault("processes", {})
        processes[f"{server}:{project_path}"] = {
            "server": server,
            "pid": pid,
            "project_path": project_path,
            "command": cmd,
            "started_at": _now(),
        }
        reg["updated_at"] = _now()
        # Never store env/secrets.
        save_json(PROCESS_REGISTRY, reg)


def proxy_stdio(proc: subprocess.Popen[bytes], server: str, project_path: str) -> int:
    """Bidirectional byte proxy between this process stdio and child stdio."""
    last_activity = time.time()
    stop = threading.Event()

    def pump_in() -> None:
        nonlocal last_activity
        assert proc.stdin is not None
        try:
            while not stop.is_set():
                chunk = sys.stdin.buffer.read(64 * 1024)
                if not chunk:
                    break
                proc.stdin.write(chunk)
                proc.stdin.flush()
                last_activity = time.time()
        except (BrokenPipeError, OSError):
            pass
        finally:
            stop.set()
            try:
                proc.stdin.close()
            except OSError:
                pass

    def pump_out() -> None:
        nonlocal last_activity
        assert proc.stdout is not None
        try:
            while not stop.is_set():
                chunk = proc.stdout.read(64 * 1024)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                last_activity = time.time()
        except (BrokenPipeError, OSError):
            pass
        finally:
            stop.set()

    def idle_watch() -> None:
        while not stop.is_set():
            time.sleep(5)
            if time.time() - last_activity > IDLE_TIMEOUT_SECONDS:
                _log(f"idle timeout {IDLE_TIMEOUT_SECONDS}s — terminating child")
                stop.set()
                try:
                    proc.terminate()
                except OSError:
                    pass
                break

    t_in = threading.Thread(target=pump_in, daemon=True)
    t_out = threading.Thread(target=pump_out, daemon=True)
    t_idle = threading.Thread(target=idle_watch, daemon=True)
    t_in.start()
    t_out.start()
    t_idle.start()

    # Also forward stderr for diagnostics (sanitized: never echo env)
    def pump_err() -> None:
        assert proc.stderr is not None
        try:
            for line in proc.stderr:
                try:
                    text = line.decode("utf-8", errors="replace")
                except Exception:  # noqa: BLE001
                    continue
                # Drop lines that look like secrets
                lowered = text.lower()
                if "api_key" in lowered or "password" in lowered or "authorization:" in lowered:
                    sys.stderr.write("[child_launcher] <redacted child stderr line>\n")
                else:
                    sys.stderr.buffer.write(line)
                sys.stderr.flush()
        except (BrokenPipeError, OSError):
            pass

    t_err = threading.Thread(target=pump_err, daemon=True)
    t_err.start()

    returncode = proc.wait()
    stop.set()
    return int(returncode or 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--server",
        required=True,
        help="Project-scoped server key: serena|depwire|tentra|context-fabric|filesystem",
    )
    args = parser.parse_args()

    project = load_active_project()
    spec = load_server_spec(args.server)
    if spec.get("project_scope") != "project" and spec.get("connection_type") != "router":
        _log(f"warning: {args.server} is not marked project-scoped in registry")

    cmd, env, cwd = build_command(spec, project)
    _log(f"starting {spec['canonical_id']} in {cwd}")
    _log(f"command: {cmd[0]} ({len(cmd) - 1} args)")

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
    except OSError as exc:
        _log(f"failed to spawn child: {exc}")
        return 1

    update_process_registry(spec["canonical_id"], proc.pid or 0, str(cwd), cmd)
    return proxy_stdio(proc, spec["canonical_id"], str(cwd))


if __name__ == "__main__":
    raise SystemExit(main())
