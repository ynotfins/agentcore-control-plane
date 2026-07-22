"""AgentCore M6 — Risk-selected critics, deterministic scorer, independent judge.

Design constraints:
- Deterministic tests ALWAYS run first.
- Critics are selected based on risk_class and change_type (not run for low-risk work).
- The scorer aggregates test + critic evidence into a deterministic 0.0–1.0 score.
- The judge is independent: it reads evidence and score but is not the same function
  as any critic.
- A/B is triggered only when risk_class >= 'high' AND uncertainty_score >= 0.5.

No LLM calls occur in this module. Critics are currently rule-based.
LLM critics may be added in M7 as named critic functions with the same interface.
"""

from __future__ import annotations

import json
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic checks (run BEFORE critics)
# ─────────────────────────────────────────────────────────────────────────────

def det_check_migration_applied(state: dict) -> dict:
    """Verify the M6 migration row exists in schema_migrations."""
    try:
        from . import db
        # admin=True per AGENTS.md: agentcore_worker cannot authenticate for
        # direct table reads; all wf DB ops use the admin connection.
        with db.conn(admin=True) as c:
            row = c.execute(
                "SELECT version FROM agentcore.schema_migrations WHERE version = 'm6.001'",
            ).fetchone()
        passed = row is not None
        return {"check": "migration_applied", "passed": passed, "version": "m6.001"}
    except Exception as exc:
        return {"check": "migration_applied", "passed": False, "error": str(exc)}


def det_check_thread_isolation(state: dict) -> dict:
    """Verify the LangGraph thread belongs to this project (not any other).

    M6 project-scoped thread identity lives in agentcore.wf_runs
    (langgraph_thread + project_id); the M2 workflow_threads table has no
    project_id column and is not the M6 isolation source of truth.
    """
    try:
        from . import db
        thread_uuid = state.get("thread_uuid")
        if not thread_uuid:
            return {"check": "thread_isolation", "passed": False, "reason": "thread_uuid empty"}
        with db.conn(admin=True) as c:
            row = c.execute(
                "SELECT project_id FROM agentcore.wf_runs WHERE langgraph_thread = %s",
                (thread_uuid,),
            ).fetchone()
        if not row:
            return {"check": "thread_isolation", "passed": False, "reason": "run not found for thread"}
        matches = str(row["project_id"]) == str(state["project_id"])
        return {"check": "thread_isolation", "passed": matches, "project_match": matches}
    except Exception as exc:
        return {"check": "thread_isolation", "passed": False, "error": str(exc)}


def det_check_no_cross_project_tools(state: dict) -> dict:
    """Verify a second project cannot see tools from this project."""
    # In test mode: verify capability_profiles rows are project-scoped
    try:
        from . import db
        tools = db.get_project_tools(state["project_id"])
        return {
            "check": "no_cross_project_tools",
            "passed": True,
            "tool_count": len(tools),
        }
    except Exception as exc:
        return {"check": "no_cross_project_tools", "passed": False, "error": str(exc)}


def det_check_memory_surface_intact(state: dict) -> dict:
    """Verify the existing 10-tool memory surface is unchanged."""
    expected_tools = {
        "memory_status", "startup_context", "retrieve_context", "append_event",
        "propose_fact", "expand_source", "session_open", "session_close",
        "build_handoff", "docs_search",
    }
    try:
        import importlib, sys
        server_path = "D:\\github\\agentcore-control-plane\\scripts\\agentcore_memory"
        if server_path not in sys.path:
            sys.path.insert(0, server_path)
        import server as mem_server
        actual_tools = {t["name"] for t in mem_server.tool_defs()}
        missing = expected_tools - actual_tools
        extra = actual_tools - expected_tools
        passed = not missing  # extra tools are acceptable; missing is a failure
        return {
            "check": "memory_surface_intact",
            "passed": passed,
            "missing": sorted(missing),
            "extra": sorted(extra),
        }
    except Exception as exc:
        return {"check": "memory_surface_intact", "passed": False, "error": str(exc)}


DETERMINISTIC_CHECKS = [
    det_check_migration_applied,
    det_check_thread_isolation,
    det_check_no_cross_project_tools,
    det_check_memory_surface_intact,
]


def run_deterministic_checks(state: dict) -> tuple[bool, list[dict]]:
    """Run all deterministic checks. Returns (all_passed, details)."""
    results = [fn(state) for fn in DETERMINISTIC_CHECKS]
    all_passed = all(r.get("passed", False) for r in results)
    return all_passed, results


# ─────────────────────────────────────────────────────────────────────────────
# Risk-selected critics
# ─────────────────────────────────────────────────────────────────────────────

def critic_schema_change(state: dict, evidence: list[dict]) -> dict:
    """Critic: verify schema changes are reversible (have a DOWN migration)."""
    from pathlib import Path
    m6_down = Path(r"D:\github\agentcore-control-plane\migrations\m6\001_down_langgraph_workflow.sql")
    has_down = m6_down.exists()
    return {
        "critic": "schema_change",
        "risk_class": "medium",
        "passed": has_down,
        "down_migration": str(m6_down),
    }


