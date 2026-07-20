"""AgentCore M6/M8 — Workflow operator launcher.

Adds a ``python -m agentcore workflow <subcommand>`` command family to the
existing ``python -m agentcore`` operator CLI. Provides a single, supported
way for a new operator to launch, observe, pause, approve, resume, cancel,
recover, and complete an autonomous AgentCore workflow against any
registered project — without writing custom Python.

The launcher uses the canonical AgentCore PostgresSaver in
``public.checkpoints`` (PG18 at ``127.0.0.1:55433``) and reuses every
existing workflow primitive (``register_run``, ``upsert_milestone``,
``create_pause``, ``resolve_pause``, ``record_evidence``, ``set_capability_state``,
``create_capability_lease``). It does NOT replace the production checkpointer,
does NOT fork the workflow definition, and does NOT add workflow tools to the
ten-tool ``agentcore-memory`` surface.

Authority:
    BLUEPRINT.md M6 / MEMORY_PLATFORM_EXECUTION_PLAN.md M6
    PROJECT_ANCHOR.md §3 (PostgreSQL 18 at 127.0.0.1:55433)
    AGENTS.md (Git policy, no committed .env, no printed secrets)

Exit codes (per :mod:`agentcore.__main__`):
    0 = ok, 1 = warnings, 2 = error

Subcommands:
    init       Register or update a project + scaffold an isolated worktree.
    start      Create a new thread/run and execute the workflow.
    status     Show project, run, thread, Milestone, node, checkpoint, blockers.
    pause      Inspect a pending human pause.
    approve    Resolve a pending pause with operator approval and resume.
    reject     Resolve a pending pause with operator rejection and resume.
    resume     Resume a paused thread after process restart.
    cancel     Transition the run to cancelled safely without deleting evidence.
    logs       Tail workflow log lines for a thread or run.
    evidence   List recorded evidence for a run.
    topology   Show the shared graph topology fingerprint.
    studio     Start the local LangGraph Studio (Agent Server) for this graph.

All commands accept ``--json`` for machine-readable output.

Canonical runbook:
    docs\\operations\\AUTONOMOUS_WORKFLOW_AND_STUDIO.md

Studio adapter docs:
    scripts\\agentcore_workflow\\studio\\README.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentcore_workflow import db as wf_db
from agentcore_workflow.workflow import (
    build_topology,
    topology_fingerprint,
    build_graph,
    run_workflow,
)


# ──────────────────────────────────────────────────────────────────────────────
# Paths and constants (mirror agentcore/__main__.py; never print secrets)
# ──────────────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts/agentcore -> repo root
_WORKFLOW_DIR = _REPO_ROOT / "scripts" / "agentcore_workflow"


PG_HOST = "127.0.0.1"
PG_PORT = 55433
PG_DB = "agent_core"
PG_USER = "postgres"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pg_conninfo() -> str:
    pw = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    return f"host={PG_HOST} port={PG_PORT} dbname={PG_DB} user={PG_USER} password={pw}"


def _import_psycopg():
    """Import psycopg + dict_row without failing the whole CLI."""
    try:
        import psycopg
        from psycopg.rows import dict_row
        return psycopg, dict_row
    except ImportError:
        return None, None


def _print_json_or_text(payload: dict, as_json: bool, human_renderer=None) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
        return
    if human_renderer is not None:
        out = human_renderer(payload)
        if out is not None:
            print(out)
        return
    # Fallback: emit YAML-like text
    for k, v in payload.items():
        print(f"  {k}: {v}")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers: project registration, worktree resolution
# ──────────────────────────────────────────────────────────────────────────────


def _ensure_project(
    project_key: str,
    project_name: str,
    root_path: str,
    trust_class: str = "project_verified",
) -> str:
    """Register or update the project in agentcore.projects (admin=True).

    Returns the project UUID.
    """
    psycopg, dict_row = _import_psycopg()
    if psycopg is None:
        raise RuntimeError("psycopg not installed (pip install 'psycopg[binary]')")
    ci = _pg_conninfo()
    with psycopg.connect(ci, row_factory=dict_row) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.projects
                (project_key, project_name, root_path, trust_class)
            VALUES (%s, %s, %s, %s::agentcore.trust_class)
            ON CONFLICT (project_key) DO UPDATE
                SET project_name = EXCLUDED.project_name,
                    root_path = EXCLUDED.root_path,
                    trust_class = EXCLUDED.trust_class
            RETURNING id
            """,
            (project_key, project_name, root_path, trust_class),
        ).fetchone()
        return str(row["id"])


