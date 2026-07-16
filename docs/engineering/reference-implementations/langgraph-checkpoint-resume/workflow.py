#!/usr/bin/env python3
"""Reference implementation — LangGraph PostgreSQL checkpoint and resume.

Teaches ONE pattern: how to build a durable LangGraph workflow that resumes
after process restart using PostgreSQL checkpoints.

This is a reference implementation, not a template. See:
    templates/agent-langgraph-postgres-checkpointer/  for the Copier template.
    recipes/05-langgraph-pg-checkpoint.md  for the recipe.

Run:
    python workflow.py start    # start a new run, prints thread_id
    python workflow.py resume <thread_id>   # resume from checkpoint
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Annotated
from typing_extensions import TypedDict
import operator

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, END

PG_PASS = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
CONNINFO = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={PG_PASS}"


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

class State(TypedDict):
    thread_id: str
    steps_completed: Annotated[list[str], operator.add]  # accumulates via reducer
    next_action: str
    completed: bool


# ─────────────────────────────────────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────────────────────────────────────

def node_step_one(state: State) -> dict:
    print(f"[step_one] thread={state['thread_id']}", file=sys.stderr)
    return {"steps_completed": ["step_one"], "next_action": "step_two"}


def node_step_two(state: State) -> dict:
    print(f"[step_two] thread={state['thread_id']}", file=sys.stderr)
    return {"steps_completed": ["step_two"], "next_action": "done", "completed": True}


def route(state: State) -> str:
    return state.get("next_action", "done")


# ─────────────────────────────────────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────────────────────────────────────

def build_graph(saver: PostgresSaver):
    builder = StateGraph(State)
    builder.add_node("step_one", node_step_one)
    builder.add_node("step_two", node_step_two)
    builder.set_entry_point("step_one")
    builder.add_conditional_edges("step_one", route, {
        "step_two": "step_two",
        "done": END,
    })
    builder.add_conditional_edges("step_two", route, {
        "done": END,
    })
    return builder.compile(checkpointer=saver)


# ─────────────────────────────────────────────────────────────────────────────
# Entry points
# ─────────────────────────────────────────────────────────────────────────────

def start_new() -> str:
    thread_id = str(uuid.uuid4())
    with PostgresSaver.from_conn_string(CONNINFO) as saver:
        saver.setup()
        graph = build_graph(saver)
        config = {"configurable": {"thread_id": thread_id}}
        initial = State(
            thread_id=thread_id,
            steps_completed=[],
            next_action="step_two",
            completed=False,
        )
        result = graph.invoke(initial, config=config)
    print(json.dumps({"thread_id": thread_id, "result": result}))
    return thread_id


def resume(thread_id: str) -> dict:
    """Resume from the last PostgreSQL checkpoint for thread_id."""
    with PostgresSaver.from_conn_string(CONNINFO) as saver:
        graph = build_graph(saver)
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(None, config=config)
    print(json.dumps({"thread_id": thread_id, "result": result}))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python workflow.py start | resume <thread_id>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "start":
        start_new()
    elif cmd == "resume" and len(sys.argv) == 3:
        resume(sys.argv[2])
    else:
        print("Usage: python workflow.py start | resume <thread_id>")
        sys.exit(1)
