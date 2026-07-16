# {{ project_name }}

LangGraph agent with PostgreSQL checkpointing.  
Generated from `templates/agent-langgraph-postgres-checkpointer`.

**Authority:** AgentCore Engineering Constitution §7  
**Checkpointer:** `langgraph-checkpoint-postgres==3.1.0`  
**Database:** PostgreSQL 18 on `{{ pg_host }}:{{ pg_port }}`

## Prerequisites

Set the PostgreSQL password as a Windows User-scope environment variable:

```powershell
[System.Environment]::SetEnvironmentVariable("{{ pg_password_env }}", "...", "User")
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run

```powershell
python -c "from {{ project_slug }}.workflow import run_new; print(run_new())"
```

## Resume After Restart

```powershell
python -c "
from {{ project_slug }}.workflow import run_resume
print(run_resume('<thread_id_from_previous_run>'))
"
```

## Test

```powershell
pytest tests/ -v
```

## Lint and Type Check

```powershell
ruff check {{ project_slug }}/ tests/
mypy {{ project_slug }}/
```

## Architecture

```
{{ project_slug }}/
  __init__.py        — version
  state.py           — WorkflowState TypedDict + initial_state()
  nodes.py           — node functions (step_one, step_two{% if enable_human_pause %}, human_pause{% endif %})
  workflow.py        — graph assembly + PostgresSaver + run_new/run_resume
tests/
  test_workflow.py   — checkpoint/resume integration tests
```

## Human Review ({% if enable_human_pause %}enabled{% else %}disabled{% endif %})

{% if enable_human_pause %}
This agent supports human-review pauses. When a node calls `interrupt()`, the graph
suspends. Resume with:

```python
from {{ project_slug }}.workflow import run_resume
run_resume(thread_id, resume_value={"decision": "yes", "notes": "Approved manually"})
```
{% else %}
Human-review support is disabled for this template instance. Regenerate with
`enable_human_pause: true` to enable it.
{% endif %}

## Update Template

```powershell
copier update
```

## Rollback

Restore from Git: `git checkout <sha> -- {{ project_slug }}/`
