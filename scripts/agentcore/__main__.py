"""AgentCore operator CLI — python -m agentcore <command> [--json].

Commands:
  health        Check all components (PG18, Bifrost, memory service, scheduled tasks).
  status        Show active workflow runs, sessions, evidence counts.
  backup        Invoke ops/Backup-AgentCorePostgres.ps1 and report result.
  restore-test  Invoke ops/Test-AgentCorePostgresRestore.ps1 and report result.
  diagnose      Collect diagnostics bundle (PG version, table counts, task states).
  workflow      Launch / observe / control an autonomous AgentCore workflow run.
                Subcommands:
                  init      Register project + worktree (idempotent).
                  start     Open a workflow thread + execute the graph.
                  status    Report project / run / thread / node / checkpoint.
                  pause     Mark active run paused (preserves checkpoints).
                  approve   Resolve a pending human pause as approved.
                  reject    Resolve a pending human pause as rejected.
                  resume    Re-execute the thread from the latest checkpoint.
                  cancel    Mark run aborted, preserve evidence.
                  logs      Tail per-run logs.
                  evidence  List wf_evidence rows.
                  topology  Show prod + studio topology fingerprint + node list.
                  studio    Launch LangGraph Studio (Agent Server dev checkpointer).

Exit codes: 0=ok, 1=warnings, 2=error.
Never prints secrets or passwords.

Usage (from repo root, run from scripts/):
    python -m agentcore health
    python -m agentcore health --json
    python -m agentcore workflow init  --project-key foo --target D:\\projects\\foo
    python -m agentcore workflow start --project-key foo --goal "fix failing test"
    python -m agentcore workflow status --project-key foo
    python -m agentcore workflow topology
    python -m agentcore workflow studio --port 8124 --no-browser

See docs\\operations\\AUTONOMOUS_WORKFLOW_AND_STUDIO.md for the full runbook.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ──────────────────────────────────────────────────────────────────────

# scripts/agentcore/__main__.py → parents[1] = scripts → parents[2] = repo root
_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[2]
OPS_DIR = REPO_ROOT / "ops"

PG_HOST = "127.0.0.1"
PG_PORT = 55433
PG_DB = "agent_core"
PG_USER = "postgres"
BIFROST_URL = "http://127.0.0.1:8080/mcp"
TASK_PREFIX = "\\AgentCore\\"
REQUIRED_TASKS = [
    "AgentCore-Bifrost-Gateway",
    "DailyDriftCheck",
    "NightlyBackup",
    "NightlyRestoreTest",
    "PostgresRuntime",
    "WeeklyMaintenance",
]


def _pg_conninfo() -> str:
    pw = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    return f"host={PG_HOST} port={PG_PORT} dbname={PG_DB} user={PG_USER} password={pw}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Component checks ────────────────────────────────────────────────────────────

def check_postgres() -> dict[str, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row

        ci = _pg_conninfo()
        with psycopg.connect(ci, row_factory=dict_row, connect_timeout=5) as c:
            row = c.execute("SELECT version()").fetchone()
            version = row["version"] if row else "unknown"
            db_row = c.execute("SELECT current_database()").fetchone()
            db_name = db_row["current_database"] if db_row else "unknown"
        return {"ok": True, "version": version[:80], "database": db_name}
    except ImportError:
        return {"ok": False, "error": "psycopg not installed (pip install psycopg[binary])"}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "hint": f"Check PG at {PG_HOST}:{PG_PORT}"}


def check_bifrost() -> dict[str, Any]:
    try:
        req = urllib.request.Request(BIFROST_URL, method="GET")
        try:
            urllib.request.urlopen(req, timeout=5)
            return {"ok": True, "status": 200}
        except urllib.error.HTTPError as he:
            # 401 = Bifrost is up and requiring auth (expected)
            if he.code == 401:
                return {"ok": True, "status": 401, "note": "auth required (expected)"}
            return {"ok": False, "status": he.code, "error": str(he)}
        except urllib.error.URLError as ue:
            return {"ok": False, "error": str(ue), "hint": f"Is Bifrost running at {BIFROST_URL}?"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_memory_service() -> dict[str, Any]:
    expected = {
        "memory_status", "startup_context", "retrieve_context", "append_event",
        "propose_fact", "expand_source", "session_open", "session_close",
        "build_handoff", "docs_search",
    }
    try:
        mem_path = str(REPO_ROOT / "scripts" / "agentcore_memory")
        if mem_path not in sys.path:
            sys.path.insert(0, mem_path)
        import importlib
        import server as mem_server
        importlib.reload(mem_server)
        actual = {t["name"] for t in mem_server.tool_defs()}
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        ok = not missing
        return {
            "ok": ok,
            "tool_count": len(actual),
            "missing": missing,
            "extra": extra,
            "all_10_present": ok,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_scheduled_tasks() -> dict[str, Any]:
    results: dict[str, str] = {}
    missing: list[str] = []
    try:
        for task in REQUIRED_TASKS:
            full_path = TASK_PREFIX + task
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-ScheduledTask -TaskPath '\\AgentCore\\' -TaskName '{task}' -ErrorAction SilentlyContinue).State"],
                capture_output=True, text=True, timeout=15,
            )
            state = out.stdout.strip() or "Missing"
            results[task] = state
            if state == "Missing":
                missing.append(task)
        return {"ok": len(missing) == 0, "tasks": results, "missing": missing}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Commands ────────────────────────────────────────────────────────────────────

def cmd_health(as_json: bool) -> int:
    """Check all components."""
    pg = check_postgres()
    bifrost = check_bifrost()
    mem = check_memory_service()
    tasks = check_scheduled_tasks()

    all_ok = pg["ok"] and bifrost["ok"] and mem["ok"] and tasks["ok"]
    has_warn = not all_ok and (pg["ok"] or bifrost["ok"] or mem["ok"] or tasks["ok"])

    payload = {
        "timestamp": _now_iso(),
        "overall": "ok" if all_ok else ("warn" if has_warn else "error"),
        "components": {
            "postgres_18": pg,
            "bifrost_gateway": bifrost,
            "memory_service": mem,
            "scheduled_tasks": tasks,
        },
    }

    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"AgentCore Health Check — {payload['timestamp']}")
        print(f"Overall: {payload['overall'].upper()}")
        print()
        _print_component("PostgreSQL 18", pg, f"{PG_HOST}:{PG_PORT}/{PG_DB}")
        _print_component("Bifrost Gateway", bifrost, BIFROST_URL)
        _print_component("Memory Service", mem, "10-tool surface")
        _print_component("Scheduled Tasks", tasks, f"{len(REQUIRED_TASKS)} required tasks")

    return 0 if all_ok else (1 if has_warn else 2)


def _print_component(name: str, result: dict, detail: str) -> None:
    icon = "OK" if result.get("ok") else "!!"
    print(f"  [{icon}] {name:<24} {detail}")
    if not result.get("ok"):
        err = result.get("error") or result.get("missing") or ""
        if err:
            print(f"       ERROR: {err}")
    hint = result.get("hint", "")
    if hint:
        print(f"       HINT:  {hint}")


def cmd_status(as_json: bool) -> int:
    """Show active workflow state."""
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(_pg_conninfo(), row_factory=dict_row, connect_timeout=5) as c:
            # Active runs (wf_runs = M6 table name)
            runs = c.execute(
                "SELECT status, COUNT(*) AS cnt FROM agentcore.wf_runs GROUP BY status"
            ).fetchall()
            # Recent evidence (last 24h) — column is created_at
            ev = c.execute(
                "SELECT COUNT(*) AS cnt FROM agentcore.wf_evidence "
                "WHERE created_at > NOW() - INTERVAL '24 hours'"
            ).fetchone()
            # Active sessions (agentcore.sessions — M3 table; ended_at=NULL = active)
            sessions = c.execute(
                "SELECT COUNT(*) AS cnt FROM agentcore.sessions "
                "WHERE ended_at IS NULL"
            ).fetchone()
            # Event count (agentcore.evidence_events — M3 table)
            events = c.execute(
                "SELECT COUNT(*) AS cnt FROM agentcore.evidence_events"
            ).fetchone()

        run_counts = {r["status"]: r["cnt"] for r in runs}
        payload = {
            "timestamp": _now_iso(),
            "workflow_runs": run_counts,
            "evidence_last_24h": ev["cnt"] if ev else 0,
            "active_sessions": sessions["cnt"] if sessions else 0,
            "total_events": events["cnt"] if events else 0,
        }

        if as_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"AgentCore Status — {payload['timestamp']}")
            print(f"  Workflow runs:    {run_counts}")
            print(f"  Evidence (24h):   {payload['evidence_last_24h']}")
            print(f"  Active sessions:  {payload['active_sessions']}")
            print(f"  Total events:     {payload['total_events']}")
        return 0

    except Exception as exc:
        msg = {"timestamp": _now_iso(), "error": str(exc)}
        if as_json:
            print(json.dumps(msg))
        else:
            print(f"ERROR: {exc}")
            print("  Log: H:\\AgentRuntime\\service-logs\\")
        return 2


def _run_ps1(script_path: Path, as_json: bool, label: str) -> int:
    """Run a PowerShell ops script, stream output, report result."""
    if not script_path.exists():
        msg = {"error": f"Script not found: {script_path}"}
        if as_json:
            print(json.dumps(msg))
        else:
            print(f"ERROR: Script not found: {script_path}")
        return 2

    if not as_json:
        print(f"Running {label}...")
        print(f"  Script: {script_path}")
        print()

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            capture_output=True, text=True, timeout=900,
        )
        success = result.returncode == 0
        stdout_lines = result.stdout.strip().splitlines()
        stderr_lines = result.stderr.strip().splitlines() if result.stderr.strip() else []

        payload = {
            "timestamp": _now_iso(),
            "script": str(script_path),
            "exit_code": result.returncode,
            "ok": success,
            "stdout_tail": stdout_lines[-20:] if len(stdout_lines) > 20 else stdout_lines,
            "stderr_tail": stderr_lines[-10:] if stderr_lines else [],
        }

        if as_json:
            print(json.dumps(payload, indent=2))
        else:
            for line in stdout_lines:
                print(f"  {line}")
            if stderr_lines:
                print("  STDERR:")
                for line in stderr_lines[-5:]:
                    print(f"    {line}")
            print()
            status = "PASS" if success else "FAIL"
            print(f"Result: {status} (exit {result.returncode})")

        return 0 if success else 2

    except subprocess.TimeoutExpired:
        msg = {"error": "Script timed out (900s)", "script": str(script_path)}
        if as_json:
            print(json.dumps(msg))
        else:
            print(f"ERROR: Script timed out after 900 seconds.")
        return 2
    except Exception as exc:
        msg = {"error": str(exc)}
        if as_json:
            print(json.dumps(msg))
        else:
            print(f"ERROR: {exc}")
        return 2


def cmd_backup(as_json: bool) -> int:
    return _run_ps1(OPS_DIR / "Backup-AgentCorePostgres.ps1", as_json, "AgentCore PostgreSQL Backup")


def cmd_restore_test(as_json: bool) -> int:
    return _run_ps1(OPS_DIR / "Test-AgentCorePostgresRestore.ps1", as_json, "AgentCore Restore Test")


def cmd_diagnose(as_json: bool) -> int:
    """Collect diagnostics bundle."""
    diag: dict[str, Any] = {"timestamp": _now_iso()}

    # PostgreSQL version + table counts
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(_pg_conninfo(), row_factory=dict_row, connect_timeout=5) as c:
            ver = c.execute("SELECT version()").fetchone()
            diag["pg_version"] = ver["version"][:120] if ver else "unknown"

            tables = c.execute("""
                SELECT schemaname, tablename,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                FROM pg_tables
                WHERE schemaname IN ('agentcore', 'public')
                ORDER BY schemaname, tablename
            """).fetchall()
            diag["tables"] = [dict(r) for r in tables]

            # Key row counts
            counts: dict[str, int] = {}
            for t in ["evidence_events", "wf_evidence", "wf_runs", "projects", "sessions"]:
                try:
                    row = c.execute(f"SELECT COUNT(*) AS n FROM agentcore.{t}").fetchone()
                    counts[t] = row["n"] if row else 0
                except Exception:
                    counts[t] = -1
            diag["row_counts"] = counts

    except Exception as exc:
        diag["pg_error"] = str(exc)

    # Bifrost
    diag["bifrost"] = check_bifrost()

    # Scheduled tasks
    diag["scheduled_tasks"] = check_scheduled_tasks()

    # Memory service
    diag["memory_service"] = check_memory_service()

    # Log files (tail)
    log_dir = Path(r"H:\AgentRuntime\service-logs")
    log_tails: dict[str, list[str]] = {}
    if log_dir.exists():
        for lf in sorted(log_dir.glob("*.log"))[-3:]:
            try:
                lines = lf.read_text(encoding="utf-8", errors="replace").splitlines()
                log_tails[lf.name] = lines[-20:]
            except Exception:
                log_tails[lf.name] = ["<unreadable>"]
    diag["log_tails"] = log_tails

    # Requirements file existence
    req = REPO_ROOT / "scripts" / "agentcore_workflow" / "requirements.txt"
    diag["requirements_txt"] = str(req) if req.exists() else "MISSING"

    if as_json:
        print(json.dumps(diag, indent=2))
    else:
        print(f"AgentCore Diagnostics — {diag['timestamp']}")
        print()
        pg_ver = diag.get("pg_version", diag.get("pg_error", "unavailable"))
        print(f"  PostgreSQL: {pg_ver[:80]}")
        print(f"  Bifrost:    {diag['bifrost']}")
        print()
        print("  Table row counts:")
        for t, n in diag.get("row_counts", {}).items():
            print(f"    agentcore.{t:<30} {n}")
        print()
        tasks = diag.get("scheduled_tasks", {})
        print(f"  Scheduled tasks: {tasks.get('tasks', {})}")
        print()
        if log_tails:
            print(f"  Log tails ({len(log_tails)} files):")
            for fname, lines in log_tails.items():
                print(f"    {fname}: {lines[-1] if lines else '(empty)'}")
        else:
            print(f"  No logs at {log_dir}")

    return 0


# ── Entry point ─────────────────────────────────────────────────────────────────

COMMANDS = {
    "health": cmd_health,
    "status": cmd_status,
    "backup": cmd_backup,
    "restore-test": cmd_restore_test,
    "diagnose": cmd_diagnose,
}

HELP = """\
AgentCore Operator CLI

