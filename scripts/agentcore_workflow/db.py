"""AgentCore M6 — Database helpers for workflow nodes (wf_ schema).

All writes go through SECURITY DEFINER functions that enforce project isolation.
Never issue raw SQL against evidence tables from normal agent code.

Tables use wf_ prefix (e.g. wf_runs, wf_milestones) to avoid conflict with
M2 identity tables (workflows, workflow_threads).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

PG_DSN = (
    f"host=127.0.0.1 port=55433 dbname=agent_core "
    f"user=agentcore_worker password={os.environ.get('AGENT_CORE_POSTGRES_PASSWORD', '')}"
)
PG_DSN_ADMIN = (
    f"host=127.0.0.1 port=55433 dbname=agent_core "
    f"user=postgres password={os.environ.get('AGENT_CORE_POSTGRES_PASSWORD', '')}"
)


def conn(admin: bool = False) -> psycopg.Connection:
    return psycopg.connect(PG_DSN_ADMIN if admin else PG_DSN, row_factory=dict_row)


# ─────────────────────────────────────────────────────────────────────────────
# Run registration
# ─────────────────────────────────────────────────────────────────────────────

def register_run(project_id: str, langgraph_thread: str, session_id: Optional[str] = None) -> str:
    """Register a workflow run (idempotent on thread_id)."""
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT agentcore.register_wf_run(%s, %s, %s) AS id",
            (project_id, langgraph_thread, session_id),
        ).fetchone()
        return str(row["id"])


def set_run_model_selection(run_db_id: str, provider: str, model: str) -> None:
    """Persist the operator's explicit provider/model selection on the run row.

    Stored in wf_runs.metadata so the selection survives process termination
    independently of LangGraph checkpoint state.
    """
    import json as _json

    selection = {"provider": provider, "model": model}
    with conn(admin=True) as c:
        c.execute(
            """
            UPDATE agentcore.wf_runs
            SET metadata = metadata || jsonb_build_object('model_selection', %s::jsonb),
                updated_at = now()
            WHERE id = %s
            """,
            (_json.dumps(selection), run_db_id),
        )


def get_run_model_selection(run_db_id: str) -> Optional[dict]:
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT metadata -> 'model_selection' AS sel FROM agentcore.wf_runs WHERE id = %s",
            (run_db_id,),
        ).fetchone()
        return row["sel"] if row and row["sel"] else None


def update_run_status(run_db_id: str, status: str, **kwargs: Any) -> None:
    set_clauses = ["status = %s", "updated_at = now()"]
    params: list = [status]
    for k, v in kwargs.items():
        if k in ("current_milestone", "current_macro", "current_micro"):
            set_clauses.append(f"{k} = %s")
            params.append(v)
    params.append(run_db_id)
    with conn(admin=True) as c:
        c.execute(
            f"UPDATE agentcore.wf_runs SET {', '.join(set_clauses)} WHERE id = %s",
            params,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Milestone / Macro / Micro upserts
# ─────────────────────────────────────────────────────────────────────────────

def upsert_charter(
    project_id: str,
    title: str,
    goal: str,
    locked_milestones: list | None = None,
    acceptance_criteria: list | None = None,
    *,
    lock: bool = True,
    locked_by: str = "workflow_start",
) -> str:
    """Insert the next immutable charter version for a project (wf_charters)."""
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_charters
                (project_id, version, title, goal, locked_milestones, acceptance_criteria,
                 locked_at, locked_by)
            SELECT
                %s,
                COALESCE((SELECT MAX(version) FROM agentcore.wf_charters WHERE project_id = %s), 0) + 1,
                %s, %s, %s::jsonb, %s::jsonb,
                CASE WHEN %s THEN now() ELSE NULL END,
                CASE WHEN %s THEN %s ELSE NULL END
            RETURNING id
            """,
            (
                project_id,
                project_id,
                title,
                goal,
                json.dumps(locked_milestones or []),
                json.dumps(acceptance_criteria or []),
                lock,
                lock,
                locked_by,
            ),
        ).fetchone()
        return str(row["id"])


