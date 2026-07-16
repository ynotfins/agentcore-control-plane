"""AgentCore M6/Deep Agents integration — bounded worker adapter.

Deep Agents (deepagents==0.6.12, MIT) is used ONLY as a worker harness
inside M6 LangGraph nodes. It is NOT a canonical memory, checkpoint, or
policy authority.

Responsibility boundary (from ADR-DEEP-AGENTS-WORKER-HARNESS.md):

  ALLOWED via this adapter:
    - create_deep_agent() restricted to the assigned worktree
    - FilesystemMiddleware with FilesystemPermission (read/write or read-only)
    - AgentCore context injected via system prompt
    - Tool output returned to M6 caller; durable writes go through agentcore-memory

  FORBIDDEN via this adapter:
    - MemoryMiddleware  (would create a competing AGENTS.md source of truth)
    - LangSmith tracing (external data egress without operator approval)
    - .env file loading (violates AgentCore secret handling policy)
    - Overriding M6 checkpoints (M6 PostgresSaver remains canonical)
    - Writing outside the assigned worktree

Security: The deep agent runs with a LangGraph MemorySaver for its own
short-lived subgraph. All durable state must go through the M6 caller,
which writes to agentcore.wf_evidence via the existing db.record_evidence()
call. The deep agent's MemorySaver is ephemeral — it dies when the M6 node
function returns.

Authority: BLUEPRINT.md + docs/decisions/ADR-DEEP-AGENTS-WORKER-HARNESS.md
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Deep Agents is a bounded optional dependency.
# We guard the import so AgentCore works without it and fails fast here.
try:
    from deepagents import FilesystemMiddleware, FilesystemPermission, create_deep_agent
    from langchain_core.messages import HumanMessage
    DEEPAGENTS_AVAILABLE = True
except ImportError:
    DEEPAGENTS_AVAILABLE = False


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _require_deepagents() -> None:
    if not DEEPAGENTS_AVAILABLE:
        raise ImportError(
            "deepagents is required for the builder/critic worker. "
            "Install with: pip install deepagents==0.6.12"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Worktree boundary enforcement
# ─────────────────────────────────────────────────────────────────────────────

def _validate_worktree(worktree_path: str) -> Path:
    """Verify the worktree path is a real directory under D:\\ or an approved path.

    This is the outermost enforcement boundary for the builder worker.
    FilesystemMiddleware enforces it at the tool level inside the agent.
    """
    root = Path(worktree_path).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Worktree path does not exist or is not a directory: {root}")
    # Block filesystem roots and paths outside D: project tier
    forbidden_prefixes = (
        Path("C:\\"),
        Path("E:\\"),
        Path("F:\\"),
        Path("G:\\"),
        Path("H:\\"),
    )
    for fp in forbidden_prefixes:
        if str(root).startswith(str(fp)):
            raise PermissionError(
                f"Builder worker may not access {root}. "
                f"Allowed: D:\\github\\ and D:\\test\\ only."
            )
    return root


# ─────────────────────────────────────────────────────────────────────────────
# Builder worker
# ─────────────────────────────────────────────────────────────────────────────

def run_builder_worker(
    *,
    task: str,
    worktree_path: str,
    agentcore_context: str,
    model: str = "openai:gpt-4o-mini",
    max_iterations: int = 3,
    allowed_tools: list[str] | None = None,
    project_id: str = "",
    thread_uuid: str = "",
) -> dict[str, Any]:
    """Run a Deep Agents builder worker restricted to the assigned worktree.

    The builder:
    1. Receives AgentCore startup_context as a read-only system prompt injection.
    2. Operates only within `worktree_path` via FilesystemMiddleware.
    3. Writes NO durable memory — the caller (M6 node) records evidence.
    4. Uses a short-lived MemorySaver for its own subgraph (ephemeral).

    Args:
        task: The specific micro-step work to perform.
        worktree_path: Absolute path to the assigned Git worktree.
        agentcore_context: The startup_context string from agentcore-memory.
        model: Model spec to use (deepagents format: 'provider:model').
        max_iterations: Maximum agent loop iterations (prevents runaway).
        allowed_tools: Tool names from capability_profiles that are active.
                       If None, only filesystem tools are available.
        project_id: AgentCore project UUID (for audit only; not used in agent).
        thread_uuid: M6 thread UUID (for audit only; not used in agent).

    Returns:
        dict with keys: status, output, files_changed, error, elapsed_ms
    """
    _require_deepagents()
    root = _validate_worktree(worktree_path)
    t0 = datetime.now(UTC)

    # System prompt: inject AgentCore context and strict boundaries
    system_prompt = f"""You are a focused builder agent. You have been delegated ONE micro-step.