Usage: python -m agentcore <command> [--json]

Commands:
  health        Check PostgreSQL 18, Bifrost, memory service, scheduled tasks
  status        Show workflow runs, active sessions, evidence counts
  backup        Run ops/Backup-AgentCorePostgres.ps1 and report result
  restore-test  Run ops/Test-AgentCorePostgresRestore.ps1 and report result
  diagnose      Collect full diagnostics bundle
  workflow      Launch / observe / control an autonomous AgentCore workflow
                (init | start | status | pause | approve | reject | resume |
                 cancel | logs | evidence | topology | studio)
  cursor        Cursor new-chat recovery (recover | status | new-task | resume)

Options:
  --json        Output machine-readable JSON

Exit codes: 0=ok, 1=warnings, 2=error
"""


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(HELP)
        return 0

    # The "workflow" subcommand family is handled by its own module.
    if args[0].lower() == "workflow":
        from . import workflow_cli
        return workflow_cli.main(args[1:])

    if args[0].lower() == "cursor":
        from . import cursor_cli
        return cursor_cli.main(args[1:])

    cmd_name = args[0].lower()
    as_json = "--json" in args

    fn = COMMANDS.get(cmd_name)
    if fn is None:
        print(f"Unknown command: {cmd_name!r}. Run with --help for usage.")
        return 2

    return fn(as_json)


if __name__ == "__main__":
    sys.exit(main())