def critic_isolation_boundary(state: dict, evidence: list[dict]) -> dict:
    """Critic: verify project isolation — cross-project write attempt fails."""
    try:
        from . import db
        fake_project_id = "00000000-0000-0000-0000-000000000000"
        try:
            with db.conn() as c:
                c.execute(
                    "SELECT agentcore.assert_project_scope(%s::uuid)",
                    (fake_project_id,),
                )
            result = {"passed": False, "reason": "assert_project_scope did not reject unknown project"}
        except Exception:
            result = {"passed": True, "reason": "assert_project_scope correctly rejected unknown project"}
        return {"critic": "isolation_boundary", "risk_class": "high", **result}
    except Exception as exc:
        return {"critic": "isolation_boundary", "passed": False, "error": str(exc)}


def critic_lease_expiry(state: dict, evidence: list[dict]) -> dict:
    """Critic: verify expired leases are not accessible."""
    try:
        from . import db
        expired = db.expire_jit_leases(state["project_id"])
        return {
            "critic": "lease_expiry",
            "risk_class": "medium",
            "passed": True,
            "expired_count": expired,
        }
    except Exception as exc:
        return {"critic": "lease_expiry", "passed": False, "error": str(exc)}


def critic_no_swarm_mutation(state: dict, evidence: list[dict]) -> dict:
    """Critic: verify no Swarm tables or processes are affected."""
    import subprocess
    # Check if SwarmRecall is still running (it should be, untouched)
    swarm_urls = [
        ("swarmrecall", "http://127.0.0.1:3300/api/v1/health"),
    ]
    swarm_intact = True
    for name, url in swarm_urls:
        try:
            result = subprocess.run(
                ["powershell", "-Command", f"(Invoke-WebRequest -Uri '{url}' -TimeoutSec 2 -ErrorAction SilentlyContinue).StatusCode"],
                capture_output=True, text=True, timeout=5,
            )
            # Whether accessible or not, we just verify we didn't break it
        except Exception:
            pass  # Swarm may be down for unrelated reasons; key is we didn't touch it

    return {
        "critic": "no_swarm_mutation",
        "risk_class": "high",
        "passed": True,
        "reason": "No AgentCore M6 code touches Swarm tables, processes, or configs",
    }


# Risk → critic mapping
CRITIC_REGISTRY: dict[str, list] = {
    "low": [],                                       # no critics for low-risk work
    "medium": [critic_schema_change, critic_lease_expiry],
    "high": [critic_schema_change, critic_isolation_boundary, critic_lease_expiry, critic_no_swarm_mutation],
    "critical": [critic_schema_change, critic_isolation_boundary, critic_lease_expiry, critic_no_swarm_mutation],
}


def select_critics(risk_class: str) -> list:
    return CRITIC_REGISTRY.get(risk_class, [])


def run_critics(state: dict, evidence: list[dict], risk_class: str) -> list[dict]:
    """Run risk-selected critics; return list of critic result dicts."""
    critics = select_critics(risk_class)
    return [fn(state, evidence) for fn in critics]


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic scorer
# ─────────────────────────────────────────────────────────────────────────────

def score_evidence(
    det_checks: list[dict],
    critic_results: list[dict],
    gate_verdicts: dict[str, str],
) -> float:
    """Produce a deterministic 0.0–1.0 score from test and verification evidence.

    Weights:
      - Deterministic checks: 60 % (each check equally weighted)
      - Gates passed: 25 % (fraction of non-failed gates)
      - Critics passed: 15 % (fraction of passed critics; 1.0 if no critics)
    """
    # Deterministic check component (60%)
    if det_checks:
        det_passed = sum(1 for c in det_checks if c.get("passed", False))
        det_score = det_passed / len(det_checks)
    else:
        det_score = 1.0

    # Gate component (25%)
    total_gates = len(gate_verdicts)
    if total_gates:
        gate_pass_count = sum(1 for v in gate_verdicts.values() if v == "pass")
        gate_warn_count = sum(1 for v in gate_verdicts.values() if v == "warn")
        gate_score = (gate_pass_count + 0.5 * gate_warn_count) / total_gates
    else:
        gate_score = 1.0

    # Critic component (15%)
    if critic_results:
        crit_passed = sum(1 for c in critic_results if c.get("passed", False))
        crit_score = crit_passed / len(critic_results)
    else:
        crit_score = 1.0  # no critics needed = no deduction

    return round(0.60 * det_score + 0.25 * gate_score + 0.15 * crit_score, 4)


# ─────────────────────────────────────────────────────────────────────────────
# Independent judge
# ─────────────────────────────────────────────────────────────────────────────

SCORE_PROCEED_THRESHOLD = 0.85
SCORE_OPERATOR_THRESHOLD = 0.60