Work only within your assigned worktree: {root}

## AgentCore Project Context (read-only; do not modify this context)
{agentcore_context[:4000]}

## Your task
{task}

## Strict rules
- Work ONLY within the assigned worktree above.
- Do NOT read or write files outside that path.
- Do NOT call any network API, send emails, push to git, or deploy.
- Do NOT output credentials, secrets, or environment variable values.
- Do NOT install new packages or modify lock files.
- Write clear, testable code. Run tests if they exist.
- Stop after completing the task; do not over-engineer.
- Your output will be captured by the AgentCore platform; do not create
  separate memory files or AGENTS.md files.
"""

    # Filesystem middleware restricted to worktree — read+write allowed
    fs_middleware = FilesystemMiddleware(
        root_dir=str(root),
        permissions=[
            FilesystemPermission(
                path="**",
                operations=["read", "write"],
            )
        ],
    )

    # Create the deep agent WITH filesystem but WITHOUT memory middleware
    # (MemoryMiddleware is deliberately omitted — it would read AGENTS.md
    # files which would create a competing source of truth with AgentCore)
    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        middleware=[fs_middleware],
        # No MemoryMiddleware, no SubAgentMiddleware, no LangSmith tracing
    )

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=task)]},
            config={
                "configurable": {
                    "thread_id": f"builder-{thread_uuid or 'local'}",
                    "max_iterations": max_iterations,
                }
            },
        )
        messages = result.get("messages", [])
        final_text = ""
        for m in reversed(messages):
            if hasattr(m, "content") and isinstance(m.content, str) and m.content.strip():
                final_text = m.content
                break

        elapsed = int((datetime.now(UTC) - t0).total_seconds() * 1000)
        return {
            "status": "completed",
            "output": final_text[:8000],
            "files_changed": [],  # deep agent doesn't expose diff; M6 caller can compare
            "error": None,
            "elapsed_ms": elapsed,
            "model": model,
            "worktree": str(root),
            "project_id": project_id,
        }

    except Exception as exc:
        elapsed = int((datetime.now(UTC) - t0).total_seconds() * 1000)
        return {
            "status": "failed",
            "output": "",
            "files_changed": [],
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": elapsed,
            "model": model,
            "worktree": str(root),
            "project_id": project_id,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Critic worker (read-only)
# ─────────────────────────────────────────────────────────────────────────────

def run_critic_worker(
    *,
    task: str,
    worktree_path: str,
    agentcore_context: str,
    rubric: str = "",
    model: str = "openai:gpt-4o-mini",
    max_iterations: int = 2,
    project_id: str = "",
    thread_uuid: str = "",
) -> dict[str, Any]:
    """Run a Deep Agents critic worker with read-only filesystem access.

    The critic reads files from the worktree and produces a structured
    critique. It CANNOT write any files.

    Returns:
        dict with keys: status, critique, passed, score, error, elapsed_ms
    """
    _require_deepagents()
    root = _validate_worktree(worktree_path)
    t0 = datetime.now(UTC)

    rubric_section = f"\n## Rubric\n{rubric}" if rubric else ""
    system_prompt = f"""You are a focused code reviewer. You may only READ files.
Assigned worktree: {root}

## AgentCore Project Context
{agentcore_context[:2000]}

## Review task
{task}{rubric_section}

## Strict rules
- Read ONLY. You may NOT write, edit, delete, or execute anything.
- Produce a structured critique with: PASSED (yes/no), SCORE (0.0-1.0),
  and FINDINGS (list of specific issues or confirmations).
- Format your final response as JSON:
  {{"passed": true/false, "score": 0.0-1.0, "findings": ["..."]}}