def persist_step_catalogue(
    milestone_db_id: str,
    project_id: str,
    macro_steps: list[dict],
    micro_steps: list[dict],
    checklist_items: list[dict] | None = None,
) -> dict[str, str]:
    """Upsert macro/micro/checklist rows for a milestone. Returns micro_key → id map."""
    macro_ids: dict[str, str] = {}
    for macro in sorted(macro_steps, key=lambda x: int(x.get("ordinal") or 0)):
        macro_ids[macro["key"]] = upsert_macro_step(
            milestone_db_id,
            project_id,
            macro["key"],
            macro.get("label") or macro["key"],
            int(macro.get("ordinal") or 0),
            macro.get("risk_class") or "low",
        )

    micro_ids: dict[str, str] = {}
    for micro in sorted(micro_steps, key=lambda x: int(x.get("ordinal") or 0)):
        macro_id = macro_ids.get(str(micro.get("macro_key") or ""))
        if not macro_id:
            continue
        micro_ids[micro["key"]] = upsert_micro_step(
            macro_id,
            project_id,
            micro["key"],
            micro.get("label") or micro["key"],
            int(micro.get("ordinal") or 0),
            micro.get("risk_class") or "low",
        )

    for item in checklist_items or []:
        micro_id = micro_ids.get(str(item.get("micro_key") or ""))
        if not micro_id:
            continue
        upsert_checklist_item(
            micro_id,
            project_id,
            item["key"],
            item.get("label") or item["key"],
            int(item.get("ordinal") or 0),
        )
    return micro_ids


def upsert_milestone(run_db_id: str, project_id: str, milestone_key: str, label: str) -> str:
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_milestones
                (run_id, project_id, milestone_key, label, status, started_at)
            VALUES (%s, %s, %s, %s, 'running', now())
            ON CONFLICT (run_id, milestone_key) DO UPDATE
                SET status = 'running',
                    started_at = COALESCE(agentcore.wf_milestones.started_at, now())
            RETURNING id
            """,
            (run_db_id, project_id, milestone_key, label),
        ).fetchone()
        return str(row["id"])


def upsert_macro_step(milestone_db_id: str, project_id: str, step_key: str, label: str, ordinal: int, risk_class: str = "low") -> str:
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_macro_steps
                (milestone_id, project_id, step_key, label, ordinal, risk_class, status)
            VALUES (%s, %s, %s, %s, %s, %s::agentcore.wf_risk_class, 'pending')
            ON CONFLICT (milestone_id, step_key) DO UPDATE
                SET label = EXCLUDED.label, risk_class = EXCLUDED.risk_class
            RETURNING id
            """,
            (milestone_db_id, project_id, step_key, label, ordinal, risk_class),
        ).fetchone()
        return str(row["id"])


def set_macro_step_status(macro_db_id: str, status: str) -> None:
    ts = "started_at = COALESCE(started_at, now())" if status == "running" else (
        "completed_at = now()" if status == "completed" else None
    )
    extra = f", {ts}" if ts else ""
    with conn(admin=True) as c:
        c.execute(
            f"UPDATE agentcore.wf_macro_steps SET status = %s::agentcore.wf_step_status{extra} WHERE id = %s",
            (status, macro_db_id),
        )


def upsert_micro_step(macro_db_id: str, project_id: str, step_key: str, label: str, ordinal: int, risk_class: str = "low") -> str:
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_micro_steps
                (macro_id, project_id, step_key, label, ordinal, risk_class, status)
            VALUES (%s, %s, %s, %s, %s, %s::agentcore.wf_risk_class, 'pending')
            ON CONFLICT (macro_id, step_key) DO UPDATE
                SET label = EXCLUDED.label, risk_class = EXCLUDED.risk_class
            RETURNING id
            """,
            (macro_db_id, project_id, step_key, label, ordinal, risk_class),
        ).fetchone()
        return str(row["id"])


def set_micro_step_result(
    micro_db_id: str,
    status: str,
    det_checks_passed: Optional[bool] = None,
    score: Optional[float] = None,
    judge_verdict: Optional[str] = None,
    jit_lease_id: Optional[str] = None,
) -> None:
    updates = ["status = %s::agentcore.wf_step_status"]
    params: list = [status]
    if det_checks_passed is not None:
        updates.append("deterministic_checks_passed = %s")
        params.append(det_checks_passed)
    if score is not None:
        updates.append("score = %s")
        params.append(score)
    if judge_verdict is not None:
        updates.append("judge_verdict = %s::agentcore.wf_judge_verdict")
        params.append(judge_verdict)
    if jit_lease_id:
        updates.append("jit_lease_id = %s")
        params.append(jit_lease_id)
    if status in ("completed", "failed"):
        updates.append("completed_at = now()")
    elif status == "running":
        updates.append("started_at = COALESCE(started_at, now())")
    params.append(micro_db_id)
    with conn(admin=True) as c:
        c.execute(
            f"UPDATE agentcore.wf_micro_steps SET {', '.join(updates)} WHERE id = %s",
            params,
        )


def upsert_checklist_item(micro_db_id: str, project_id: str, item_key: str, label: str, ordinal: int) -> str:
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_checklist_items
                (micro_id, project_id, item_key, label, ordinal, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            ON CONFLICT (micro_id, item_key) DO UPDATE SET label = EXCLUDED.label
            RETURNING id
            """,
            (micro_db_id, project_id, item_key, label, ordinal),
        ).fetchone()
        return str(row["id"])