def _resolve_project(project_key: str) -> dict | None:
    psycopg, dict_row = _import_psycopg()
    ci = _pg_conninfo()
    with psycopg.connect(ci, row_factory=dict_row) as c:
        row = c.execute(
            "SELECT id, project_key, project_name, root_path, current_milestone, trust_class "
            "FROM agentcore.projects WHERE project_key = %s",
            (project_key,),
        ).fetchone()
        return dict(row) if row else None


def _find_run(thread_uuid: str | None, run_db_id: str | None) -> dict | None:
    """Find a wf_runs row by thread_uuid or run id."""
    psycopg, dict_row = _import_psycopg()
    ci = _pg_conninfo()
    if run_db_id:
        sql = ("SELECT id, langgraph_thread, project_id, status, current_milestone, "
               "current_macro, current_micro, ab_enabled, started_at, updated_at, completed_at "
               "FROM agentcore.wf_runs WHERE id = %s")
        params = (run_db_id,)
    elif thread_uuid:
        sql = ("SELECT id, langgraph_thread, project_id, status, current_milestone, "
               "current_macro, current_micro, ab_enabled, started_at, updated_at, completed_at "
               "FROM agentcore.wf_runs WHERE langgraph_thread = %s "
               "ORDER BY started_at DESC LIMIT 1")
        params = (thread_uuid,)
    else:
        return None
    with psycopg.connect(ci, row_factory=dict_row) as c:
        row = c.execute(sql, params).fetchone()
        return dict(row) if row else None


def _checkpoint_summary(thread_uuid: str) -> dict:
    """Return a checkpoint summary for a thread from public.checkpoints."""
    psycopg, dict_row = _import_psycopg()
    ci = _pg_conninfo()
    out: dict[str, Any] = {"thread_id": thread_uuid}
    try:
        with psycopg.connect(ci, row_factory=dict_row) as c:
            cnt = c.execute(
                "SELECT COUNT(*) AS n FROM public.checkpoints WHERE thread_id = %s",
                (thread_uuid,),
            ).fetchone()
            out["checkpoint_count"] = int(cnt["n"]) if cnt else 0
            latest = c.execute(
                "SELECT checkpoint_id, checkpoint_ns, type, checkpoint "
                "FROM public.checkpoints WHERE thread_id = %s "
                "ORDER BY checkpoint_id DESC LIMIT 1",
                (thread_uuid,),
            ).fetchone()
            if latest:
                out["latest_checkpoint_id"] = latest["checkpoint_id"]
                out["latest_checkpoint_ns"] = latest["checkpoint_ns"]
                out["latest_type"] = latest["type"]
                # Latest node name from blob
                blob = latest["checkpoint"]
                if isinstance(blob, dict):
                    node = blob.get("next") or blob.get("node") or blob.get("step")
                    out["latest_node"] = node
    except Exception as exc:
        out["error"] = str(exc)
    return out


def _pending_pause(run_db_id: str) -> dict | None:
    psycopg, dict_row = _import_psycopg()
    ci = _pg_conninfo()
    with psycopg.connect(ci, row_factory=dict_row) as c:
        row = c.execute(
            """
            SELECT id, scope_key, question, context_summary, resolution,
                   operator_decision, operator_notes, requested_at, resolved_at
            FROM agentcore.wf_human_pauses
            WHERE run_id = %s AND resolution = 'pending'
            ORDER BY requested_at DESC LIMIT 1
            """,
            (run_db_id,),
        ).fetchone()
        return dict(row) if row else None


# ──────────────────────────────────────────────────────────────────────────────
# Subcommand implementations
# ──────────────────────────────────────────────────────────────────────────────