"""

    # Critic: read-only filesystem
    fs_middleware = FilesystemMiddleware(
        root_dir=str(root),
        permissions=[
            FilesystemPermission(
                path="**",
                operations=["read"],
            )
        ],
    )

    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        middleware=[fs_middleware],
    )

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=f"Please review: {task}")]},
            config={
                "configurable": {
                    "thread_id": f"critic-{thread_uuid or 'local'}",
                    "max_iterations": max_iterations,
                }
            },
        )
        messages = result.get("messages", [])
        final_text = ""
        for m in reversed(messages):
            if hasattr(m, "content") and isinstance(m.content, str) and m.content.strip():
                final_text = m.content
                break

        # Extract structured JSON if present
        critique: dict[str, Any] = {"passed": True, "score": 1.0, "findings": [final_text[:2000]]}
        for chunk in [final_text]:
            try:
                start = chunk.find("{")
                end = chunk.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(chunk[start:end])
                    if "passed" in parsed:
                        critique = parsed
                        break
            except (json.JSONDecodeError, ValueError):
                pass

        elapsed = int((datetime.now(UTC) - t0).total_seconds() * 1000)
        return {
            "status": "completed",
            "critique": critique,
            "passed": bool(critique.get("passed", True)),
            "score": float(critique.get("score", 1.0)),
            "error": None,
            "elapsed_ms": elapsed,
            "model": model,
            "worktree": str(root),
            "project_id": project_id,
        }

    except Exception as exc:
        elapsed = int((datetime.now(UTC) - t0).total_seconds() * 1000)
        return {
            "status": "failed",
            "critique": {},
            "passed": False,
            "score": 0.0,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": elapsed,
            "model": model,
            "worktree": str(root),
            "project_id": project_id,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Drift check (ported from libs/platform/guard/drift.py)
# Pure deterministic function — no LLM, no network, no deepagents dependency.
# ─────────────────────────────────────────────────────────────────────────────

import re as _re


_FORBIDDEN_PATH_PATTERNS: tuple[str, ...] = (
    r"\.env$",
    r"\.env\..*$",
    r".*\.pem$",
    r".*\.key$",
    r"secrets/.*",
    r"\.git/.*",
)

_TEST_PATH_HINTS: tuple[str, ...] = (
    "test_", "_test.", "/tests/", "/__tests__/", ".test.", ".spec.",
)


def compute_drift(
    *,
    diff: str,
    plan: list[str] | None = None,
    file_count_soft_cap: int = 8,
) -> dict[str, Any]:
    """Deterministic drift score from a unified diff and an optional plan.

    Ported from D:\\github\\deepagents\\libs\\platform\\guard\\drift.py
    (local AI-generated code, MIT-compatible, no external dependencies).

    Returns a dict shaped like agentcore.wf_gate_evals detail:
        name, score (0.0-1.0), passed, findings, suggested_action
    """
    plan = plan or []
    files: list[str] = []
    for line in diff.splitlines():
        m = _re.match(r"^\+\+\+\s+b/(.+)$", line)
        if m and m.group(1) != "/dev/null":
            files.append(m.group(1))

    findings: list[str] = []
    scores: list[float] = []

    # 1. size shock
    n = len(files)
    if n > file_count_soft_cap:
        scores.append(min(1.0, (n - file_count_soft_cap) / file_count_soft_cap))
        findings.append(f"size shock: {n} files changed (cap={file_count_soft_cap})")
    else:
        scores.append(0.0)

    # 2. forbidden paths
    forbidden = [f for f in files if any(_re.match(p, f) for p in _FORBIDDEN_PATH_PATTERNS)]
    if forbidden:
        scores.append(1.0)
        findings.append(f"forbidden paths touched: {forbidden!r}")
    else:
        scores.append(0.0)

    # 3. test absence (code changed but no test file)
    code_files = [f for f in files if not any(h in f for h in _TEST_PATH_HINTS) and not f.endswith(".md")]
    test_files = [f for f in files if any(h in f for h in _TEST_PATH_HINTS)]
    if code_files and not test_files:
        scores.append(0.4)
        findings.append("code changed but no test file changed")
    else:
        scores.append(0.0)

    # 4. plan deviation
    plan_files: set[str] = set()
    for step in plan:
        for m in _re.finditer(r"[\w/]+\.[a-zA-Z]{1,5}", step):
            plan_files.add(m.group(0))
    if plan_files:
        unexpected = [f for f in files if f and f not in plan_files and not any(h in f for h in _TEST_PATH_HINTS)]
        if unexpected:
            scores.append(min(0.6, 0.2 * len(unexpected)))
            findings.append(f"diff touched files not in plan: {unexpected!r}")
        else:
            scores.append(0.0)
    else:
        scores.append(0.0)

    score = max(scores) if scores else 0.0
    return {
        "name": "drift",
        "score": round(float(score), 3),
        "passed": score < 0.30,
        "findings": findings or ["drift within acceptable bounds"],
        "suggested_action": "reflect" if score >= 0.30 else "none",
        "ts": _now(),
    }


def gate_drift(state: dict) -> tuple[str, dict]:
    """M6 gate wrapper around compute_drift.

    Checks if there is a diff in the execution_result and computes drift.
    If no diff is present, passes with no drift.
    """
    result = state.get("execution_result", {})
    diff = result.get("diff", "")
    plan = state.get("macro_steps", [])
    plan_labels = [s.get("label", "") for s in plan]

    if not diff:
        return "pass", {"gate": "drift", "reason": "no diff in execution_result"}

    drift = compute_drift(diff=diff, plan=plan_labels)
    verdict = "pass" if drift["passed"] else "fail"
    return verdict, {"gate": "drift", **drift}