def set_checklist_item_status(item_db_id: str, status: str, evidence: Optional[str] = None) -> None:
    with conn(admin=True) as c:
        c.execute(
            """
            UPDATE agentcore.wf_checklist_items
            SET status = %s, evidence = %s,
                completed_at = CASE WHEN %s = 'completed' THEN now() ELSE NULL END
            WHERE id = %s
            """,
            (status, evidence, status, item_db_id),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Gate records
# ─────────────────────────────────────────────────────────────────────────────

def record_gate(run_db_id: str, project_id: str, gate_name: str, scope_key: str, verdict: str, details: dict) -> str:
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT agentcore.record_wf_gate(%s, %s, %s, %s, %s::agentcore.wf_gate_verdict, %s) AS id",
            (run_db_id, project_id, gate_name, scope_key, verdict, json.dumps(details)),
        ).fetchone()
        return str(row["id"])


# ─────────────────────────────────────────────────────────────────────────────
# Scope baselines
# ─────────────────────────────────────────────────────────────────────────────

def set_scope_baseline(run_db_id: str, project_id: str, aspect: str, content: str) -> None:
    with conn(admin=True) as c:
        c.execute(
            "SELECT agentcore.set_wf_scope_baseline(%s, %s, %s, %s)",
            (run_db_id, project_id, aspect, content),
        )


def check_scope_drift(run_db_id: str, project_id: str, aspect: str, current: str) -> bool:
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT agentcore.check_wf_scope_drift(%s, %s, %s, %s) AS drifted",
            (run_db_id, project_id, aspect, current),
        ).fetchone()
        return bool(row["drifted"])


# ─────────────────────────────────────────────────────────────────────────────
# Human pause
# ─────────────────────────────────────────────────────────────────────────────

def create_pause(run_db_id: str, project_id: str, scope_key: str, question: str, context_summary: str = "") -> str:
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT agentcore.create_wf_pause(%s, %s, %s, %s, %s) AS id",
            (run_db_id, project_id, scope_key, question, context_summary),
        ).fetchone()
        return str(row["id"])


def resolve_pause(pause_db_id: str, project_id: str, resolution: str, decision: str, notes: str = "") -> None:
    with conn(admin=True) as c:
        c.execute(
            "SELECT agentcore.resolve_wf_pause(%s, %s, %s::agentcore.wf_pause_resolution, %s, %s)",
            (pause_db_id, project_id, resolution, decision, notes),
        )


def get_pause_status(pause_db_id: str) -> dict:
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT resolution, operator_decision, operator_notes, resolved_at "
            "FROM agentcore.wf_human_pauses WHERE id = %s",
            (pause_db_id,),
        ).fetchone()
        return dict(row) if row else {}


# ─────────────────────────────────────────────────────────────────────────────
# Capability profiles and JIT leases
# ─────────────────────────────────────────────────────────────────────────────

def set_capability_state(
    project_id: str,
    tool_name: str,
    state: str,
    milestone_key: Optional[str] = None,
    reason: Optional[str] = None,
    requires_operator: bool = False,
) -> str:
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT agentcore.set_capability_state(%s, %s, %s::agentcore.wf_capability_state, %s, %s, %s) AS id",
            (project_id, tool_name, state, milestone_key, reason, requires_operator),
        ).fetchone()
        return str(row["id"])


