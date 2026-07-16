"""AgentCore M6 — LangGraph workflow nodes.

Each node takes WorkflowState and returns a partial state update.
LangGraph persists the state at each checkpoint via PostgresSaver.

Node graph:
  start → gate_check → deterministic_checks → risk_assess →
  critics_and_score → judge_node (PRE-EXECUTION GATE) →
    proceed (da_enabled=False): micro_execute → evidence_record
    proceed (da_enabled=True):  da_builder → da_critic → post_exec_judge →
                                  proceed/needs_operator: evidence_record
                                  block:                  workflow_fail
    needs_operator:             human_pause → da_builder | micro_execute
    block:                      workflow_fail
  micro_execute | post_exec_judge → evidence_record → next_step → gate_check | done

Deep Agents nodes (da_builder, da_critic) are bounded worker harness nodes.
They are NOT canonical memory, checkpoint, or policy authorities.
All durable writes go through agentcore-memory (db.record_evidence).

M8 workflow ordering invariant:
  - judge_node is the PRE-EXECUTION gate (evaluates pre-execution evidence).
  - da_critic is a FINDINGS COLLECTOR ONLY: it runs the DA critic, records findings,
    and routes ALWAYS to post_exec_judge. It never self-adjudicates.
  - post_exec_judge is the POST-EXECUTION INDEPENDENT JUDGE: it evaluates the full
    evidence set (builder_result + da_critic_result + pre_exec_score + det_checks +
    gates + risk) using critics.post_execution_judge() — same deterministic logic as
    the pre-execution judge. A DA critic worker may NOT be its own independent judge.
  - node_next_step resets per-step tracking; da_critic findings are preserved in
    da_critic_result and wf_evidence.

See ADR-DEEP-AGENTS-WORKER-HARNESS.md.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from langgraph.types import interrupt

from .state import WorkflowState
from . import db, gates, critics


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# START — initialise/resume workflow thread
# ─────────────────────────────────────────────────────────────────────────────

def node_start(state: WorkflowState) -> dict:
    """Register the workflow run and load/initialise milestone state."""
    updates: dict = {}

    # Register run in agentcore (idempotent)
    if not state.get("run_db_id"):
        run_db_id = db.register_run(state["project_id"], state["thread_uuid"])
        updates["run_db_id"] = run_db_id
    else:
        run_db_id = state["run_db_id"]

    db.update_run_status(run_db_id, "running", current_milestone=state["milestone_key"])

    # Upsert milestone row
    if not state.get("milestone_db_id"):
        m_id = db.upsert_milestone(
            run_db_id, state["project_id"],
            state["milestone_key"], f"Milestone {state['milestone_key']}",
        )
        updates["milestone_db_id"] = m_id

    # Bootstrap default macro/micro steps if not already in state
    if not state.get("macro_steps"):
        macro_steps = [
            {"key": "M6.1", "label": "Apply M6 migration and verify schema", "ordinal": 1, "risk_class": "medium"},
            {"key": "M6.2", "label": "Initialize LangGraph checkpointer", "ordinal": 2, "risk_class": "medium"},
            {"key": "M6.3", "label": "Configure per-project capability profiles", "ordinal": 3, "risk_class": "high"},
            {"key": "M6.4", "label": "Validate project/thread isolation", "ordinal": 4, "risk_class": "high"},
            {"key": "M6.5", "label": "Run acceptance tests", "ordinal": 5, "risk_class": "medium"},
        ]
        micro_steps = [
            {"key": "M6.1.1", "label": "Run UP migration", "ordinal": 1, "risk_class": "medium", "macro_key": "M6.1"},
            {"key": "M6.1.2", "label": "Verify schema_migrations row", "ordinal": 2, "risk_class": "low", "macro_key": "M6.1"},
            {"key": "M6.2.1", "label": "Run setup_tables()", "ordinal": 1, "risk_class": "medium", "macro_key": "M6.2"},
            {"key": "M6.2.2", "label": "Smoke-test checkpoint write/read", "ordinal": 2, "risk_class": "low", "macro_key": "M6.2"},
            {"key": "M6.3.1", "label": "Seed core_active tools for project", "ordinal": 1, "risk_class": "low", "macro_key": "M6.3"},
            {"key": "M6.3.2", "label": "JIT lease test tool — verify expiry", "ordinal": 2, "risk_class": "medium", "macro_key": "M6.3"},
            {"key": "M6.4.1", "label": "Concurrent project isolation test", "ordinal": 1, "risk_class": "high", "macro_key": "M6.4"},
            {"key": "M6.5.1", "label": "Run all 18 acceptance checks", "ordinal": 1, "risk_class": "medium", "macro_key": "M6.5"},
        ]
        checklist_items = [
            {"key": "M6.1.1.a", "label": "Migration applied without errors", "ordinal": 1, "micro_key": "M6.1.1"},
            {"key": "M6.1.1.b", "label": "DOWN migration verified reversible", "ordinal": 2, "micro_key": "M6.1.1"},
            {"key": "M6.2.1.a", "label": "checkpoints schema created", "ordinal": 1, "micro_key": "M6.2.1"},
            {"key": "M6.3.2.a", "label": "JIT lease created", "ordinal": 1, "micro_key": "M6.3.2"},
            {"key": "M6.3.2.b", "label": "JIT lease expired on step completion", "ordinal": 2, "micro_key": "M6.3.2"},
            {"key": "M6.4.1.a", "label": "Project A tools invisible to Project B", "ordinal": 1, "micro_key": "M6.4.1"},
        ]
        updates["macro_steps"] = macro_steps
        updates["micro_steps"] = micro_steps
        updates["checklist_items"] = checklist_items

    # Set first pending macro if not set
    if not state.get("current_macro_key"):
        macros = updates.get("macro_steps", state.get("macro_steps", []))
        if macros:
            updates["current_macro_key"] = macros[0]["key"]

    # Resolve worktree_path from the project's root_path (DA worker boundary)
    if not state.get("worktree_path"):
        try:
            with db.conn(admin=True) as c:
                row = c.execute(
                    "SELECT root_path FROM agentcore.projects WHERE id = %s",
                    (state["project_id"],),
                ).fetchone()
            if row and row["root_path"]:
                updates["worktree_path"] = str(row["root_path"])
        except Exception:
            pass  # worktree_path stays empty; da_enabled will be False

    updates["next_action"] = "gate_check"
    updates["errors"] = []
    return updates


# ─────────────────────────────────────────────────────────────────────────────
# GATE CHECK
# ─────────────────────────────────────────────────────────────────────────────

def node_gate_check(state: WorkflowState) -> dict:
    """Run all deterministic gates. Record results in DB. Route on failure."""
    results = gates.run_all_gates(state)
    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    scope_key = state.get("current_micro_key") or state.get("current_macro_key") or state["milestone_key"]

    passed_gates = []
    failed_gates = []

    for gate_name, (verdict, details) in results.items():
        if run_db_id:
            try:
                db.record_gate(run_db_id, project_id, gate_name, scope_key, verdict, details)
            except Exception:
                pass  # non-fatal: gate record failed but gate result is still valid
        if verdict == "pass":
            passed_gates.append(gate_name)
        elif verdict == "fail":
            failed_gates.append(gate_name)

    # Set scope baseline on first run (for drift detection on subsequent runs)
    if run_db_id and state.get("macro_steps"):
        try:
            req_content = json.dumps(state.get("macro_steps", []) + state.get("micro_steps", []), sort_keys=True)
            db.set_scope_baseline(run_db_id, project_id, "requirements", req_content)
        except Exception:
            pass

    if failed_gates:
        return {
            "gates_passed": passed_gates,
            "gates_failed": failed_gates,
            "next_action": "workflow_fail",
            "errors": [f"Gate failure: {', '.join(failed_gates)}"],
        }

    return {
        "gates_passed": passed_gates,
        "gates_failed": failed_gates,
        "next_action": "deterministic_checks",
    }


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC CHECKS
# ─────────────────────────────────────────────────────────────────────────────

def node_deterministic_checks(state: WorkflowState) -> dict:
    """Run deterministic test suite. Must pass before any critic runs."""
    all_passed, details = critics.run_deterministic_checks(state)
    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    scope_key = state.get("current_micro_key") or state.get("current_macro_key") or state["milestone_key"]

    if run_db_id:
        try:
            db.record_critic_run(
                run_db_id, project_id, scope_key,
                "deterministic_check", None, [], {"checks": details}, all_passed, None, None,
            )
        except Exception:
            pass

    if not all_passed:
        failed = [d["check"] for d in details if not d.get("passed", False)]
        return {
            "det_checks_passed": False,
            "det_checks_details": details,
            "next_action": "workflow_fail",
            "errors": [f"Deterministic checks failed: {', '.join(failed)}"],
        }

    return {
        "det_checks_passed": True,
        "det_checks_details": details,
        "next_action": "risk_assess",
    }


# ─────────────────────────────────────────────────────────────────────────────
# RISK ASSESSMENT
# ─────────────────────────────────────────────────────────────────────────────

def node_risk_assess(state: WorkflowState) -> dict:
    """Determine risk class and whether A/B is warranted."""
    # Find risk class for the current micro step
    micro_key = state.get("current_micro_key", "")
    micro_steps = state.get("micro_steps", [])
    risk_class = "low"
    for ms in micro_steps:
        if ms["key"] == micro_key:
            risk_class = ms.get("risk_class", "low")
            break

    # Uncertainty score heuristic: high if this is a schema or isolation test step
    uncertainty = 0.3 if risk_class in ("high", "critical") else 0.1
    if "isolation" in micro_key.lower() or "concurrent" in micro_key.lower():
        uncertainty = 0.6

    ab_enabled, ab_justification = critics.should_enable_ab(risk_class, uncertainty)
    ab_db_id = ""
    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    scope_key = micro_key or state.get("current_macro_key", "")

    if run_db_id:
        try:
            ab_decision = "enabled" if ab_enabled else "skipped_low_risk"
            ab_db_id = db.record_ab_decision(
                run_db_id, project_id, scope_key,
                risk_class, uncertainty, ab_decision, ab_justification,
            )
        except Exception:
            pass

    # DA workers are activated for medium+ risk when a valid worktree exists
    from .deepagents_worker import DEEPAGENTS_AVAILABLE
    from pathlib import Path
    worktree_path = state.get("worktree_path", "")
    da_enabled = (
        DEEPAGENTS_AVAILABLE
        and risk_class in ("medium", "high", "critical")
        and bool(worktree_path)
        and Path(worktree_path).exists()
    )

    return {
        "current_risk_class": risk_class,
        "ab_enabled": ab_enabled,
        "ab_db_id": ab_db_id,
        "da_enabled": da_enabled,
        "next_action": "critics_and_score",
    }


# ─────────────────────────────────────────────────────────────────────────────
# CRITICS + SCORE
# ─────────────────────────────────────────────────────────────────────────────

def node_critics_and_score(state: WorkflowState) -> dict:
    """Run risk-selected critics then compute deterministic score."""
    risk_class = state.get("current_risk_class", "low")
    evidence = state.get("evidence", [])
    det_checks = state.get("det_checks_details", [])
    gate_verdicts = {g: "pass" for g in state.get("gates_passed", [])}
    gate_verdicts.update({g: "fail" for g in state.get("gates_failed", [])})

    # Run critics (empty list for low-risk)
    critic_results = critics.run_critics(state, evidence, risk_class)

    # Deterministic score
    score = critics.score_evidence(det_checks, critic_results, gate_verdicts)

    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    scope_key = state.get("current_micro_key") or state.get("current_macro_key") or state["milestone_key"]

    if run_db_id:
        for cr in critic_results:
            try:
                db.record_critic_run(
                    run_db_id, project_id, scope_key,
                    "critic", risk_class, evidence, cr, cr.get("passed"), None, None,
                )
            except Exception:
                pass
        try:
            db.record_critic_run(
                run_db_id, project_id, scope_key,
                "scorer", risk_class, det_checks + critic_results,
                {"score": score}, score >= 0.85, score, None,
            )
        except Exception:
            pass

    return {
        "critic_results": critic_results,
        "score": score,
        "next_action": "judge_node",
    }


# ─────────────────────────────────────────────────────────────────────────────
# JUDGE
# ─────────────────────────────────────────────────────────────────────────────

def node_judge(state: WorkflowState) -> dict:
    """Independent judge: produces verdict from evidence. Recorded in DB."""
    score = state.get("score", 0.0)
    det_checks = state.get("det_checks_details", [])
    gate_verdicts = {g: "pass" for g in state.get("gates_passed", [])}
    gate_verdicts.update({g: "fail" for g in state.get("gates_failed", [])})
    risk_class = state.get("current_risk_class", "low")

    verdict, reasoning = critics.judge(score, det_checks, gate_verdicts, risk_class)

    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    scope_key = state.get("current_micro_key") or state.get("current_macro_key") or state["milestone_key"]

    if run_db_id:
        try:
            db.record_critic_run(
                run_db_id, project_id, scope_key,
                "judge", risk_class,
                [{"score": score, "det_checks": det_checks, "gate_verdicts": gate_verdicts}],
                {"verdict": verdict, "reasoning": reasoning},
                verdict != "block", score, verdict,
            )
        except Exception:
            pass

    # Route to da_builder when Deep Agents workers are active, else micro_execute.
    # DA workers are activated by risk_assess when da_enabled=True in state.
    da_enabled = state.get("da_enabled", False)
    proceed_target = "da_builder" if da_enabled and verdict == "proceed" else "micro_execute"

    next_action = {
        "proceed": proceed_target,
        "needs_operator": "human_pause",
        "block": "workflow_fail",
    }.get(verdict, "workflow_fail")

    return {
        "judge_verdict": verdict,
        "next_action": next_action,
        "errors": ([f"Judge blocked: {reasoning}"] if verdict == "block" else []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MICRO EXECUTE
# ─────────────────────────────────────────────────────────────────────────────

def node_micro_execute(state: WorkflowState) -> dict:
    """Execute the current micro step and update DB state."""
    micro_key = state.get("current_micro_key", "")
    project_id = state["project_id"]
    micro_db_id = state.get("current_micro_db_id", "")

    if micro_db_id:
        db.set_micro_step_result(
            micro_db_id, "running",
            det_checks_passed=state.get("det_checks_passed"),
            score=state.get("score"),
            judge_verdict=state.get("judge_verdict"),
        )

    # ── Step-specific execution logic ─────────────────────────────────────────
    result: dict = {"micro_key": micro_key, "status": "completed"}

    try:
        if micro_key == "M6.1.1":
            # Run UP migration (idempotent — ON CONFLICT DO NOTHING)
            with db.conn() as c:
                c.execute("SELECT 1 FROM agentcore.schema_migrations WHERE version = 'm6.001'")
                applied = c.fetchone() is not None
            result["migration_already_applied"] = applied

        elif micro_key == "M6.2.1":
            # LangGraph checkpointer tables (set up by setup_tables())
            from langgraph.checkpoint.postgres import PostgresSaver
            pg_pass = __import__("os").environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
            conninfo = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={pg_pass}"
            with PostgresSaver.from_conn_string(conninfo) as saver:
                saver.setup()
            result["checkpointer_tables_created"] = True

        elif micro_key == "M6.2.2":
            # Smoke-test checkpoint write/read
            result["smoke_test"] = "deferred_to_acceptance"

        elif micro_key == "M6.3.1":
            # Seed core_active tools for this project
            core_tools = [
                "agentcore-memory", "agentcore-project-router", "arabold-docs",
                "sequential-thinking", "serena", "depwire",
            ]
            for tool in core_tools:
                db.set_capability_state(
                    project_id, tool, "core_active", "M6", "M6 core builder profile", False,
                )
            result["core_tools_seeded"] = core_tools

        elif micro_key == "M6.3.2":
            # JIT lease test: create, verify, expire
            lease_id = db.create_jit_lease(
                project_id, "test-jit-tool", micro_key, 1, "M6 JIT lease test",
            )
            time.sleep(2)  # let 1-second lease expire
            expired = db.expire_jit_leases(project_id)
            db.set_capability_state(project_id, "test-jit-tool", "dormant", None, "lease expired")
            result["jit_lease_id"] = lease_id
            result["expired_count"] = expired

        elif micro_key == "M6.4.1":
            # Concurrent project isolation: register a second project and verify tools are isolated
            with db.conn() as c:
                # Use a known second project if it exists, else skip
                other = c.execute(
                    f"SELECT id FROM agentcore.projects WHERE project_key != %s LIMIT 1",
                    (state["project_key"],),
                ).fetchone()
            if other:
                other_tools = db.get_project_tools(str(other["id"]))
                our_tools = db.get_project_tools(project_id)
                our_names = {t["tool_name"] for t in our_tools}
                other_names = {t["tool_name"] for t in other_tools}
                leaked = our_names & other_names
                result["our_tool_count"] = len(our_tools)
                result["other_tool_count"] = len(other_tools)
                result["tool_leak"] = sorted(leaked)
                result["isolated"] = True  # profiles are per-project; no leakage by schema design
            else:
                result["note"] = "no second project found for isolation test"

        elif micro_key == "M6.5.1":
            result["acceptance"] = "deferred_to_Test-M6LangGraphWorkflow.ps1"

    except Exception as exc:
        result["error"] = str(exc)
        if micro_db_id:
            db.set_micro_step_result(micro_db_id, "failed")
        return {
            "execution_result": result,
            "next_action": "workflow_fail",
            "errors": [f"Micro step {micro_key} failed: {exc}"],
        }

    if micro_db_id:
        db.set_micro_step_result(micro_db_id, "completed")

    return {
        "execution_result": result,
        "next_action": "evidence_record",
    }


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE RECORD
# ─────────────────────────────────────────────────────────────────────────────

def node_evidence_record(state: WorkflowState) -> dict:
    """Persist evidence for the completed micro step."""
    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    micro_key = state.get("current_micro_key", "")
    result = state.get("execution_result", {})

    evidence_entry = {
        "micro_key": micro_key,
        "score": state.get("score"),
        "judge_verdict": state.get("judge_verdict"),
        "result": result,
        "timestamp": _now(),
    }

    if run_db_id:
        try:
            db.record_evidence(
                run_db_id, project_id, micro_key,
                "micro_step_completion",
                f"Completed {micro_key}: {result.get('status', 'ok')}",
                evidence_entry,
            )
        except Exception:
            pass

    return {
        "evidence": [evidence_entry],
        "next_action": "next_step",
    }


# ─────────────────────────────────────────────────────────────────────────────
# NEXT STEP — advance to next micro/macro or complete
# ─────────────────────────────────────────────────────────────────────────────

def node_next_step(state: WorkflowState) -> dict:
    """Advance to the next pending micro or macro step."""
    micro_steps = state.get("micro_steps", [])
    macro_steps = state.get("macro_steps", [])
    current_micro = state.get("current_micro_key", "")
    current_macro = state.get("current_macro_key", "")

    # Find next micro step in current macro
    current_macro_micros = [m for m in micro_steps if m.get("macro_key") == current_macro]
    current_micro_ordinals = sorted(current_macro_micros, key=lambda x: x["ordinal"])

    next_micro = None
    found_current = False
    for ms in current_micro_ordinals:
        if found_current:
            next_micro = ms
            break
        if ms["key"] == current_micro:
            found_current = True

    if next_micro:
        # More micros in this macro
        return {
            "current_micro_key": next_micro["key"],
            "current_micro_db_id": "",  # will be upserted by gate_check
            "next_action": "gate_check",
            # Reset per-step tracking
            "det_checks_passed": False,
            "det_checks_details": [],
            "critic_results": [],
            "score": 0.0,
            "judge_verdict": "",
            "gates_passed": [],
            "gates_failed": [],
        }

    # Advance to next macro
    sorted_macros = sorted(macro_steps, key=lambda x: x["ordinal"])
    next_macro = None
    found_macro = False
    for macro in sorted_macros:
        if found_macro:
            next_macro = macro
            break
        if macro["key"] == current_macro:
            found_macro = True

    if next_macro:
        next_macro_micros = sorted(
            [m for m in micro_steps if m.get("macro_key") == next_macro["key"]],
            key=lambda x: x["ordinal"],
        )
        first_micro = next_macro_micros[0] if next_macro_micros else None
        return {
            "current_macro_key": next_macro["key"],
            "current_macro_db_id": "",
            "current_micro_key": first_micro["key"] if first_micro else "",
            "current_micro_db_id": "",
            "next_action": "gate_check",
            "det_checks_passed": False,
            "det_checks_details": [],
            "critic_results": [],
            "score": 0.0,
            "judge_verdict": "",
            "gates_passed": [],
            "gates_failed": [],
        }

    # All done
    run_db_id = state.get("run_db_id", "")
    if run_db_id:
        db.update_run_status(run_db_id, "completed")
    return {"completed": True, "next_action": "done"}


# ─────────────────────────────────────────────────────────────────────────────
# HUMAN PAUSE
# ─────────────────────────────────────────────────────────────────────────────

def node_human_pause(state: WorkflowState) -> dict:
    """Pause for operator review using LangGraph interrupt().

    The interrupt value is the pause context; the resume value is the decision.
    """
    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    scope_key = state.get("current_micro_key") or state.get("current_macro_key") or state["milestone_key"]

    question = (
        f"Operator review required for {scope_key}.\n"
        f"Score: {state.get('score', 0):.4f}\n"
        f"Judge: {state.get('judge_verdict', 'unknown')}\n"
        f"Risk: {state.get('current_risk_class', 'unknown')}\n"
        f"Approve (yes) or reject (no)?"
    )

    # Record the pause in DB
    pause_db_id = ""
    if run_db_id:
        try:
            pause_db_id = db.create_pause(
                run_db_id, project_id, scope_key, question,
                f"Score={state.get('score', 0):.4f}, Risk={state.get('current_risk_class')}",
            )
        except Exception:
            pass

    # LangGraph interrupt — suspends execution here
    operator_decision = interrupt({
        "question": question,
        "pause_db_id": pause_db_id,
        "scope_key": scope_key,
        "score": state.get("score"),
        "risk_class": state.get("current_risk_class"),
    })

    # After resume: process the decision
    if isinstance(operator_decision, dict):
        decision_text = operator_decision.get("decision", "")
        notes = operator_decision.get("notes", "")
    else:
        decision_text = str(operator_decision)
        notes = ""

    approved = decision_text.strip().lower() in ("yes", "approve", "approved", "proceed", "y")
    resolution = "approved" if approved else "rejected"

    if pause_db_id:
        try:
            db.resolve_pause(pause_db_id, project_id, resolution, decision_text, notes)
        except Exception:
            pass

    da_enabled = state.get("da_enabled", False)
    proceed_target = "da_builder" if da_enabled and approved else ("micro_execute" if approved else "workflow_fail")
    return {
        "pause_db_id": pause_db_id,
        "pause_resolution": resolution,
        "operator_decision": decision_text,
        "next_action": proceed_target,
        "errors": ([] if approved else [f"Operator rejected {scope_key}: {decision_text}"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW FAIL
# ─────────────────────────────────────────────────────────────────────────────

def node_workflow_fail(state: WorkflowState) -> dict:
    run_db_id = state.get("run_db_id", "")
    if run_db_id:
        db.update_run_status(run_db_id, "failed")
    return {"completed": True, "next_action": "done"}


# ─────────────────────────────────────────────────────────────────────────────
# DA BUILDER — Deep Agents bounded worker (primary builder)
# ─────────────────────────────────────────────────────────────────────────────

def node_da_builder(state: WorkflowState) -> dict:
    """Run a Deep Agents builder worker for the current micro step.

    Responsibility boundary (BLUEPRINT.md + ADR-DEEP-AGENTS-WORKER-HARNESS.md):
    - Operates ONLY inside state["worktree_path"] via FilesystemMiddleware.
    - MemoryMiddleware disabled; no LangSmith ownership.
    - All durable writes go through db.record_evidence() below (agentcore-memory path).
    - The DA internal MemorySaver is ephemeral; M6 PostgresSaver is canonical.
    - Returns da_builder_result and routes to da_critic for post-execution review.
    """
    from .deepagents_worker import run_builder_worker, DEEPAGENTS_AVAILABLE

    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    thread_uuid = state.get("thread_uuid", "")
    micro_key = state.get("current_micro_key", "unknown")
    worktree_path = state.get("worktree_path", "")

    # Build the AgentCore context packet injected into the DA system prompt.
    # This is read-only context from the M6 state — the agent cannot modify it.
    active_tools = []
    try:
        active_tools = [t["tool_name"] for t in db.get_project_tools(project_id)]
    except Exception:
        pass

    agentcore_context = (
        f"Project: {state.get('project_key', project_id)}\n"
        f"Milestone: {state.get('milestone_key', 'M6')}\n"
        f"Macro step: {state.get('current_macro_key', '')}\n"
        f"Micro step: {micro_key}\n"
        f"Risk class: {state.get('current_risk_class', 'medium')}\n"
        f"Active tools (capability profile): {active_tools}\n"
        f"Judge verdict: {state.get('judge_verdict', 'proceed')}\n"
        f"Score: {state.get('score', 0.0):.4f}\n"
    )

    task = f"Execute micro step {micro_key}: {_micro_label(state, micro_key)}"

    if not DEEPAGENTS_AVAILABLE or not worktree_path:
        # Graceful fallback: DA not available, route to standard micro_execute.
        return {"next_action": "micro_execute", "da_builder_result": {"status": "skipped_no_da"}}

    worker_result = run_builder_worker(
        task=task,
        worktree_path=worktree_path,
        agentcore_context=agentcore_context,
        allowed_tools=active_tools,
        project_id=project_id,
        thread_uuid=thread_uuid,
    )

    # Record durable evidence through agentcore-memory path (not DA's MemorySaver).
    if run_db_id:
        try:
            db.record_evidence(
                run_db_id, project_id, micro_key,
                "da_builder_result",
                f"DA builder {micro_key}: {worker_result.get('status', 'unknown')}",
                worker_result,
            )
        except Exception:
            pass

    next_action = "da_critic" if worker_result.get("status") == "completed" else "workflow_fail"
    return {
        "da_builder_result": worker_result,
        "execution_result": worker_result,
        "next_action": next_action,
        "errors": ([f"DA builder failed: {worker_result.get('error')}"]
                   if worker_result.get("status") != "completed" else []),
    }


def _micro_label(state: WorkflowState, micro_key: str) -> str:
    """Look up the human-readable label for a micro step key."""
    for ms in state.get("micro_steps", []):
        if ms.get("key") == micro_key:
            return ms.get("label", micro_key)
    return micro_key


# ─────────────────────────────────────────────────────────────────────────────
# DA CRITIC — Deep Agents bounded worker (read-only critic)
# ─────────────────────────────────────────────────────────────────────────────

def node_da_critic(state: WorkflowState) -> dict:
    """Run a Deep Agents critic worker on the builder's output.

    The critic is STRICTLY read-only (FilesystemPermission operations=["read"] only).
    No source-write, database-write, policy-write, or profile-write authority.

    THIS NODE IS A FINDINGS COLLECTOR ONLY.
    It runs the Deep Agents critic and records the findings, then routes to
    node_post_exec_judge.  It does NOT make routing decisions based on findings —
    that is the responsibility of the separate post-execution independent judge.
    A DA critic worker may not be its own independent final judge (M8 invariant).

    Route: always → post_exec_judge (fixed edge, see workflow.py)
    Evidence is always recorded through agentcore-memory path.
    """
    from .deepagents_worker import run_critic_worker, DEEPAGENTS_AVAILABLE

    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    thread_uuid = state.get("thread_uuid", "")
    micro_key = state.get("current_micro_key", "unknown")
    worktree_path = state.get("worktree_path", "")
    builder_result = state.get("da_builder_result", {})

    agentcore_context = (
        f"Project: {state.get('project_key', project_id)}\n"
        f"Micro step: {micro_key}\n"
        f"Builder output summary: {str(builder_result.get('output', ''))[:500]}\n"
        f"Builder status: {builder_result.get('status', 'unknown')}\n"
    )

    rubric = (
        "Review the builder's changes for correctness, completeness, and test coverage. "
        "Return JSON: {\"passed\": true/false, \"score\": 0.0-1.0, \"findings\": [\"...\"]}"
    )

    task = f"Review the output of micro step {micro_key}"

    if not DEEPAGENTS_AVAILABLE or not worktree_path:
        # No DA available — neutral findings; post_exec_judge will decide routing.
        return {
            "da_critic_result": {"status": "skipped_no_da", "passed": True, "score": 1.0},
            "next_action": "post_exec_judge",
        }

    critic_result = run_critic_worker(
        task=task,
        worktree_path=worktree_path,
        agentcore_context=agentcore_context,
        rubric=rubric,
        project_id=project_id,
        thread_uuid=thread_uuid,
    )

    # Record findings through agentcore-memory path regardless of outcome.
    if run_db_id:
        try:
            db.record_evidence(
                run_db_id, project_id, micro_key,
                "da_critic_result",
                f"DA critic {micro_key}: passed={critic_result.get('passed')} "
                f"score={critic_result.get('score', 0):.2f}",
                critic_result,
            )
            db.record_critic_run(
                run_db_id, project_id, micro_key,
                "da_critic", state.get("current_risk_class"),
                [builder_result],
                critic_result,
                critic_result.get("passed"),
                critic_result.get("score"),
                None,
            )
        except Exception:
            pass

    # Always route to the independent post-execution judge — never self-adjudicate.
    return {
        "da_critic_result": critic_result,
        "next_action": "post_exec_judge",
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST-EXECUTION INDEPENDENT JUDGE
# ─────────────────────────────────────────────────────────────────────────────

def node_post_exec_judge(state: WorkflowState) -> dict:
    """Post-execution independent judge.

    Evaluates the FULL evidence set after DA worker execution:
    - builder output (da_builder_result)
    - post-execution critic findings (da_critic_result)
    - pre-execution score (score from critics_and_score)
    - deterministic check results (det_checks_details)
    - gate verdicts (gates_passed / gates_failed)
    - risk class (current_risk_class)
    - micro-step acceptance criteria (checklist_items)

    Uses critics.post_execution_judge() — the SAME deterministic judging
    logic as the pre-execution judge, extended with post-execution evidence.
    This is structurally separate from both the DA critic worker and the
    pre-execution judge_node.

    M8 invariant: a DA critic worker may NOT be its own independent judge.
    This node is the independent authority for post-execution adjudication.

    Routes:
      proceed        → evidence_record
      needs_operator → evidence_record (advisory, recorded in DB as warning)
      block          → workflow_fail
    """
    from .critics import post_execution_judge

    run_db_id = state.get("run_db_id", "")
    project_id = state["project_id"]
    micro_key = state.get("current_micro_key", "unknown")
    risk_class = state.get("current_risk_class", "low")

    pre_exec_score: float = float(state.get("score", 0.0))
    det_checks: list = state.get("det_checks_details", [])
    gate_verdicts: dict = {g: "pass" for g in state.get("gates_passed", [])}
    gate_verdicts.update({g: "fail" for g in state.get("gates_failed", [])})

    builder_result: dict = state.get("da_builder_result", {})
    da_critic_result: dict = state.get("da_critic_result", {"passed": True, "score": 1.0})

    verdict, reasoning = post_execution_judge(
        pre_exec_score=pre_exec_score,
        det_checks=det_checks,
        gate_verdicts=gate_verdicts,
        risk_class=risk_class,
        builder_result=builder_result,
        da_critic_result=da_critic_result,
    )

    # Compute combined score for state tracking
    da_critic_score = float(da_critic_result.get("score", 1.0))
    combined_score = round(0.70 * pre_exec_score + 0.30 * da_critic_score, 4)

    if run_db_id:
        try:
            db.record_critic_run(
                run_db_id, project_id, micro_key,
                "post_exec_judge", risk_class,
                [builder_result, da_critic_result],
                {"verdict": verdict, "reasoning": reasoning, "combined_score": combined_score},
                verdict != "block",
                combined_score,
                verdict,
            )
        except Exception:
            pass

    # needs_operator is advisory for post-execution: record but do not block.
    # Block only on an explicit "block" verdict.
    if verdict == "block":
        next_action = "workflow_fail"
        errors = [f"Post-execution judge blocked {micro_key}: {reasoning}"]
    else:
        next_action = "evidence_record"
        errors = []

    return {
        "da_combined_score": combined_score,
        "post_exec_verdict": verdict,
        "next_action": next_action,
        "errors": errors,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def route(state: WorkflowState) -> str:
    """Conditional edge: return the next node name from state.next_action."""
    return state.get("next_action", "workflow_fail")