def cmd_init(args: argparse.Namespace) -> int:
    """Register/update project + scaffold an isolated approved worktree.

    --project-key    (required) stable project key
    --project-name   (optional, default = project_key)
    --target         (required) absolute path to the project directory on D:
    --git-remote     (optional) origin URL for fetch/push (used by commit/push)
    --worktree       (optional) isolated worktree path under D:\\agentcore-worktrees
    """
    project_key = args.project_key
    target = Path(args.target).resolve()
    if not target.exists():
        print(f"ERROR: target path does not exist: {target}", file=sys.stderr)
        return 2
    if not str(target).startswith(("D:\\", "D:/", "E:\\", "E:/", "F:\\", "F:/", "H:\\", "H:/")):
        # Only D: (canonical_d) is the normal project source root per BLUEPRINT.
        # Allow E:/F:/H: for archive/runtime scopes if operator passes them.
        pass

    project_name = args.project_name or project_key
    target_str = str(target)

    project_id = _ensure_project(project_key, project_name, target_str)

    # Worktree selection
    worktree = args.worktree
    if worktree:
        worktree_path = Path(worktree).resolve()
        worktree_path.mkdir(parents=True, exist_ok=True)
        worktree_str = str(worktree_path)
    else:
        # Default isolated worktree under D:\agentcore-worktrees\<project_key>
        wt_root = Path(r"D:\agentcore-worktrees") / project_key
        wt_root.mkdir(parents=True, exist_ok=True)
        worktree_str = str(wt_root)

    # Optional git remote capture (no fetching, no push)
    remote = args.git_remote or ""
    if remote:
        psycopg, dict_row = _import_psycopg()
        ci = _pg_conninfo()
        with psycopg.connect(ci, row_factory=dict_row) as c:
            # Insert a repositories row keyed by canonical_path; ignore if already there.
            repo_key = f"{project_key}-repo"
            c.execute(
                """
                INSERT INTO agentcore.repositories (repo_key, canonical_path, remote_url)
                VALUES (%s, %s, %s)
                ON CONFLICT (canonical_path) DO UPDATE SET remote_url = EXCLUDED.remote_url
                """,
                (repo_key, target_str, remote),
            )

    payload = {
        "timestamp": _now_iso(),
        "ok": True,
        "project_id": project_id,
        "project_key": project_key,
        "project_name": project_name,
        "target_path": target_str,
        "worktree_path": worktree_str,
        "git_remote": remote or None,
    }
    _print_json_or_text(
        payload,
        args.json,
        lambda p: (
            f"Project registered: {p['project_key']}\n"
            f"  project_id:     {p['project_id']}\n"
            f"  target_path:    {p['target_path']}\n"
            f"  worktree_path:  {p['worktree_path']}\n"
            f"  git_remote:     {p['git_remote']}\n"
            "Run: python -m agentcore workflow start --project-key ..."
        ),
    )
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """Start a new workflow run against a registered project."""
    project_key = args.project_key
    if not project_key and args.project:
        # Resolve project key from root path if --project is a path, otherwise use it as key
        proj_path = Path(args.project).resolve() if os.path.exists(args.project) else None
        if proj_path:
            # Let's search registered projects for a matching root_path
            psycopg, dict_row = _import_psycopg()
            if psycopg:
                ci = _pg_conninfo()
                with psycopg.connect(ci, row_factory=dict_row) as c:
                    row = c.execute(
                        "SELECT project_key FROM agentcore.projects WHERE root_path = %s",
                        (str(proj_path),),
                    ).fetchone()
                    if row:
                        project_key = row["project_key"]
        if not project_key:
            # Fallback: assume --project was passed as the project_key directly
            project_key = args.project

    if not project_key:
        print("ERROR: Either --project-key or --project must be specified.", file=sys.stderr)
        return 2

    goal = args.goal
    if not goal and args.goal_file:
        goal_path = Path(args.goal_file).resolve()
        if goal_path.exists():
            goal = goal_path.read_text(encoding="utf-8")
        else:
            print(f"ERROR: goal file does not exist: {goal_path}", file=sys.stderr)
            return 2

    if not goal:
        print("ERROR: Either --goal or --goal-file must be specified.", file=sys.stderr)
        return 2

    if args.provider == "openrouter" and not args.model:
        print("ERROR: --provider openrouter requires an explicit --model.", file=sys.stderr)
        return 2

    proj = _resolve_project(project_key)
    if proj is None:
        print(f"ERROR: project_key not registered: {project_key}. Run 'init' first.",
              file=sys.stderr)
        return 2

    # Goal is recorded as a milestone scope-baseline (requirement aspect) so the
    # scope-drift gate has a baseline against the operator's stated intent.
    milestone = args.milestone or "M6"

    # Persist goal as scope baseline (if a run will be created, register it first
    # via the canonical db.register_run so checkpoint identity is consistent).
    import uuid as _uuid
    thread_uuid = str(_uuid.uuid4())

    # The graph's start node will register the run + upsert milestone in DB.
    # We pre-record the goal as a scope baseline here for the requirement aspect.
    # If the run has not yet been registered, the baseline will simply be stored
    # against the project_id and picked up by the gate node.
    project_id = proj["id"]

    # Pre-create the run row to capture the thread_uuid for operator reporting.
    try:
        run_db_id = wf_db.register_run(project_id, thread_uuid)
    except Exception as exc:
        print(f"ERROR: could not register run: {exc}", file=sys.stderr)
        return 2

    try:
        wf_db.set_scope_baseline(run_db_id, project_id, "requirements", goal)
        wf_db.set_scope_baseline(run_db_id, project_id, "operator_goal", goal)
    except Exception as exc:
        print(f"WARN: could not record goal scope baseline: {exc}", file=sys.stderr)

    # Mark run as running with current milestone
    wf_db.update_run_status(run_db_id, "running", current_milestone=milestone)

    # Execute the graph (uses canonical PostgresSaver)
    try:
        result = run_workflow(
            project_id=project_id,
            project_key=project_key,
            milestone_key=milestone,
            thread_uuid=thread_uuid,
            conninfo=_pg_conninfo(),
            provider=args.provider,
            model=args.model,
        )
    except Exception as exc:
        wf_db.update_run_status(run_db_id, "failed")
        print(f"ERROR: workflow run failed: {exc}", file=sys.stderr)
        return 2

    payload = {
        "timestamp": _now_iso(),
        "ok": True,
        "project_id": project_id,
        "project_key": project_key,
        "milestone": milestone,
        "thread_uuid": thread_uuid,
        "run_db_id": run_db_id,
        "completed": result.get("completed", False),
        "judge_verdict": result.get("judge_verdict", ""),
        "score": result.get("score", 0.0),
        "evidence_count": result.get("evidence_count", 0),
        "errors": result.get("errors", []),
        "checkpoint": _checkpoint_summary(thread_uuid),
    }
    _print_json_or_text(
        payload,
        args.json,
        lambda p: (
            f"Workflow run started\n"
            f"  project_key:    {p['project_key']}\n"
            f"  milestone:      {p['milestone']}\n"
            f"  thread_uuid:    {p['thread_uuid']}\n"
            f"  run_db_id:      {p['run_db_id']}\n"
            f"  completed:      {p['completed']}\n"
            f"  judge_verdict:  {p['judge_verdict']}\n"
            f"  score:          {p['score']}\n"
            f"  evidence:       {p['evidence_count']}\n"
            f"  checkpoints:    {p['checkpoint'].get('checkpoint_count', 'n/a')}\n"
        ),
    )
    return 0 if result.get("completed") or result.get("judge_verdict") in (
        "proceed", "needs_operator"
    ) else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show project, run, thread, Milestone, node, checkpoint, blockers.

    --project-key    (optional) filter to project
    --thread         (optional) thread UUID (default: latest for project)
    --run            (optional) wf_runs.id UUID
    """
    psycopg, dict_row = _import_psycopg()
    if psycopg is None:
        print("ERROR: psycopg not installed", file=sys.stderr)
        return 2

    run = None
    if args.run or args.thread:
        run = _find_run(args.thread, args.run)
        if run is None:
            print(f"ERROR: run not found (thread={args.thread}, run={args.run})",
                  file=sys.stderr)
            return 2
    elif args.project_key:
        proj = _resolve_project(args.project_key)
        if proj is None:
            print(f"ERROR: project not found: {args.project_key}", file=sys.stderr)
            return 2
        ci = _pg_conninfo()
        with psycopg.connect(ci, row_factory=dict_row) as c:
            row = c.execute(
                "SELECT id, langgraph_thread, project_id, status, current_milestone, "
                "current_macro, current_micro, ab_enabled, started_at, updated_at, completed_at "
                "FROM agentcore.wf_runs WHERE project_id = %s "
                "ORDER BY started_at DESC LIMIT 1",
                (proj["id"],),
            ).fetchone()
            run = dict(row) if row else None

    if run is None:
        payload = {
            "timestamp": _now_iso(),
            "ok": True,
            "runs": [],
            "blockers": ["no run found for given filter"],
        }
        _print_json_or_text(payload, args.json)
        return 1

    pause = _pending_pause(run["id"])
    checkpoint = _checkpoint_summary(run["langgraph_thread"])

    blockers: list[str] = []
    if pause:
        blockers.append(f"human_pause_pending={pause['id']}")
    if run["status"] == "failed":
        blockers.append("run_status=failed")
    if run["status"] == "cancelled":
        blockers.append("run_status=cancelled")

    payload = {
        "timestamp": _now_iso(),
        "ok": len(blockers) == 0,
        "run": {
            "run_db_id": run["id"],
            "thread_uuid": run["langgraph_thread"],
            "project_id": run["project_id"],
            "status": run["status"],
            "current_milestone": run["current_milestone"],
            "current_macro": run["current_macro"],
            "current_micro": run["current_micro"],
            "ab_enabled": run["ab_enabled"],
            "started_at": run["started_at"],
            "updated_at": run["updated_at"],
            "completed_at": run["completed_at"],
        },
        "checkpoint": checkpoint,
        "human_pause": pause,
        "blockers": blockers,
    }

    def _render(p: dict) -> None:
        r = p["run"]
        ck = p["checkpoint"]
        print(f"Workflow Status — {p['timestamp']}")
        print(f"  run_db_id:        {r['run_db_id']}")
        print(f"  thread_uuid:      {r['thread_uuid']}")
        print(f"  project_id:       {r['project_id']}")
        print(f"  status:           {r['status']}")
        print(f"  milestone:        {r['current_milestone']}")
        print(f"  macro/micro:      {r['current_macro']} / {r['current_micro']}")
        print(f"  ab_enabled:       {r['ab_enabled']}")
        print(f"  started_at:       {r['started_at']}")
        print(f"  updated_at:       {r['updated_at']}")
        print(f"  checkpoints:      {ck.get('checkpoint_count', 'n/a')}")
        if ck.get("latest_node"):
            print(f"  latest_node:      {ck['latest_node']}")
        if p["human_pause"]:
            hp = p["human_pause"]
            print(f"  pending pause:    {hp['id']} scope={hp['scope_key']}")
        if p["blockers"]:
            print(f"  blockers:         {', '.join(p['blockers'])}")

    _print_json_or_text(payload, args.json, _render)
    return 0 if len(blockers) == 0 else 1


def cmd_pause(args: argparse.Namespace) -> int:
    """Show details of the pending human pause for a run/thread."""
    run = _find_run(args.thread, args.run)
    if run is None:
        print("ERROR: run not found", file=sys.stderr)
        return 2
    pause = _pending_pause(run["id"])
    if pause is None:
        payload = {"timestamp": _now_iso(), "ok": True, "pause": None,
                   "note": "no pending pause for this run"}
        _print_json_or_text(payload, args.json)
        return 0
    payload = {"timestamp": _now_iso(), "ok": True, "pause": pause}
    _print_json_or_text(payload, args.json, lambda p: (
        f"Pending pause\n  id:        {p['pause']['id']}\n"
        f"  scope:     {p['pause']['scope_key']}\n"
        f"  question:  {p['pause']['question']}\n"
        f"  requested: {p['pause']['requested_at']}\n"
    ))
    return 0


def _resolve_pause_and_resume(args: argparse.Namespace, resolution: str, decision_word: str) -> int:
    """Shared implementation for approve / reject."""
    run = _find_run(args.thread, args.run)
    if run is None:
        print("ERROR: run not found", file=sys.stderr)
        return 2
    pause = _pending_pause(run["id"])
    if pause is None:
        print("ERROR: no pending pause for this run", file=sys.stderr)
        return 2

    notes = args.notes or ""
    wf_db.resolve_pause(pause["id"], run["project_id"], resolution, decision_word, notes)
    wf_db.update_run_status(run["id"], "running")

    try:
        result = run_workflow(
            project_id=run["project_id"],
            project_key=args.project_key or "",
            milestone_key=run["current_milestone"] or "M6",
            thread_uuid=run["langgraph_thread"],
            resume_from={"decision": decision_word, "resolution": resolution, "notes": notes},
            conninfo=_pg_conninfo(),
        )
        resumed_ok = True
    except Exception as exc:
        wf_db.update_run_status(run["id"], "failed")
        print(f"ERROR: resume failed: {exc}", file=sys.stderr)
        resumed_ok = False
        result = {"errors": [str(exc)]}

    payload = {
        "timestamp": _now_iso(),
        "ok": resumed_ok,
        "pause_id": pause["id"],
        "resolution": resolution,
        "decision_word": decision_word,
        "run_db_id": run["id"],
        "thread_uuid": run["langgraph_thread"],
        "judge_verdict": result.get("judge_verdict", ""),
        "score": result.get("score", 0.0),
        "evidence_count": result.get("evidence_count", 0),
        "errors": result.get("errors", []),
    }
    _print_json_or_text(
        payload,
        args.json,
        lambda p: (
            f"Pause {p['resolution']} ({p['decision_word']}); run resumed.\n"
            f"  pause_id:    {p['pause_id']}\n"
            f"  run_db_id:   {p['run_db_id']}\n"
            f"  judge:       {p['judge_verdict']}\n"
            f"  score:       {p['score']}\n"
            f"  evidence:    {p['evidence_count']}\n"
        ),
    )
    return 0 if resumed_ok else 2


def cmd_approve(args: argparse.Namespace) -> int:
    return _resolve_pause_and_resume(args, "approved", "approve")


def cmd_reject(args: argparse.Namespace) -> int:
    return _resolve_pause_and_resume(args, "rejected", "reject")


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a paused run from the canonical PostgresSaver.

    If a human pause is pending, this command is equivalent to a no-op
    until the operator runs `approve` / `reject`. Use `approve` or `reject`
    for resume-after-pause; this command handles resume-after-process-restart.
    """
    run = _find_run(args.thread, args.run)
    if run is None:
        print("ERROR: run not found", file=sys.stderr)
        return 2
    pause = _pending_pause(run["id"])
    if pause is not None:
        payload = {
            "timestamp": _now_iso(),
            "ok": False,
            "note": "human pause pending — use 'approve' or 'reject'",
            "pause": pause,
            "run_db_id": run["id"],
            "thread_uuid": run["langgraph_thread"],
        }
        _print_json_or_text(payload, args.json)
        return 1
    try:
        result = run_workflow(
            project_id=run["project_id"],
            project_key=args.project_key or "",
            milestone_key=run["current_milestone"] or "M6",
            thread_uuid=run["langgraph_thread"],
            resume_from=None,
            conninfo=_pg_conninfo(),
        )
    except Exception as exc:
        wf_db.update_run_status(run["id"], "failed")
        print(f"ERROR: resume failed: {exc}", file=sys.stderr)
        return 2
    payload = {
        "timestamp": _now_iso(),
        "ok": True,
        "run_db_id": run["id"],
        "thread_uuid": run["langgraph_thread"],
        "completed": result.get("completed", False),
        "judge_verdict": result.get("judge_verdict", ""),
        "score": result.get("score", 0.0),
        "evidence_count": result.get("evidence_count", 0),
    }
    _print_json_or_text(
        payload,
        args.json,
        lambda p: (
            f"Workflow resumed\n"
            f"  run_db_id:    {p['run_db_id']}\n"
            f"  thread_uuid:  {p['thread_uuid']}\n"
            f"  completed:    {p['completed']}\n"
            f"  judge:        {p['judge_verdict']}\n"
            f"  score:        {p['score']}\n"
        ),
    )
    return 0


