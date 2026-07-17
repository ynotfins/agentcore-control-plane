# Recipe 11 — Deep Agents Worker Harness inside M6 LangGraph Nodes

**Pattern:** Use `deepagents` as a bounded worker inside AgentCore M6 nodes.  
**Stack:** Python 3.12+, deepagents==0.6.12, LangGraph 1.2.5.  
**Decision:** `docs/decisions/ADR-DEEP-AGENTS-WORKER-HARNESS.md`  
**Authority:** BLUEPRINT.md — "Deep Agents may be used as an optional worker harness
inside LangGraph nodes; it is not a canonical memory, workflow, policy, or tool authority."

---

## What Deep Agents provides here

- `FilesystemMiddleware` + `FilesystemPermission` — worktree-scoped file access
- `create_deep_agent()` — a focused LLM loop for builder/critic tasks
- The agent uses a short-lived MemorySaver (ephemeral); M6 PostgresSaver is canonical

## What is disabled

- `MemoryMiddleware` — would create a competing AGENTS.md source of truth
- LangSmith tracing — external data egress risk
- `.env` file loading — secrets come from Windows User env vars only

---

## Builder Worker (read-write, restricted to worktree)

```python
from agentcore_workflow.deepagents_worker import run_builder_worker
from agentcore_workflow import db as wfdb

# 1. Verify tool is leased for this project
tools = wfdb.get_project_tools(project_id)
active = [t["tool_name"] for t in tools if t["tool_state"] in ("core_active", "jit_leased")]
if "deepagents-builder" not in active:
    raise PermissionError("deepagents-builder tool not in active capability profile")

# 2. Get AgentCore context (startup_context from agentcore-memory)
context_str = "Project: my-project\nMilestone: M6\n..."  # from startup_context

# 3. Run the builder worker
result = run_builder_worker(
    task="Write a hello-world function with tests in src/hello.py",
    worktree_path="D:\\github\\my-project",  # must be under D:\\
    agentcore_context=context_str,
    model="openai:gpt-4o-mini",
    max_iterations=3,
    allowed_tools=active,
    project_id=project_id,
    thread_uuid=thread_uuid,
)

# 4. Record evidence through agentcore-memory (never through deepagents)
wfdb.record_evidence(
    run_db_id, project_id, "M6.2.1",
    "builder_result", f"Builder: {result['status']}",
    result, "system_verified",
)
```

## Critic Worker (read-only)

```python
from agentcore_workflow.deepagents_worker import run_critic_worker

result = run_critic_worker(
    task="Review the code in src/hello.py for correctness and test coverage",
    worktree_path="D:\\github\\my-project",
    agentcore_context=context_str,
    rubric="PASS if: function exists, has type hints, has at least one test.",
    model="openai:gpt-4o-mini",
    max_iterations=2,
    project_id=project_id,
    thread_uuid=thread_uuid,
)
# result["passed"] → bool
# result["score"] → 0.0-1.0
# result["critique"] → {"passed": ..., "score": ..., "findings": [...]}
```

## Drift Gate

```python
from agentcore_workflow.deepagents_worker import compute_drift, gate_drift

# Deterministic check — no LLM, no network
drift = compute_drift(
    diff="--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-x=1\n+x=2\n",
    plan=["update main.py variable"],
)
# drift["passed"] → True/False
# drift["score"]  → 0.0-1.0

# In the M6 gate_check node (via GATE_REGISTRY["drift"]):
verdict, detail = gate_drift(state)  # runs before any LLM critic
```

## Rules

1. **Never use MemoryMiddleware** — it reads AGENTS.md files.
2. **Never pass secrets** in `agentcore_context` or `task`.
3. **Worktree must be under D:\\** — `_validate_worktree()` enforces this.
4. **Record evidence via db.record_evidence()** after the worker returns.
5. **Check capability profile** before invoking the worker (test 3 proof).
6. **MemorySaver is ephemeral** — do not rely on deep agent internal state across M6 nodes.
7. **PostgresSaver is canonical** — M6 resumes from PostgreSQL checkpoints, not DA state.
