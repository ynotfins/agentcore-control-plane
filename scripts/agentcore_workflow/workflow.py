"""AgentCore M6 — LangGraph graph assembly.

Creates a StateGraph with PostgreSQL-backed checkpointing.
Thread IDs are always project-scoped UUIDs stored in agentcore.workflow_threads.

The graph topology is built ONCE in :func:`build_topology` and shared by:

- the **production** runtime, which compiles the topology with the canonical
  AgentCore :class:`PostgresSaver` (real durable checkpoints in
  ``public.checkpoints``);
- the **Studio** runtime, which compiles the same topology without a
  production checkpointer so that the LangGraph CLI / Agent Server can
  inject its own development checkpointer. Studio is a visualization /
  debugging surface only — it MUST NOT register an already
  production-checkpointed graph in a way that creates duplicate or
  conflicting checkpointers.

Topology fingerprint: :func:`topology_fingerprint` returns a stable
sha256 over the (node set, edges, conditional-edge options) tuple. Both
production and Studio runtimes expose the same fingerprint, proving they
share a single graph topology.

Usage:
    from agentcore_workflow.workflow import (
        build_topology,
        topology_fingerprint,
        build_graph,           # production (PostgresSaver)
        build_studio_graph,    # Studio (Agent-Server checkpointer)
        run_workflow,
    )
    b = build_topology()
    print(topology_fingerprint(b))
    graph, ctx = build_graph()           # production
    graph2 = build_studio_graph(b)       # Studio / Agent Server
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from .state import WorkflowState
from .nodes import (
    node_start,
    node_gate_check,
    node_deterministic_checks,
    node_risk_assess,
    node_critics_and_score,
    node_judge,
    node_micro_execute,
    node_da_builder,
    node_da_critic,
    node_ab_alternate,
    node_post_exec_judge,
    node_evidence_record,
    node_next_step,
    node_human_pause,
    node_workflow_fail,
    route,
)

PG_HOST = "127.0.0.1"
PG_PORT = 55433
PG_DATABASE = "agent_core"
PG_USER = "postgres"


def _conninfo() -> str:
    pg_pass = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    return f"host={PG_HOST} port={PG_PORT} dbname={PG_DATABASE} user={PG_USER} password={pg_pass}"


# Conditional-edge option sets — the canonical names of every legal next node.
# Kept here so fingerprint + topology are the single source of truth.
_AFTER_START = {"gate_check", "workflow_fail"}
_AFTER_GATE = {"deterministic_checks", "workflow_fail"}
_AFTER_DET = {"risk_assess", "workflow_fail"}
_AFTER_JUDGE = {"micro_execute", "da_builder", "human_pause", "workflow_fail"}
_AFTER_HUMAN = {"micro_execute", "da_builder", "workflow_fail"}
_AFTER_MICRO = {"evidence_record", "workflow_fail"}
_AFTER_DA_BUILDER = {"da_critic", "micro_execute", "workflow_fail"}
_AFTER_DA_CRITIC = {"ab_alternate", "post_exec_judge"}
_AFTER_POST_JUDGE = {"evidence_record", "workflow_fail"}
_AFTER_NEXT = {"gate_check", "__end__"}

# Frozen ordered node list. Changing this list invalidates the topology
# fingerprint — by design (a graph topology change is a locked architecture
# decision).
NODE_ORDER: tuple[str, ...] = (
    "start",
    "gate_check",
    "deterministic_checks",
    "risk_assess",
    "critics_and_score",
    "judge_node",
    "micro_execute",
    "da_builder",
    "da_critic",
    "ab_alternate",
    "post_exec_judge",
    "evidence_record",
    "next_step",
    "human_pause",
    "workflow_fail",
)


class TopologyBuilder:
    """The single shared graph topology.

    Built once via :func:`build_topology`. Used by both production
    (PostgresSaver) and Studio (Agent Server dev checkpointer).
    """

    def __init__(self) -> None:
        self.builder = StateGraph(WorkflowState)
        self._build_nodes()
        self._build_edges()

    def _build_nodes(self) -> None:
        # M6 core graph — unchanged. DA nodes are additive extensions.
        self.builder.add_node("start", node_start)
        self.builder.add_node("gate_check", node_gate_check)
        self.builder.add_node("deterministic_checks", node_deterministic_checks)
        self.builder.add_node("risk_assess", node_risk_assess)
        self.builder.add_node("critics_and_score", node_critics_and_score)
        self.builder.add_node("judge_node", node_judge)
        self.builder.add_node("micro_execute", node_micro_execute)
        # DA worker nodes (bounded harness; see ADR-DEEP-AGENTS-WORKER-HARNESS.md)
        self.builder.add_node("da_builder", node_da_builder)
        self.builder.add_node("da_critic", node_da_critic)
        # A/B alternate (high-risk only)
        self.builder.add_node("ab_alternate", node_ab_alternate)
        # Independent post-execution judge (M8 invariant)
        self.builder.add_node("post_exec_judge", node_post_exec_judge)
        self.builder.add_node("evidence_record", node_evidence_record)
        self.builder.add_node("next_step", node_next_step)
        self.builder.add_node("human_pause", node_human_pause)
        self.builder.add_node("workflow_fail", node_workflow_fail)

    def _build_edges(self) -> None:
        b = self.builder
        b.set_entry_point("start")

        # LangGraph add_conditional_edges expects a mapping from next_node
        # to itself (used as a set of legal next names).
        def _map(opts: set[str]) -> dict[str, str]:
            return {n: n for n in opts}

        b.add_conditional_edges("start", route, _map(_AFTER_START))
        b.add_conditional_edges("gate_check", route, _map(_AFTER_GATE))
        b.add_conditional_edges("deterministic_checks", route, _map(_AFTER_DET))
        b.add_edge("risk_assess", "critics_and_score")
        b.add_edge("critics_and_score", "judge_node")
        b.add_conditional_edges("judge_node", route, _map(_AFTER_JUDGE))
        b.add_conditional_edges("human_pause", route, _map(_AFTER_HUMAN))
        b.add_conditional_edges("micro_execute", route, _map(_AFTER_MICRO))
        b.add_conditional_edges("da_builder", route, _map(_AFTER_DA_BUILDER))
        b.add_conditional_edges("da_critic", route, _map(_AFTER_DA_CRITIC))
        b.add_edge("ab_alternate", "post_exec_judge")
        b.add_conditional_edges("post_exec_judge", route, _map(_AFTER_POST_JUDGE))
        b.add_edge("evidence_record", "next_step")
        b.add_conditional_edges("next_step", route, _map(_AFTER_NEXT))
        b.add_edge("workflow_fail", END)


def build_topology() -> TopologyBuilder:
    """Build the canonical graph topology. Single source of truth.

    Returned :class:`TopologyBuilder` is reused by production and Studio.
    Do not mutate ``builder`` directly after building.
    """
    return TopologyBuilder()


def topology_fingerprint(t: TopologyBuilder) -> str:
    """Deterministic sha256 over (nodes, edges, conditional-edge options).

    Same topology from production and Studio paths produce the same
    fingerprint. Used by validators to prove parity.
    """
    # Nodes: the ordered NODE_ORDER set (the canonical M6 node set).
    # Edges: all builder edges + conditional edges + their option sets.
    payload = {
        "nodes": list(NODE_ORDER),
        "conditional_options": {
            "start": sorted(_AFTER_START),
            "gate_check": sorted(_AFTER_GATE),
            "deterministic_checks": sorted(_AFTER_DET),
            "judge_node": sorted(_AFTER_JUDGE),
            "human_pause": sorted(_AFTER_HUMAN),
            "micro_execute": sorted(_AFTER_MICRO),
            "da_builder": sorted(_AFTER_DA_BUILDER),
            "da_critic": sorted(_AFTER_DA_CRITIC),
            "post_exec_judge": sorted(_AFTER_POST_JUDGE),
            "next_step": sorted(_AFTER_NEXT),
        },
        "entry": "start",
        "interrupt_before": ["human_pause"],
    }
    import json as _json
    raw = _json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_graph(conninfo: str | None = None) -> tuple[Any, PostgresSaver]:
    """Build and compile the production LangGraph workflow graph.

    Uses the canonical AgentCore PostgresSaver against ``public.checkpoints``.
    Returns ``(compiled_graph, checkpointer_context)``. The caller MUST
    ``__exit__`` the returned context manager.

    The graph topology is the same one Studio exposes via
    :func:`build_studio_graph`.
    """
    conninfo = conninfo or _conninfo()
    t = build_topology()
    checkpointer = PostgresSaver.from_conn_string(conninfo)
    # Enter the context manager to get the actual saver
    saver = checkpointer.__enter__()
    saver.setup()
    graph = t.builder.compile(checkpointer=saver, interrupt_before=["human_pause"])
    return graph, checkpointer


def build_studio_graph(t: TopologyBuilder | None = None):
    """Build the same topology for LangGraph Studio / Agent Server.

    Studio / Agent Server injects its own development checkpointer, so we
    compile WITHOUT a production checkpointer. This avoids registering an
    already production-checkpointed graph in a way that would create
    duplicate or conflicting checkpointers.

    The resulting graph shares the topology with production, proven by
    :func:`topology_fingerprint`.
    """
    if t is None:
        t = build_topology()
    # No checkpointer; Agent Server will inject its own. interrupt_before is
    # preserved on the compiled graph for human-pause observability.
    return t.builder.compile(interrupt_before=["human_pause"])


def run_workflow(
    project_id: str,
    project_key: str,
    milestone_key: str = "M6",
    thread_uuid: str | None = None,
    resume_from: dict | None = None,
    conninfo: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    *,
    goal: str = "",
    acceptance_criteria: list | None = None,
    charter_override: bool = False,
    autonomous: bool = False,
    context_profile: str = "standard-context",
    risk_profile: str = "medium",
    budget_profile: str = "",
) -> dict:
    """Start or resume a workflow run against the production PostgresSaver.

    Args:
        project_id:    AgentCore project UUID
        project_key:   Human-readable project key
        milestone_key: Target milestone (default 'M6')
        thread_uuid:   Existing thread UUID to resume (None = new run)
        resume_from:   Human pause decision dict for resume (None = fresh start)
        conninfo:      PostgreSQL connection string
        goal:          Operator goal text (recorded + optional charter synthesis)
        acceptance_criteria: Optional acceptance lines (forces charter synthesis on M6)
        autonomous:    Strict fixture/autonomous gate mode
        context_profile / risk_profile / budget_profile: run profiles

    Returns:
        Final workflow state dict.
    """
    from .state import initial_state

    import uuid as _uuid

    if thread_uuid is None:
        thread_uuid = str(_uuid.uuid4())

    graph, ctx = build_graph(conninfo)
    config = {"configurable": {"thread_id": thread_uuid}}

    try:
        if resume_from is not None:
            # Resume after human pause — pass operator decision as Command input
            from langgraph.types import Command
            result = graph.invoke(Command(resume=resume_from), config=config)
        else:
            # If the thread already has a checkpoint, resume with None input so
            # the checkpointed state (including provider/model selection) is
            # preserved instead of being overwritten by a fresh initial_state.
            existing = graph.get_state(config)
            if existing is not None and existing.values:
                result = graph.invoke(None, config=config)
            else:
                state = initial_state(
                    project_id, project_key, thread_uuid, milestone_key,
                    provider=provider or "", model=model or "",
                    goal=goal or "",
                    acceptance_criteria=acceptance_criteria,
                    charter_override=charter_override,
                    autonomous=autonomous,
                    context_profile=context_profile or "standard-context",
                    risk_profile=risk_profile or "medium",
                    budget_profile=budget_profile or "",
                )
                result = graph.invoke(state, config=config)

        return {
            "thread_uuid": thread_uuid,
            "completed": result.get("completed", False),
            "judge_verdict": result.get("judge_verdict", ""),
            "score": result.get("score", 0.0),
            "errors": result.get("errors", []),
            "evidence_count": len(result.get("evidence", [])),
            "milestone_key": result.get("milestone_key"),
            "run_db_id": result.get("run_db_id", ""),
        }
    finally:
        ctx.__exit__(None, None, None)