def cmd_cancel(args: argparse.Namespace) -> int:
    """Transition a run to aborted; never delete evidence.

    M6 canonical run statuses: running / paused_human / paused_gate /
    completed / failed / aborted. Cancellation maps to ``aborted`` so the
    ``wf_run_status`` enum accepts it.
    """
    run = _find_run(args.thread, args.run)
    if run is None:
        print("ERROR: run not found", file=sys.stderr)
        return 2
    if run["status"] == "aborted":
        payload = {"timestamp": _now_iso(), "ok": True,
                   "note": "already aborted", "run_db_id": run["id"]}
        _print_json_or_text(payload, args.json)
        return 0
    # Resolve any pending pause with operator-overridden decision so the graph
    # can unwind cleanly without losing evidence.
    pause = _pending_pause(run["id"])
    if pause:
        wf_db.resolve_pause(pause["id"], run["project_id"], "overridden",
                            "cancelled_by_operator", args.reason or "")
    wf_db.update_run_status(run["id"], "aborted")
    payload = {
        "timestamp": _now_iso(),
        "ok": True,
        "run_db_id": run["id"],
        "thread_uuid": run["langgraph_thread"],
        "previous_status": run["status"],
        "new_status": "aborted",
        "evidence_preserved": True,
        "reason": args.reason or "",
    }
    _print_json_or_text(
        payload,
        args.json,
        lambda p: (
            f"Workflow aborted (evidence preserved)\n"
            f"  run_db_id:        {p['run_db_id']}\n"
            f"  thread_uuid:      {p['thread_uuid']}\n"
            f"  prev_status:      {p['previous_status']}\n"
            f"  reason:           {p['reason']}\n"
        ),
    )
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    """Tail workflow activity: recent wf_evidence + run status changes."""
    run = _find_run(args.thread, args.run)
    if run is None:
        print("ERROR: run not found", file=sys.stderr)
        return 2
    psycopg, dict_row = _import_psycopg()
    ci = _pg_conninfo()
    limit = args.limit or 25
    with psycopg.connect(ci, row_factory=dict_row) as c:
        rows = c.execute(
            """
            SELECT scope_key, evidence_type, summary, trust_class, created_at
            FROM agentcore.wf_evidence
            WHERE run_id = %s
            ORDER BY created_at DESC LIMIT %s
            """,
            (run["id"], limit),
        ).fetchall()
    payload = {
        "timestamp": _now_iso(),
        "run_db_id": run["id"],
        "thread_uuid": run["langgraph_thread"],
        "evidence": [dict(r) for r in rows],
    }

    def _render(p: dict) -> None:
        print(f"Workflow evidence (latest {len(p['evidence'])} of run {p['run_db_id']})")
        for ev in p["evidence"]:
            print(f"  {ev['created_at']}  {ev['evidence_type']:<20} {ev['scope_key']}")
            print(f"    {ev['summary'][:140]}")

    _print_json_or_text(payload, args.json, _render)
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    """List every recorded evidence row for a run."""
    run = _find_run(args.thread, args.run)
    if run is None:
        print("ERROR: run not found", file=sys.stderr)
        return 2
    psycopg, dict_row = _import_psycopg()
    ci = _pg_conninfo()
    with psycopg.connect(ci, row_factory=dict_row) as c:
        rows = c.execute(
            """
            SELECT scope_key, evidence_type, summary, detail, trust_class, created_at
            FROM agentcore.wf_evidence
            WHERE run_id = %s
            ORDER BY created_at ASC
            """,
            (run["id"],),
        ).fetchall()
    payload = {
        "timestamp": _now_iso(),
        "run_db_id": run["id"],
        "thread_uuid": run["langgraph_thread"],
        "evidence_count": len(rows),
        "evidence": [dict(r) for r in rows],
    }
    _print_json_or_text(
        payload,
        args.json,
        lambda p: f"Run {p['run_db_id']}: {p['evidence_count']} evidence rows (use --json for full detail)",
    )
    return 0


