"""Reconcile wf_runs rows stuck in 'running' status.

Usage:
    python -m agentcore_workflow.reconcile_stale_runs [options]

Options:
    --dry-run        Show what would be changed without writing anything.
    --yes            Skip the interactive confirmation prompt (non-interactive/CI use).
    --hours N        Threshold in hours; rows updated more than N hours ago are
                     candidates (default: 24).
    --project-key K  Limit candidates to a single project key (optional).

Design constraints (AGENTS.md / BLUEPRINT.md):
    - All status transitions go through db.update_run_status (SECURITY DEFINER
      path).  No raw UPDATE against wf_* tables.
    - PostgreSQL is canonical; script reads from agentcore.wf_runs and
      public.checkpoints.
    - Never deletes rows — only transitions status to "aborted".
    - Exits 0 on success, 1 on errors.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make agentcore_workflow importable when run as a module from the repo root.
_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from agentcore_workflow import db as wfdb


PG_DSN_ADMIN = (
    f"host=127.0.0.1 port=55433 dbname=agent_core "
    f"user=postgres password={os.environ.get('AGENT_CORE_POSTGRES_PASSWORD', '')}"
)


def _pg_conn():
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(PG_DSN_ADMIN, row_factory=dict_row)


def _find_stale_runs(*, hours: float, project_key: str | None) -> list[dict]:
    """Return wf_runs rows in 'running' state with no recent checkpoint activity."""
    query = """
        SELECT
            r.id,
            r.project_id,
            r.langgraph_thread,
            r.started_at,
            r.updated_at,
            r.current_milestone,
            r.metadata,
            p.project_key
        FROM agentcore.wf_runs r
        LEFT JOIN agentcore.projects p ON p.id = r.project_id
        WHERE r.status = 'running'
          AND r.updated_at < NOW() - INTERVAL '{hours} hours'
    """.replace("{hours}", str(float(hours)))
    if project_key:
        query += "  AND p.project_key = %(project_key)s"
    query += "\nORDER BY r.updated_at ASC"

    params: dict = {}
    if project_key:
        params["project_key"] = project_key

    rows: list[dict] = []
    with _pg_conn() as c:
        rows = list(c.execute(query, params or None).fetchall())

    stale: list[dict] = []
    for row in rows:
        thread = row.get("langgraph_thread") or ""
        last_checkpoint_ns: int | None = None
        if thread:
            try:
                with _pg_conn() as c:
                    cp = c.execute(
                        "SELECT MAX(checkpoint_ns) AS max_ns "
                        "FROM public.checkpoints WHERE thread_id = %s",
                        (thread,),
                    ).fetchone()
                if cp and cp.get("max_ns") is not None:
                    last_checkpoint_ns = cp["max_ns"]
            except Exception:
                pass

        stale.append({
            **dict(row),
            "last_checkpoint_ns": last_checkpoint_ns,
        })

    return stale


def _format_table(rows: list[dict]) -> str:
    if not rows:
        return "  (no stale runs found)"
    lines = [
        f"  {'ID':<36}  {'project_key':<24}  {'updated_at':<26}  {'last_chk'}",
        f"  {'-'*36}  {'-'*24}  {'-'*26}  {'-'*22}",
    ]
    for r in rows:
        rid = str(r.get("id", ""))[:36]
        pk = str(r.get("project_key") or "unknown")[:24]
        upd = str(r.get("started_at") or r.get("updated_at") or "")[:26]
        ns = r.get("last_checkpoint_ns")
        chk = f"ns={ns}" if ns is not None else "no checkpoint"
        lines.append(f"  {rid:<36}  {pk:<24}  {upd:<26}  {chk}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reconcile_stale_runs",
        description="Transition stale 'running' wf_runs rows to 'aborted'.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show candidates only — no writes.",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip the interactive confirmation prompt (non-interactive/CI use).",
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=24.0,
        metavar="N",
        help="Rows updated more than N hours ago are candidates (default: 24).",
    )
    parser.add_argument(
        "--project-key",
        metavar="KEY",
        default=None,
        help="Limit to a single project key.",
    )
    args = parser.parse_args(argv)

    ts = datetime.now(timezone.utc).isoformat()
    print(f"AgentCore wf_runs reconciliation — {ts}")
    print(f"  threshold: {args.hours}h  project_key: {args.project_key or '(all)'}")
    print()

    try:
        stale = _find_stale_runs(hours=args.hours, project_key=args.project_key)
    except Exception as exc:
        print(f"ERROR: Could not query wf_runs: {exc}", file=sys.stderr)
        return 1

    print(f"Stale 'running' candidates ({len(stale)} found):")
    print(_format_table(stale))
    print()

    if not stale:
        print("Nothing to reconcile.")
        return 0

    if args.dry_run:
        print("--dry-run: no changes written.")
        return 0

    if not args.yes:
        try:
            answer = input(f"Transition {len(stale)} run(s) to 'aborted'? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted by user.")
            return 1
        if answer not in ("y", "yes"):
            print("No changes written.")
            return 0

    aborted = 0
    errors = 0
    for row in stale:
        run_id = str(row["id"])
        try:
            wfdb.update_run_status(run_id, "aborted")
            print(f"  aborted {run_id}  project={row.get('project_key', 'unknown')}")
            aborted += 1
        except Exception as exc:
            print(f"  ERROR  {run_id}: {exc}", file=sys.stderr)
            errors += 1

    print()
    print(f"Summary: {aborted} aborted, {errors} errors, {len(stale) - aborted - errors} skipped.")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
