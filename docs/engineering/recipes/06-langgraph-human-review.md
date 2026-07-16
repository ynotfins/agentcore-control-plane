# Recipe 06 — LangGraph Human-Review Pause/Resume

**Pattern:** Suspend a workflow for operator decision and resume with the response.  
**Stack:** Python 3.12+, LangGraph 1.2.5, PostgreSQL 18.  
**Authority:** `docs/engineering/CONSTITUTION.md` §7.3.

---

## Pause Node

```python
from langgraph.types import interrupt

def node_human_pause(state: WorkflowState) -> dict:
    """Pause for operator review. Resume with Command(resume=decision)."""
    pause_context = {
        "question": f"Approve {state['current_step']}?",
        "score": state.get("score"),
        "risk_class": state.get("risk_class"),
    }

    # interrupt() suspends graph execution here
    # The value passed is returned to the caller as the interrupt value
    operator_decision = interrupt(pause_context)

    # After resume: process the decision
    if isinstance(operator_decision, dict):
        approved = operator_decision.get("decision", "").lower() in ("yes", "approve", "y")
        notes = operator_decision.get("notes", "")
    else:
        approved = str(operator_decision).lower() in ("yes", "approve", "y")
        notes = ""

    return {
        "operator_approved": approved,
        "operator_notes": notes,
        "next_action": "execute" if approved else "abort",
    }
```

## Graph with interrupt_before

```python
graph = builder.compile(
    checkpointer=saver,
    interrupt_before=["human_pause"],  # pause BEFORE executing human_pause node
)
```

## Starting Until Pause

```python
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

result = graph.invoke(initial_state, config=config)
# Graph returns at the interrupt point
# result contains the state up to the pause
```

## Resuming After Operator Decision

```python
from langgraph.types import Command

operator_decision = {"decision": "yes", "notes": "Verified manually"}

result = graph.invoke(
    Command(resume=operator_decision),  # pass the decision as resume value
    config=config,
)
```

## PostgreSQL Pause Record

Always record pauses in `agentcore.wf_human_pauses`:

```python
pause_id = db.create_pause(
    run_db_id, project_id, scope_key, question, context_summary
)
# On resume:
db.resolve_pause(pause_id, project_id, "approved", decision_text, notes)
```

## Timeout Pattern

```python
# Set timeout in the pause record
# A scheduled task or worker calls expire_wf_jit_leases() to clean up stale pauses
# Workflow checks timeout_at in the state before resuming
```

## Rules

- `interrupt_before` not `interrupt_after` — less surprising recovery.
- Always record the pause in PostgreSQL; the LangGraph checkpoint alone is insufficient evidence.
- Resolve the pause record when the operator responds.
- Default timeout: 24 hours. Set `timeout_at` to enforce.
- After rejection, route to a `workflow_fail` or `abort` node — never silently proceed.