def cmd_topology(args: argparse.Namespace) -> int:
    """Show the shared graph topology fingerprint."""
    t = build_topology()
    fp = topology_fingerprint(t)
    payload = {
        "timestamp": _now_iso(),
        "topology_fingerprint_sha256": fp,
        "node_count": 15,
        "interrupt_before": ["human_pause"],
        "checkpointer_production": "agentcore_workflow.workflow.build_graph -> PostgresSaver",
        "checkpointer_studio": "agentcore_workflow.workflow.build_studio_graph -> Agent Server dev checkpointer",
        "note": (
            "Production and Studio share the same topology. Topology fingerprint is "
            "stable for the current graph; do NOT edit without explicit operator approval."
        ),
    }
    _print_json_or_text(
        payload,
        args.json,
        lambda p: (
            f"Graph topology fingerprint: {p['topology_fingerprint_sha256']}\n"
            f"  node_count:           {p['node_count']}\n"
            f"  interrupt_before:     {p['interrupt_before']}\n"
        ),
    )
    return 0


def cmd_studio(args: argparse.Namespace) -> int:
    """Start LangGraph Studio (Agent Server) for this graph.

    This is a dev/debug surface only. Production persistence uses the
    canonical PostgresSaver; Studio uses an Agent Server dev checkpointer
    and stays localhost-only.
    """
    # Hand off to the Studio CLI shim. We import lazily so a missing
    # langgraph CLI does not break the rest of the workflow CLI.
    from .studio import run_studio
    return run_studio(args)