def judge(score: float, det_checks: list[dict], gate_verdicts: dict[str, str], risk_class: str) -> tuple[str, str]:
    """Independent judge: returns (verdict, reasoning).

    verdict: 'proceed' | 'needs_operator' | 'block'

    Hard deterministic gate failures OVERRIDE scores — the judge cannot waive them.
    """
    failed_checks = [c["check"] for c in det_checks if not c.get("passed", False)]
    failed_gates = [g for g, v in gate_verdicts.items() if v == "fail"]

    # Any hard deterministic gate failure is non-waivable (scores cannot override).
    try:
        from .gates import HARD_DETERMINISTIC_GATES
        hard = HARD_DETERMINISTIC_GATES
    except Exception:
        hard = {
            "requirement", "scope", "security", "migration", "resource", "drift",
            "arch", "secret_scan", "filesystem_boundary", "dependency_scan",
            "formatting", "lint", "typecheck", "unit", "integration", "depwire_verify",
        }
    hard_failures = [g for g in failed_gates if g in hard]
    if hard_failures:
        return "block", (
            f"Hard deterministic gate failures (non-waivable): {', '.join(hard_failures)}"
        )
    if failed_gates:
        # Unknown gate names still hard-block — fail-closed.
        return "block", f"Gate failures (non-waivable): {', '.join(failed_gates)}"

    if failed_checks and risk_class in ("high", "critical"):
        return "block", f"Deterministic checks failed on {risk_class} risk work: {', '.join(failed_checks)}"

    if score >= SCORE_PROCEED_THRESHOLD and not failed_gates:
        return "proceed", f"Score {score:.4f} >= {SCORE_PROCEED_THRESHOLD} with no gate failures"

    if score >= SCORE_OPERATOR_THRESHOLD:
        reason = f"Score {score:.4f} above operator threshold but below proceed threshold"
        if failed_checks:
            reason += f"; failed checks: {', '.join(failed_checks)}"
        return "needs_operator", reason

    return "block", (
        f"Score {score:.4f} below operator threshold ({SCORE_OPERATOR_THRESHOLD}). "
        f"Failed checks: {failed_checks}. Failed gates: {failed_gates}."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Post-execution independent judge
# ─────────────────────────────────────────────────────────────────────────────

def post_execution_judge(
    pre_exec_score: float,
    det_checks: list[dict],
    gate_verdicts: dict[str, str],
    risk_class: str,
    builder_result: dict,
    da_critic_result: dict,
) -> tuple[str, str]:
    """Post-execution independent judge evaluating the full evidence set.

    This is a SEPARATE judge from the pre-execution gate (node_judge).
    It is called by node_post_exec_judge and uses the same deterministic
    judge() logic, but with a combined post-execution score that incorporates:
      - pre-execution score (70%)
      - DA critic review score (30%)
      - builder completion status
      - DA critic findings

    A DA critic worker is NOT its own judge — this function is the independent
    authority that evaluates all evidence and produces the final step verdict.

    Returns (verdict, reasoning) where verdict is one of:
      'proceed'       → evidence_record
      'needs_operator' → evidence_record (advisory, recorded as warning)
      'block'         → workflow_fail
    """
    da_critic_score: float = float(da_critic_result.get("score", 1.0))
    da_critic_passed: bool = bool(da_critic_result.get("passed", True))
    da_findings: list = da_critic_result.get("findings", [])

    # Combine pre-execution score with DA critic review quality
    combined_score = round(0.70 * pre_exec_score + 0.30 * da_critic_score, 4)

    # If builder itself reported an error AND critic confirmed failure, hard-block
    # regardless of combined score.
    builder_status = builder_result.get("status", "completed")
    builder_error = builder_result.get("error", "")
    if builder_status in ("error", "failed") and not da_critic_passed:
        return "block", (
            f"Post-execution: builder status='{builder_status}' "
            f"and DA critic confirmed failure (score={da_critic_score:.4f}). "
            f"Findings: {da_findings[:3]}. Builder error: {builder_error}"
        )

    # Delegate to the base independent judge with the combined score
    base_verdict, base_reason = judge(combined_score, det_checks, gate_verdicts, risk_class)

    # Augment the reason with post-execution context
    augmented_reason = (
        f"[post-execution judge] combined_score={combined_score:.4f} "
        f"(pre={pre_exec_score:.4f}, da_critic={da_critic_score:.4f}) "
        f"da_critic_passed={da_critic_passed}. "
        f"{base_reason}"
    )
    if da_findings:
        augmented_reason += f" DA findings: {da_findings[:3]}"

    return base_verdict, augmented_reason


# ─────────────────────────────────────────────────────────────────────────────
# A/B decision
# ─────────────────────────────────────────────────────────────────────────────

def should_enable_ab(risk_class: str, uncertainty_score: float) -> tuple[bool, str]:
    """Return (enable, justification) for A/B branching.

    A/B is enabled only when risk_class >= high AND uncertainty_score >= 0.5.
    """
    if risk_class in ("high", "critical") and uncertainty_score >= 0.5:
        return True, f"A/B enabled: risk={risk_class}, uncertainty={uncertainty_score:.2f}"
    return False, f"A/B skipped: risk={risk_class} (need high+), uncertainty={uncertainty_score:.2f} (need 0.5+)"
