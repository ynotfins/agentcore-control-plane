"""AgentCore M6 — Workflow state schema for LangGraph.

All state fields are project/thread-scoped. The state is persisted by the
LangGraph PostgreSQL checkpointer. Additional durable state is written to
the agentcore schema tables via the workflow nodes.
"""

from __future__ import annotations

from typing import Annotated, Any
from typing_extensions import TypedDict
import operator


def _merge_dict(a: dict, b: dict) -> dict:
    """Merge update dicts (last writer wins per key)."""
    return {**a, **b}


def _merge_list(a: list, b: list) -> list:
    """Append new items to a list."""
    return a + b


class WorkflowState(TypedDict):
    # ── Identity (set once, never changed by nodes) ──────────────────────────
    project_id: str          # AgentCore project UUID
    project_key: str         # human-readable project key
    thread_uuid: str         # LangGraph thread_id (= workflow_threads.thread_id)
    run_db_id: str           # wf_runs.id UUID (PK in agentcore)
    provider: str            # LLM provider (e.g., "openrouter")
    model: str               # Selected model ID

    # ── Milestone tracking ────────────────────────────────────────────────────
    milestone_key: str       # e.g. "M6"
    milestone_db_id: str     # wf_milestones.id UUID
    current_macro_key: str   # current macro step key
    current_macro_db_id: str
    current_micro_key: str   # current micro step key
    current_micro_db_id: str

    # ── Step catalogue (loaded from DB, used for navigation) ─────────────────
    macro_steps: list[dict]  # [{key, label, ordinal, risk_class}]
    micro_steps: list[dict]  # [{key, label, ordinal, risk_class, macro_key}]
    checklist_items: list[dict]  # [{key, label, ordinal, micro_key}]

    # ── Gate results (accumulated across the run) ─────────────────────────────
    gates_passed: Annotated[list[str], _merge_list]   # gate names that passed
    gates_failed: Annotated[list[str], _merge_list]   # gate names that failed

    # ── Deterministic check results ───────────────────────────────────────────
    det_checks_passed: bool
    det_checks_details: Annotated[list[dict], _merge_list]

    # ── Risk assessment ───────────────────────────────────────────────────────
    current_risk_class: str  # low|medium|high|critical
    ab_enabled: bool
    ab_db_id: str            # workflow_ab_experiments.id if A/B active

    # ── Critic/scorer/judge ───────────────────────────────────────────────────
    critic_results: Annotated[list[dict], _merge_list]
    score: float             # 0.0 – 1.0 deterministic score
    judge_verdict: str       # proceed|needs_operator|block

    # ── Human pause ──────────────────────────────────────────────────────────
    pause_db_id: str         # workflow_human_pauses.id if paused
    pause_resolution: str    # pending|approved|rejected|overridden|timeout
    operator_decision: str   # operator's textual decision

    # ── Tool leases ──────────────────────────────────────────────────────────
    active_lease_id: str     # current capability_leases.id
    active_lease_tool: str   # tool name under active JIT lease

    # ── AgentCore memory session (via agentcore-gateway MCP) ─────────────────
    memory_session_id: str   # agentcore-memory session_id opened through gateway

    # ── Deep Agents worker harness (optional, bounded) ────────────────────────
    # All DA fields are worker-scoped; M6 PostgresSaver is the canonical checkpoint.
    # worktree_path is set from the project root_path at run start; DA workers
    # are restricted to this path via FilesystemMiddleware.
    worktree_path: str       # absolute path to assigned Git worktree (D:\\ only)
    da_enabled: bool         # True when DA workers are active for this step
    da_builder_result: dict  # last DA builder output (ephemeral, recorded to wf_evidence)
    da_critic_result: dict   # last DA critic output (findings only; post_exec_judge adjudicates)
    da_combined_score: float # post-execution combined score (0.70 * pre-exec + 0.30 * DA critic)
    post_exec_verdict: str   # verdict from post_exec_judge: proceed|needs_operator|block

    # ── A/B alternate implementation (optional, bounded, high-risk only) ─────
    # Activated by node_risk_assess when ab_enabled=True (risk >= high, uncertainty >= 0.5).
    # The B-path runs in an isolated git worktree on I: (disposable scratch) and is
    # archived to E:\\AgentCoreArchive\\ab-worktrees\\ after the run.
    # Low-risk work never creates an alt worktree; these fields remain empty.
    ab_alt_worktree_path: str  # path to isolated alternate worktree (I:\\ only); "" when unused
    ab_alt_result: dict        # B-path DA builder result (empty dict when unused)
    ab_selected: str           # "A"|"B"|"both_rejected"|"operator_review"|"" (unset)

    # ── Evidence accumulation ─────────────────────────────────────────────────
    evidence: Annotated[list[dict], _merge_list]

    # ── Execution result ─────────────────────────────────────────────────────
    execution_result: dict
    errors: Annotated[list[str], _merge_list]

    # ── Control flow ─────────────────────────────────────────────────────────
    next_action: str         # node to route to (used by conditional edges)
    completed: bool


def initial_state(
    project_id: str,
    project_key: str,
    thread_uuid: str,
    milestone_key: str = "M6",
    provider: str = "",
    model: str = "",
) -> WorkflowState:
    """Return a fresh workflow state for a new run."""
    return WorkflowState(
        project_id=project_id,
        project_key=project_key,
        thread_uuid=thread_uuid,
        run_db_id="",
        provider=provider,
        model=model,
        milestone_key=milestone_key,
        milestone_db_id="",
        current_macro_key="",
        current_macro_db_id="",
        current_micro_key="",
        current_micro_db_id="",
        macro_steps=[],
        micro_steps=[],
        checklist_items=[],
        gates_passed=[],
        gates_failed=[],
        det_checks_passed=False,
        det_checks_details=[],
        current_risk_class="low",
        ab_enabled=False,
        ab_db_id="",
        critic_results=[],
        score=0.0,
        judge_verdict="",
        pause_db_id="",
        pause_resolution="",
        operator_decision="",
        active_lease_id="",
        active_lease_tool="",
        memory_session_id="",
        worktree_path="",
        da_enabled=False,
        da_builder_result={},
        da_critic_result={},
        da_combined_score=0.0,
        post_exec_verdict="",
        ab_alt_worktree_path="",
        ab_alt_result={},
        ab_selected="",
        evidence=[],
        execution_result={},
        errors=[],
        next_action="gate_check",
        completed=False,
    )