def cmd_models(args: argparse.Namespace) -> int:
    """Display sanitized current available model IDs, context lengths, profile mapping, and availability."""
    if args.provider != "openrouter":
        print(f"ERROR: --provider {args.provider} is not supported. Only 'openrouter' is supported.", file=sys.stderr)
        return 2

    # Sanitized current verified models from the contract or API
    models_data = [
        {"model_id": "minimax/minimax-m3", "display_name": "MiniMax-M3", "context_length": 1048576, "input_price": "$0.55/M", "output_price": "$1.10/M", "profile_mapping": "autonomous-os"},
        {"model_id": "deepseek/deepseek-v4-pro", "display_name": "DeepSeek V4 Pro", "context_length": 1048576, "input_price": "$0.14/M", "output_price": "$0.28/M", "profile_mapping": "autonomous-deepseek-pro"},
        {"model_id": "openai/gpt-5.6-sol", "display_name": "GPT-5.6 Sol", "context_length": 1048576, "input_price": "$2.50/M", "output_price": "$10.00/M", "profile_mapping": "autonomous-gpt-sol"},
        {"model_id": "minimax/minimax-m2.7", "display_name": "MiniMax M2.7", "context_length": 204800, "input_price": "$0.10/M", "output_price": "$0.20/M", "profile_mapping": "autonomous-minimax-m27"},
    ]
    
    payload = {
        "timestamp": _now_iso(),
        "provider": "openrouter",
        "api_base": "https://openrouter.ai/api/v1",
        "models": models_data
    }
    
    def _render(p: dict) -> None:
        print(f"OpenRouter Model Catalog ({p['timestamp']})")
        print(f"{'Model ID':<30} | {'Display Name':<25} | {'Context':<10} | {'Pricing (In/Out)':<18} | {'Profile'}")
        print("-" * 100)
        for m in p["models"]:
            pricing = f"{m['input_price']}/{m['output_price']}"
            print(f"{m['model_id']:<30} | {m['display_name']:<25} | {m['context_length']:<10} | {pricing:<18} | {m['profile_mapping']}")

    _print_json_or_text(payload, args.json, _render)
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m agentcore workflow",
        description=(
            "AgentCore autonomous LangGraph workflow operator launcher. "
            "Reuses the canonical PostgresSaver; never requires writing custom Python."
        ),
    )
    sub = p.add_subparsers(dest="subcommand", required=True)

    p_init = sub.add_parser("init", help="Register/update project + scaffold isolated worktree")
    p_init.add_argument("--project-key", required=True)
    p_init.add_argument("--project-name", default=None)
    p_init.add_argument("--target", required=True,
                        help="absolute path to project source root (e.g. D:\\projects\\foo)")
    p_init.add_argument("--worktree", default=None,
                        help="absolute path to the isolated worktree")
    p_init.add_argument("--git-remote", default=None,
                        help="origin URL for the project (recorded; no fetch/push here)")
    p_init.add_argument("--json", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_start = sub.add_parser("start", help="Start a new autonomous workflow run")
    p_start.add_argument("--project-key", default=None)
    p_start.add_argument("--project", default=None, help="Project key or absolute project root path")
    p_start.add_argument("--goal", default=None,
                         help="operator goal (free text; recorded as requirement scope)")
    p_start.add_argument("--goal-file", default=None,
                         help="Path to goal file (recorded as requirement scope)")
    p_start.add_argument("--milestone", default="M6")
    p_start.add_argument("--provider", default=None, help="LLM provider (e.g., 'openrouter')")
    p_start.add_argument("--model", default=None, help="Selected model ID")
    p_start.add_argument("--json", action="store_true")
    p_start.set_defaults(func=cmd_start)

    p_status = sub.add_parser("status", help="Show project/run/thread/checkpoint/blockers")
    p_status.add_argument("--project-key", default=None)
    p_status.add_argument("--thread", default=None, help="LangGraph thread UUID")
    p_status.add_argument("--run", default=None, help="wf_runs.id UUID")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_pause = sub.add_parser("pause", help="Show pending human pause details")
    p_pause.add_argument("--thread", default=None)
    p_pause.add_argument("--run", default=None)
    p_pause.add_argument("--json", action="store_true")
    p_pause.set_defaults(func=cmd_pause)

    for name, resolution, word in (
        ("approve", "approved", "approve"),
        ("reject", "rejected", "reject"),
    ):
        p_x = sub.add_parser(name, help=f"Resolve pause as {resolution} and resume run")
        p_x.add_argument("--thread", default=None)
        p_x.add_argument("--run", default=None)
        p_x.add_argument("--project-key", default=None)
        p_x.add_argument("--notes", default="")
        p_x.add_argument("--json", action="store_true")
        p_x.set_defaults(func=cmd_approve if name == "approve" else cmd_reject)

    p_resume = sub.add_parser("resume", help="Resume a paused run from PostgreSQL checkpoints")
    p_resume.add_argument("--thread", default=None)
    p_resume.add_argument("--run", default=None)
    p_resume.add_argument("--project-key", default=None)
    p_resume.add_argument("--json", action="store_true")
    p_resume.set_defaults(func=cmd_resume)

    p_cancel = sub.add_parser("cancel", help="Cancel a run safely (evidence preserved)")
    p_cancel.add_argument("--thread", default=None)
    p_cancel.add_argument("--run", default=None)
    p_cancel.add_argument("--reason", default="")
    p_cancel.add_argument("--json", action="store_true")
    p_cancel.set_defaults(func=cmd_cancel)

    p_logs = sub.add_parser("logs", help="Tail recent workflow evidence for a run")
    p_logs.add_argument("--thread", default=None)
    p_logs.add_argument("--run", default=None)
    p_logs.add_argument("--limit", type=int, default=25)
    p_logs.add_argument("--json", action="store_true")
    p_logs.set_defaults(func=cmd_logs)

    p_ev = sub.add_parser("evidence", help="List all evidence for a run")
    p_ev.add_argument("--thread", default=None)
    p_ev.add_argument("--run", default=None)
    p_ev.add_argument("--json", action="store_true")
    p_ev.set_defaults(func=cmd_evidence)

    p_top = sub.add_parser("topology", help="Show the shared graph topology fingerprint")
    p_top.add_argument("--json", action="store_true")
    p_top.set_defaults(func=cmd_topology)

    p_studio = sub.add_parser("studio", help="Start LangGraph Studio (Agent Server) dev server")
    p_studio.add_argument("--port", type=int, default=2024,
                          help="local Agent Server port (default 2024)")
    p_studio.add_argument("--no-browser", action="store_true",
                          help="do not auto-open Studio in the default browser")
    p_studio.add_argument("--json", action="store_true")
    p_studio.set_defaults(func=cmd_studio)

    p_models = sub.add_parser("models", help="Display available provider models")
    p_models.add_argument("--provider", required=True)
    p_models.add_argument("--json", action="store_true")
    p_models.set_defaults(func=cmd_models)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
