"""{{ project_name }} — LangGraph graph assembly and entry points."""

from __future__ import annotations

import os
import uuid
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, END

from .state import WorkflowState, initial_state
from .nodes import (
    node_step_one,
    node_step_two,
    node_workflow_fail,
    route,
{% if enable_human_pause %}
    node_human_pause,
{% endif %}
)

PG_HOST = "{{ pg_host }}"
PG_PORT = {{ pg_port }}
PG_DATABASE = "{{ pg_database }}"
PG_USER = "{{ pg_user }}"
PG_PASSWORD_ENV = "{{ pg_password_env }}"


def _conninfo() -> str:
    pg_pass = os.environ.get(PG_PASSWORD_ENV, "")
    return f"host={PG_HOST} port={PG_PORT} dbname={PG_DATABASE} user={PG_USER} password={pg_pass}"


def build_graph(conninfo: str | None = None):
    """Build and compile the workflow graph with PostgreSQL checkpointer."""
    conninfo = conninfo or _conninfo()
    builder = StateGraph(WorkflowState)

    builder.add_node("step_one", node_step_one)
    builder.add_node("step_two", node_step_two)
    builder.add_node("workflow_fail", node_workflow_fail)
    builder.set_entry_point("step_one")
{% if enable_human_pause %}
    builder.add_node("human_pause", node_human_pause)
    builder.add_conditional_edges("step_one", route, {
        "step_two": "step_two",
        "human_pause": "human_pause",
        "workflow_fail": "workflow_fail",
    })
    builder.add_conditional_edges("human_pause", route, {
        "step_two": "step_two",
        "workflow_fail": "workflow_fail",
    })
{% else %}
    builder.add_conditional_edges("step_one", route, {
        "step_two": "step_two",
        "workflow_fail": "workflow_fail",
    })
{% endif %}
    builder.add_conditional_edges(
        "step_two", route, {"done": END, "workflow_fail": "workflow_fail"}
    )
    builder.add_edge("workflow_fail", END)

    ctx = PostgresSaver.from_conn_string(conninfo)
    saver = ctx.__enter__()
    saver.setup()
    graph = builder.compile(
        checkpointer=saver,
{% if enable_human_pause %}
        interrupt_before=["human_pause"],
{% endif %}
    )
    return graph, ctx


def run_new(project_id: str | None = None, conninfo: str | None = None) -> dict:
    """Start a new workflow run. Returns the final state and thread_id."""
    thread_id = str(uuid.uuid4())
    project_id = project_id or "default"
    graph, ctx = build_graph(conninfo)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = initial_state(project_id, thread_id)
        result = graph.invoke(state, config=config)
        return {
            "thread_id": thread_id,
            "completed": result.get("completed"),
            "errors": result.get("errors", []),
        }
    finally:
        ctx.__exit__(None, None, None)


def run_resume(thread_id: str, resume_value: Any = None, conninfo: str | None = None) -> dict:
    """Resume from a PostgreSQL checkpoint."""
    graph, ctx = build_graph(conninfo)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        if resume_value is not None:
            from langgraph.types import Command
            result = graph.invoke(Command(resume=resume_value), config=config)
        else:
            result = graph.invoke(None, config=config)
        return {
            "thread_id": thread_id,
            "completed": result.get("completed"),
            "errors": result.get("errors", []),
        }
    finally:
        ctx.__exit__(None, None, None)
