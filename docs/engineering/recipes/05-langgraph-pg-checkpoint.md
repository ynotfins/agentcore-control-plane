# Recipe 05 — LangGraph PostgreSQL Checkpoint and Resume

**Pattern:** Durable workflow with restart-safe checkpointing.  
**Stack:** Python 3.12+, LangGraph 1.2.5, langgraph-checkpoint-postgres 3.1.0.  
**Reference implementation:** `docs/engineering/reference-implementations/langgraph-checkpoint-resume/`  
**Authority:** `docs/engineering/CONSTITUTION.md` §7.

---

## Setup (one-time per database)

```python
from langgraph.checkpoint.postgres import PostgresSaver
import os

conninfo = (
    f"host=127.0.0.1 port=55433 dbname=agent_core "
    f"user=postgres password={os.environ['AGENT_CORE_POSTGRES_PASSWORD']}"
)

with PostgresSaver.from_conn_string(conninfo) as saver:
    saver.setup()  # creates public.checkpoints, checkpoint_blobs, checkpoint_writes
```

## State Definition

```python
from __future__ import annotations
from typing import Annotated
from typing_extensions import TypedDict
import operator

class WorkflowState(TypedDict):
    project_id: str
    thread_id: str
    items: Annotated[list[str], operator.add]  # reducer: append new items
    completed: bool
    next_action: str
```

## Graph with Checkpointer

```python
import uuid
from langgraph.graph import StateGraph, END

def build_graph(conninfo: str):
    builder = StateGraph(WorkflowState)
    builder.add_node("step_a", node_step_a)
    builder.add_node("step_b", node_step_b)
    builder.set_entry_point("step_a")
    builder.add_conditional_edges("step_a", route, {"step_b": "step_b", "done": END})
    builder.add_edge("step_b", END)

    with PostgresSaver.from_conn_string(conninfo) as saver:
        saver.setup()
        graph = builder.compile(checkpointer=saver)
        yield graph  # caller must stay within context


def route(state: WorkflowState) -> str:
    return state["next_action"]
```

## Starting a New Run

```python
thread_id = str(uuid.uuid4())  # unique per run; never reuse
config = {"configurable": {"thread_id": thread_id}}
initial = WorkflowState(project_id="proj-123", thread_id=thread_id, items=[], completed=False, next_action="step_b")

with build_graph_context(conninfo) as graph:
    result = graph.invoke(initial, config=config)
    print(result["thread_id"])  # save this for resume
```

## Resuming After Process Restart

```python
# thread_id was saved; graph state is in PostgreSQL
config = {"configurable": {"thread_id": saved_thread_id}}

with build_graph_context(conninfo) as graph:
    # invoke with None to resume from last checkpoint
    result = graph.invoke(None, config=config)
```

## Rules

- Thread IDs must be UUID strings under 255 characters.
- Never reuse a thread ID for a different logical run.
- `setup()` is idempotent — safe to call on every startup.
- Checkpoint blobs must not contain secret values.
- Use `interrupt_before=["human_pause"]` to enable operator review pauses.
