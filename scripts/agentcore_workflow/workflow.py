"""AgentCore M6 — LangGraph graph assembly.

Creates a StateGraph with PostgreSQL-backed checkpointing.
Thread IDs are always project-scoped UUIDs stored in agentcore.workflow_threads.

Usage:
    from agentcore_workflow.workflow import build_graph, run_workflow
    graph = build_graph(conninfo)
    result = run_workflow(graph, project_id, project_key, milestone_key)
"""

from __future__ import annotations

import os
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from .state import WorkflowState, initial_state
from .nodes import (
    node_start,
    node_gate_check,
    node_deterministic_checks,
    node_risk_assess,
    node_critics_and_score,
    node_judge,
    node_micro_execute,
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


def build_graph(conninfo: str | None = None) -> tuple[Any, PostgresSaver]:
    """Build and compile the LangGraph workflow graph with PostgreSQL checkpointer.

    Returns (compiled_graph, checkpointer) so callers can close the checkpointer.
    """
    conninfo = conninfo or _conninfo()

    # Build the state graph
    builder = StateGraph(WorkflowState)

    # Add nodes
    builder.add_node("start", node_start)
    builder.add_node("gate_check", node_gate_check)
    builder.add_node("deterministic_checks", node_deterministic_checks)
    builder.add_node("risk_assess", node_risk_assess)
    builder.add_node("critics_and_score", node_critics_and_score)
    builder.add_node("judge_node", node_judge)
    builder.add_node("micro_execute", node_micro_execute)
    builder.add_node("evidence_record", node_evidence_record)
    builder.add_node("next_step", node_next_step)
    builder.add_node("human_pause", node_human_pause)
    builder.add_node("workflow_fail", node_workflow_fail)

    # Entry point
    builder.set_entry_point("start")

    # Edges from start
    builder.add_conditional_edges("start", route, {
        "gate_check": "gate_check",
        "workflow_fail": "workflow_fail",
    })

    # Gate check routes
    builder.add_conditional_edges("gate_check", route, {
        "deterministic_checks": "deterministic_checks",
        "workflow_fail": "workflow_fail",
    })

    # Deterministic checks routes
    builder.add_conditional_edges("deterministic_checks", route, {
        "risk_assess": "risk_assess",
        "workflow_fail": "workflow_fail",
    })

    # Risk assess → critics
    builder.add_edge("risk_assess", "critics_and_score")

    # Critics → judge
    builder.add_edge("critics_and_score", "judge_node")

    # Judge routes
    builder.add_conditional_edges("judge_node", route, {
        "micro_execute": "micro_execute",
        "human_pause": "human_pause",
        "workflow_fail": "workflow_fail",
    })

    # Human pause → micro_execute or fail (after operator decision)
    builder.add_conditional_edges("human_pause", route, {
        "micro_execute": "micro_execute",
        "workflow_fail": "workflow_fail",
    })

    # Micro execute → evidence
    builder.add_conditional_edges("micro_execute", route, {
        "evidence_record": "evidence_record",
        "workflow_fail": "workflow_fail",
    })

    # Evidence → next step
    builder.add_edge("evidence_record", "next_step")

    # Next step routes
    builder.add_conditional_edges("next_step", route, {
        "gate_check": "gate_check",
        "done": END,
    })

    # Terminals
    builder.add_edge("workflow_fail", END)

    # Compile with PostgreSQL checkpointer (context manager)
    checkpointer = PostgresSaver.from_conn_string(conninfo)
    # Enter the context manager to get the actual saver
    saver = checkpointer.__enter__()
    saver.setup()
    graph = builder.compile(checkpointer=saver, interrupt_before=["human_pause"])

    return graph, (checkpointer, saver)


def run_workflow(
    project_id: str,
    project_key: str,
    milestone_key: str = "M6",
    thread_uuid: str | None = None,
    resume_from: str | None = None,
    conninfo: str | None = None,
) -> dict:
    """Start or resume a workflow run.

    Args:
        project_id:    AgentCore project UUID
        project_key:   Human-readable project key
        milestone_key: Target milestone (default 'M6')
        thread_uuid:   Existing thread UUID to resume (None = new run)
        resume_from:   Human pause decision dict for resume (None = fresh start)
        conninfo:      PostgreSQL connection string

    Returns:
        Final workflow state dict.
    """
    import uuid as _uuid

    if thread_uuid is None:
        thread_uuid = str(_uuid.uuid4())

    graph, (ctx, saver) = build_graph(conninfo)
    config = {"configurable": {"thread_id": thread_uuid}}

    try:
        if resume_from is not None:
            # Resume after human pause — pass operator decision as Command input
            from langgraph.types import Command
            result = graph.invoke(Command(resume=resume_from), config=config)
        else:
            # Fresh start or automatic resume from checkpoint
            state = initial_state(project_id, project_key, thread_uuid, milestone_key)
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