def get_project_tools(project_id: str) -> list[dict]:
    with conn(admin=True) as c:
        rows = c.execute(
            "SELECT * FROM agentcore.get_project_tools(%s)",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_source_identity_for_project(project_id: str) -> Optional[str]:
    """Get or create a source_identity row for the agentcore_worker role."""
    with conn(admin=True) as c:
        # Try to find an existing identity for this project
        row = c.execute(
            "SELECT id FROM agentcore.source_identities WHERE project_id = %s LIMIT 1",
            (project_id,),
        ).fetchone()
        if row:
            return str(row["id"])
        return None


def _is_openrouter_lease_tool(tool_name: str) -> bool:
    if not tool_name:
        return False
    if tool_name.startswith("openrouter"):
        return True
    # Exact tool names from the OpenRouter registry groups.
    known = {
        "list-models", "get-model", "list-model-endpoints", "list-providers",
        "list-daily-model-rankings", "list-app-rankings", "list-benchmarks",
        "list-task-classifications", "search-docs", "view-skills", "ping",
        "get-preset", "list-presets", "get-credits", "get-generation", "send-feedback",
        "generate-speech", "transcribe-audio",
        "openrouter-discovery-read", "openrouter-account",
        "openrouter-media-generation", "openrouter-transcription",
    }
    return tool_name in known


def _bridge_grant_for_tool(tool_name: str) -> None:
    """Best-effort Bifrost VK grant. Failure leaves tools hidden."""
    if not _is_openrouter_lease_tool(tool_name):
        return
    try:
        import sys
        from pathlib import Path

        bifrost_dir = str(Path(__file__).resolve().parents[1] / "bifrost")
        if bifrost_dir not in sys.path:
            sys.path.insert(0, bifrost_dir)
        import jit_vk_bridge as bridge  # type: ignore

        if tool_name in {
            "openrouter-discovery-read",
            "openrouter-account",
            "openrouter-media-generation",
            "openrouter-transcription",
        }:
            result = bridge.sync_lease_group(tool_name, active=True)
        else:
            result = bridge.grant_tools([tool_name])
        try:
            from .mcp_client import bump_lease_epoch

            bump_lease_epoch()
        except Exception:
            pass
        if not result.ok:
            # Do not raise — PG lease remains; tools stay hidden on failure.
            return
    except Exception:
        return


def _bridge_revoke_openrouter() -> None:
    try:
        import sys
        from pathlib import Path

        bifrost_dir = str(Path(__file__).resolve().parents[1] / "bifrost")
        if bifrost_dir not in sys.path:
            sys.path.insert(0, bifrost_dir)
        import jit_vk_bridge as bridge  # type: ignore

        bridge.revoke_openrouter_tools()
        try:
            from .mcp_client import bump_lease_epoch

            bump_lease_epoch()
        except Exception:
            pass
    except Exception:
        return


def create_jit_lease(project_id: str, tool_name: str, step_id: str, lease_seconds: int, justification: str) -> str:
    """Create a JIT capability lease and sync capability profile to jit_leased."""
    ident_id = get_source_identity_for_project(project_id)
    if not ident_id:
        # Create a minimal source_identity placeholder for the JIT lease holder
        with conn(admin=True) as c:
            machine = c.execute("SELECT id FROM agentcore.machines LIMIT 1").fetchone()
            user = c.execute("SELECT id FROM agentcore.users LIMIT 1").fetchone()
            client = c.execute("SELECT id FROM agentcore.ide_clients LIMIT 1").fetchone()
            agent = c.execute("SELECT id FROM agentcore.agents LIMIT 1").fetchone()
            # Use any session/run/workflow_thread (not necessarily project-specific)
            session = c.execute("SELECT id FROM agentcore.sessions LIMIT 1").fetchone()
            run = c.execute("SELECT id FROM agentcore.runs LIMIT 1").fetchone()
            wt_row = c.execute("SELECT id FROM agentcore.workflow_threads LIMIT 1").fetchone()
            # Use any repo/worktree from the project or fallback to any
            project_row = c.execute(
                "SELECT repository_id, primary_worktree_id FROM agentcore.projects WHERE id = %s", (project_id,)
            ).fetchone()
            repo_id = (str(project_row["repository_id"])
                       if project_row and project_row["repository_id"]
                       else str(c.execute("SELECT id FROM agentcore.repositories LIMIT 1").fetchone()["id"]))
            wt_id = (str(project_row["primary_worktree_id"])
                     if project_row and project_row["primary_worktree_id"]
                     else str(c.execute("SELECT id FROM agentcore.worktrees LIMIT 1").fetchone()["id"]))

            if not all([machine, user, client, agent, session, run, wt_row]):
                raise RuntimeError("Cannot create JIT lease: missing prerequisite identity rows")

            ident_row = c.execute(
                """
                INSERT INTO agentcore.source_identities
                    (machine_id, user_id, project_id, repository_id, worktree_id,
                     client_id, agent_id, session_id, run_id, workflow_thread_id, source_label)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'm6-workflow-worker')
                RETURNING id
                """,
                (str(machine["id"]), str(user["id"]), project_id, repo_id, wt_id,
                 str(client["id"]), str(agent["id"]), str(session["id"]),
                 str(run["id"]), str(wt_row["id"])),
            ).fetchone()
            ident_id = str(ident_row["id"])

    with conn(admin=True) as c:
        # Set the session variable that assert_project_scope checks
        c.execute("SELECT set_config('agentcore.current_project_id', %s, true)", (project_id,))
        lease_row = c.execute(
            "SELECT agentcore.create_capability_lease(%s, %s, %s, %s, %s, %s) AS id",
            (project_id, ident_id, tool_name, step_id, lease_seconds, justification),
        ).fetchone()
        lease_id = str(lease_row["id"])

        # Sync to jit_leased in capability profiles
        c.execute(
            "SELECT agentcore.set_capability_state(%s, %s, 'jit_leased', NULL, %s, false)",
            (project_id, tool_name, f"JIT lease {lease_id} for step {step_id}"),
        )
    # After PG commit: push exact tools to Bifrost VK (idempotent; fail-closed).
    _bridge_grant_for_tool(tool_name)
    return lease_id


def expire_jit_leases(project_id: str) -> int:
    with conn(admin=True) as c:
        row = c.execute(
            "SELECT agentcore.expire_wf_jit_leases(%s) AS expired",
            (project_id,),
        ).fetchone()
        expired = int(row["expired"])
    if expired:
        _bridge_revoke_openrouter()
    return expired


def revoke_lease(project_id: str, lease_id: str, tool_name: str) -> None:
    with conn(admin=True) as c:
        # Revoke directly without going through SECURITY DEFINER (admin has UPDATE)
        c.execute(
            "UPDATE agentcore.capability_leases SET status = 'revoked' WHERE id = %s AND project_id = %s",
            (lease_id, project_id),
        )
        c.execute(
            "SELECT agentcore.set_capability_state(%s, %s, 'dormant', NULL, 'lease revoked', false)",
            (project_id, tool_name),
        )
    if _is_openrouter_lease_tool(tool_name):
        _bridge_revoke_openrouter()


# ─────────────────────────────────────────────────────────────────────────────
# Critic / scorer / judge runs
# ─────────────────────────────────────────────────────────────────────────────

def record_critic_run(
    run_db_id: str,
    project_id: str,
    scope_key: str,
    run_kind: str,
    risk_class: Optional[str],
    input_evidence: list,
    result: dict,
    passed: Optional[bool] = None,
    score: Optional[float] = None,
    verdict: Optional[str] = None,
) -> str:
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_critic_runs
                (run_id, project_id, scope_key, run_kind, risk_class, input_evidence, result, passed, score, verdict)
            VALUES (%s, %s, %s, %s, %s::agentcore.wf_risk_class, %s, %s, %s, %s, %s::agentcore.wf_judge_verdict)
            RETURNING id
            """,
            (
                run_db_id, project_id, scope_key, run_kind,
                risk_class, json.dumps(input_evidence), json.dumps(result),
                passed, score, verdict,
            ),
        ).fetchone()
        return str(row["id"])


# ─────────────────────────────────────────────────────────────────────────────
# A/B experiments
# ─────────────────────────────────────────────────────────────────────────────

def record_ab_decision(
    run_db_id: str,
    project_id: str,
    scope_key: str,
    risk_class: str,
    uncertainty_score: float,
    decision: str,
    justification: str,
) -> str:
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_ab_experiments
                (run_id, project_id, scope_key, risk_class, uncertainty_score, decision, justification)
            VALUES (%s, %s, %s, %s::agentcore.wf_risk_class, %s, %s::agentcore.wf_ab_decision, %s)
            RETURNING id
            """,
            (run_db_id, project_id, scope_key, risk_class, uncertainty_score, decision, justification),
        ).fetchone()
        return str(row["id"])


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────

def record_evidence(
    run_db_id: str,
    project_id: str,
    scope_key: str,
    evidence_type: str,
    summary: str,
    detail: dict,
    trust_class: str = "system_verified",
) -> str:
    with conn(admin=True) as c:
        row = c.execute(
            """
            INSERT INTO agentcore.wf_evidence
                (run_id, project_id, scope_key, evidence_type, summary, detail, trust_class)
            VALUES (%s, %s, %s, %s, %s, %s, %s::agentcore.trust_class)
            RETURNING id
            """,
            (run_db_id, project_id, scope_key, evidence_type, summary, json.dumps(detail), trust_class),
        ).fetchone()
        return str(row["id"])
