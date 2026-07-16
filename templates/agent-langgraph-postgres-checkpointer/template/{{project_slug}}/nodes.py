"""{{ project_name }} — LangGraph workflow nodes."""

from __future__ import annotations

from datetime import UTC, datetime

{% if enable_human_pause %}
from langgraph.types import interrupt
{% endif %}

from .state import WorkflowState


def _now() -> str:
    return datetime.now(UTC).isoformat()


def node_step_one(state: WorkflowState) -> dict:
    """First workflow step — implement your logic here."""
    return {
        "steps_completed": ["step_one"],
        "evidence": [{"step": "step_one", "ts": _now(), "result": "ok"}],
        "next_action": "step_two",
    }


def node_step_two(state: WorkflowState) -> dict:
    """Second workflow step."""
    return {
        "steps_completed": ["step_two"],
        "evidence": [{"step": "step_two", "ts": _now(), "result": "ok"}],
        "next_action": "done",
        "completed": True,
    }

{% if enable_human_pause %}

def node_human_pause(state: WorkflowState) -> dict:
    """Pause for operator review. Resume with Command(resume=decision)."""
    question = (
        f"Review required for thread {state['thread_id']}. "
        f"Steps completed: {state['steps_completed']}. Approve?"
    )
    operator_decision = interrupt({"question": question, "thread_id": state["thread_id"]})

    if isinstance(operator_decision, dict):
        decision_text = operator_decision.get("decision", "")
        # notes = operator_decision.get("notes", "")  # available for DB recording
    else:
        decision_text = str(operator_decision)

    approved = decision_text.strip().lower() in ("yes", "approve", "y")
    return {
        "pause_resolution": "approved" if approved else "rejected",
        "operator_decision": decision_text,
        "next_action": "step_two" if approved else "workflow_fail",
        "errors": [] if approved else [f"Operator rejected: {decision_text}"],
    }

{% endif %}


def node_workflow_fail(state: WorkflowState) -> dict:
    """Terminal failure node."""
    return {"completed": True, "next_action": "done"}


def route(state: WorkflowState) -> str:
    return state.get("next_action", "workflow_fail")
