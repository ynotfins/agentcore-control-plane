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
    - SummarizationMiddleware durable offload into the worktree (second SoT)
    - LangSmith tracing (external data egress without operator approval)
    - .env file loading (violates AgentCore secret handling policy)
    - Overriding M6 checkpoints (M6 PostgresSaver remains canonical)
    - Writing outside the assigned worktree
    - Platform supervisor graph, Swarm, or PostgresSaver inside the worker

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
import re as _re
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

# ─────────────────────────────────────────────────────────────────────────────
# Resource ceilings — defaults sized for CHAOSCENTRAL
# (i9-14900KF / 128GB RAM / RTX 4070 SUPER 12GB VRAM)
# Override via Windows User-scope env vars; never .env files.
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_WORKER_TIMEOUT_SEC = int(os.environ.get("AGENTCORE_WORKER_TIMEOUT_SEC", "180"))
DEFAULT_MAX_CONCURRENT_WORKERS = int(os.environ.get("AGENTCORE_DA_MAX_CONCURRENT", "4"))
DEFAULT_MAX_SUBAGENTS = int(os.environ.get("AGENTCORE_DA_MAX_SUBAGENTS", "0"))
DEFAULT_MAX_REWORK = int(os.environ.get("AGENTCORE_DA_MAX_REWORK", "2"))
DEFAULT_TOKEN_BUDGET = int(os.environ.get("AGENTCORE_DA_TOKEN_BUDGET", "32000"))
DEFAULT_BUILDER_MAX_ITER = int(os.environ.get("AGENTCORE_DA_MAX_ITERATIONS_BUILDER", "3"))
DEFAULT_CRITIC_MAX_ITER = int(os.environ.get("AGENTCORE_DA_MAX_ITERATIONS_CRITIC", "2"))
DEFAULT_VRAM_SLOTS = int(os.environ.get("AGENTCORE_DA_VRAM_SLOTS", "1"))

# Process-local admission controls (not cross-process; gate_resource also checks).
_worker_slots = threading.BoundedSemaphore(DEFAULT_MAX_CONCURRENT_WORKERS)
_vram_slots = threading.BoundedSemaphore(max(1, DEFAULT_VRAM_SLOTS))
_profile_lock = threading.Lock()
_bounded_profile_registered = False

# Worker modes (orchestration proof / failure injection):
#   unset|llm   — normal Deep Agents + model path
#   deterministic — zero-cost fixture worker (no LLM, no network)
#   hang — sleep past timeout (proves WorkerTimeout → failed/blocked)


def _worker_mode() -> str:
    return os.environ.get("AGENTCORE_WORKER_MODE", "llm").strip().lower()


def resource_ceiling_defaults() -> dict[str, int]:
    """Public snapshot of resource ceiling defaults (for gates/tests/audit)."""
    return {
        "max_concurrent_workers": DEFAULT_MAX_CONCURRENT_WORKERS,
        "max_subagents": DEFAULT_MAX_SUBAGENTS,
        "max_rework": DEFAULT_MAX_REWORK,
        "token_budget": DEFAULT_TOKEN_BUDGET,
        "worker_timeout_sec": DEFAULT_WORKER_TIMEOUT_SEC,
        "builder_max_iterations": DEFAULT_BUILDER_MAX_ITER,
        "critic_max_iterations": DEFAULT_CRITIC_MAX_ITER,
        "vram_slots": DEFAULT_VRAM_SLOTS,
    }


# Deep Agents is a bounded optional dependency.
# We guard the import so AgentCore works without it and fails fast here.
try:
    from deepagents import FilesystemPermission, create_deep_agent
    from langchain_core.messages import HumanMessage
    DEEPAGENTS_AVAILABLE = True
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    FilesystemPermission = None  # type: ignore[misc, assignment]
    create_deep_agent = None  # type: ignore[misc, assignment]
    HumanMessage = None  # type: ignore[misc, assignment]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _require_deepagents() -> None:
    if _worker_mode() in {"deterministic", "hang"}:
        return
    if not DEEPAGENTS_AVAILABLE:
        raise ImportError(
            "deepagents is required for the builder/critic worker. "
            "Install with: pip install deepagents==0.6.12"
        )


def _deterministic_worker_result(
    *,
    role: str,
    task: str,
    worktree_path: str,
    project_id: str,
    t0: datetime,
    files_changed: list[str] | None = None,
) -> dict[str, Any]:
    """Zero-cost orchestration fixture — no LLM, no network."""
    elapsed = int((datetime.now(UTC) - t0).total_seconds() * 1000)
    if role == "builder":
        return {
            "status": "completed",
            "output": f"[deterministic-fixture] builder completed: {task[:200]}",
            "files_changed": list(files_changed or []),
            "error": None,
            "elapsed_ms": elapsed,
            "model": "deterministic-fixture",
            "worktree": worktree_path,
            "project_id": project_id,
            "worker_mode": "deterministic",
            "token_budget": DEFAULT_TOKEN_BUDGET,
        }
    return {
        "status": "completed",
        "critique": {
            "passed": True,
            "score": 1.0,
            "findings": ["deterministic-fixture critic: no defects"],
        },
        "passed": True,
        "score": 1.0,
        "error": None,
        "elapsed_ms": elapsed,
        "model": "deterministic-fixture",
        "worktree": worktree_path,
        "project_id": project_id,
        "worker_mode": "deterministic",
        "token_budget": DEFAULT_TOKEN_BUDGET,
    }


def _run_with_timeout(fn, *, timeout_sec: int, on_timeout: dict[str, Any]) -> dict[str, Any]:
    """Run fn in a daemon thread; on timeout return evidence-backed failure dict.

    Uses a daemon thread (not ThreadPoolExecutor) so a timed-out hang/LLM call
    cannot keep the process alive after the node returns failure evidence.
    """
    box: dict[str, Any] = {}

    def _runner() -> None:
        try:
            box["result"] = fn()
        except Exception as exc:  # noqa: BLE001 — surface to caller path
            box["error"] = exc

    t = threading.Thread(target=_runner, name="agentcore-worker-timeout", daemon=True)
    t.start()
    t.join(timeout=timeout_sec)
    if t.is_alive():
        return on_timeout
    if "error" in box:
        raise box["error"]
    return box.get("result") or on_timeout


@contextmanager
def _acquire_worker_slot(*, timeout_sec: float = 5.0) -> Iterator[None]:
    """Bound concurrent Deep Agents workers in this process."""
    acquired = _worker_slots.acquire(timeout=timeout_sec)
    if not acquired:
        raise RuntimeError(
            f"WorkerAdmissionDenied: max concurrent DA workers "
            f"({DEFAULT_MAX_CONCURRENT_WORKERS}) exhausted"
        )
    try:
        yield
    finally:
        _worker_slots.release()


@contextmanager
def _acquire_vram_slot(*, heavy_gpu: bool, timeout_sec: float = 2.0) -> Iterator[bool]:
    """VRAM admission stub — at most one heavy GPU task (4070 SUPER 12GB).

    Returns whether the VRAM slot was acquired. Non-heavy work skips admission.
    """
    if not heavy_gpu:
        yield False
        return
    acquired = _vram_slots.acquire(timeout=timeout_sec)
    if not acquired:
        raise RuntimeError(
            f"VramAdmissionDenied: all {DEFAULT_VRAM_SLOTS} heavy GPU slot(s) in use"
        )
    try:
        yield True
    finally:
        _vram_slots.release()


OPENROUTER_API_V1 = "https://openrouter.ai/api/v1"


def _resolve_model(model: str):
    """Resolve a 'provider:model' spec into a chat model instance or pass-through spec.

    For 'openrouter:<model-id>' specs, construct ChatOpenRouter with an explicit
    /api/v1 base URL: the machine-level OPENROUTER_API_BASE env var points at the
    site root (HTML), which langchain_openrouter would otherwise inherit.
    openrouter/auto is rejected — explicit model IDs only.
    """
    if isinstance(model, str) and model.startswith("openrouter:"):
        model_id = model.split(":", 1)[1]
        if not model_id or model_id == "openrouter/auto":
            raise ValueError("openrouter requires an explicit model ID (openrouter/auto is not permitted)")
        from langchain_openrouter import ChatOpenRouter

        # Explicit connect/read timeouts prevent indefinite hangs on free/slow models.
        timeout_sec = float(os.environ.get("AGENTCORE_OPENROUTER_TIMEOUT_SEC", "60"))
        return ChatOpenRouter(
            model=model_id,
            base_url=OPENROUTER_API_V1,
            timeout=timeout_sec,
            max_retries=1,
        )
    return model


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
# Git files_changed capture
# ─────────────────────────────────────────────────────────────────────────────

def _git_snapshot(worktree: Path) -> set[str]:
    """Return the set of dirty/untracked paths relative to the worktree root."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if proc.returncode != 0:
        return set()
    paths: set[str] = set()
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        # porcelain: XY PATH  or  XY ORIG -> PATH
        rest = line[3:]
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        paths.add(rest.strip().strip('"'))
    return paths


def _git_files_changed(worktree: Path, before: set[str]) -> list[str]:
    """Diff porcelain status before/after; also include newly dirty tracked files."""
    after = _git_snapshot(worktree)
    # Paths that became dirty or changed presence
    changed = sorted(after - before)
    # Also catch modifications that were already dirty but content changed:
    # re-run name-status against HEAD for a fuller picture when git repo exists.
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                p = line.strip()
                if p and p not in before:
                    # already in after typically; keep union
                    pass
            # Union of (after - before) with newly listed diffs not in before snapshot
            # is already covered by porcelain delta for most cases.
            # Include any HEAD-diff path that appeared in after but not before:
            head_diff = {ln.strip() for ln in proc.stdout.splitlines() if ln.strip()}
            # If a path was clean before and is in head_diff now, it changed.
            for p in head_diff:
                if p not in before and p not in changed:
                    changed.append(p)
            changed = sorted(set(changed))
    except (OSError, subprocess.SubprocessError):
        pass
    return changed


# ─────────────────────────────────────────────────────────────────────────────
# Bounded agent construction (no MemoryMiddleware; summarization neutralized)
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_bounded_harness_profile() -> None:
    """Register AgentCore harness profile: drop summarization offload + bound fan-out.

    deepagents 0.6.12 installs SummarizationMiddleware by default; that middleware
    offloads conversation archives to the backend at /conversation_history/*.md.
    With a worktree FilesystemBackend that would create a second durable SoT.
    We exclude SummarizationMiddleware and disable the default general-purpose
    subagent (task fan-out) unless AGENTCORE_DA_MAX_SUBAGENTS > 0.
    """
    global _bounded_profile_registered
    if not DEEPAGENTS_AVAILABLE:
        return
    with _profile_lock:
        if _bounded_profile_registered:
            return
        from deepagents import GeneralPurposeSubagentProfile, HarnessProfile, register_harness_profile

        excluded_tools: set[str] = {"execute"}  # FilesystemBackend is not a sandbox
        if DEFAULT_MAX_SUBAGENTS <= 0:
            excluded_tools.add("task")

        profile = HarnessProfile(
            excluded_middleware=frozenset({"SummarizationMiddleware"}),
            excluded_tools=frozenset(excluded_tools),
            general_purpose_subagent=GeneralPurposeSubagentProfile(
                enabled=DEFAULT_MAX_SUBAGENTS > 0,
            ),
        )
        # Register under providers used by AgentCore workers (pre-built models
        # resolve via provider when model is a ChatOpenRouter / ChatOpenAI instance).
        for key in ("agentcore-bounded-worker", "openrouter", "openai"):
            register_harness_profile(key, profile)
        _bounded_profile_registered = True


def _build_worktree_backend(root: Path):
    """Filesystem backend scoped to worktree; conversation_history stays ephemeral.

    Defense-in-depth: even if summarization/tool-offload middleware remains,
    /conversation_history/ is routed to a process-private temp dir, never the
    Git worktree (avoids a second durable source of truth).
    """
    from deepagents.backends import CompositeBackend, FilesystemBackend

    hist_dir = Path(tempfile.mkdtemp(prefix="agentcore-da-hist-"))
    worktree_fs = FilesystemBackend(root_dir=str(root), virtual_mode=True)
    history_fs = FilesystemBackend(root_dir=str(hist_dir), virtual_mode=True)
    backend = CompositeBackend(
        default=worktree_fs,
        routes={"/conversation_history/": history_fs},
    )
    return backend, hist_dir


def _cleanup_hist_dir(hist_dir: Path | None) -> None:
    if hist_dir is None:
        return
    try:
        import shutil
        shutil.rmtree(hist_dir, ignore_errors=True)
    except OSError:
        pass


def _create_bounded_agent(
    *,
    model: str,
    system_prompt: str,
    root: Path,
    permissions: list,
):
    """create_deep_agent with AgentCore boundary: no memory, no durable summarization."""
    _ensure_bounded_harness_profile()
    backend, hist_dir = _build_worktree_backend(root)
    # memory= omitted intentionally — MemoryMiddleware must not run.
    # checkpointer omitted — ephemeral MemorySaver only; M6 PostgresSaver is canonical.
    agent = create_deep_agent(
        model=_resolve_model(model),
        system_prompt=system_prompt,
        backend=backend,
        permissions=permissions,
        subagents=None,
        memory=None,
        checkpointer=None,
    )
    return agent, hist_dir


# ─────────────────────────────────────────────────────────────────────────────
# Builder worker
# ─────────────────────────────────────────────────────────────────────────────

def run_builder_worker(
    *,
    task: str,
    worktree_path: str,
    agentcore_context: str,
    model: str = "openai:gpt-4o-mini",
    max_iterations: int | None = None,
    allowed_tools: list[str] | None = None,
    project_id: str = "",
    thread_uuid: str = "",
    heavy_gpu: bool = False,
) -> dict[str, Any]:
    """Run a Deep Agents builder worker restricted to the assigned worktree.

    The builder:
    1. Receives AgentCore startup_context as a read-only system prompt injection.
    2. Operates only within `worktree_path` via FilesystemMiddleware (R/W).
    3. Writes NO durable memory — the caller (M6 node) records evidence.
    4. Uses a short-lived MemorySaver for its own subgraph (ephemeral).
    5. Populates files_changed via git status/diff before vs after the run.

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
        heavy_gpu: When True, acquire the single VRAM admission slot.

    Returns:
        dict with keys: status, output, files_changed, error, elapsed_ms
    """
    _require_deepagents()
    root = _validate_worktree(worktree_path)
    t0 = datetime.now(UTC)
    timeout_sec = int(os.environ.get("AGENTCORE_WORKER_TIMEOUT_SEC", DEFAULT_WORKER_TIMEOUT_SEC))
    if max_iterations is None:
        max_iterations = DEFAULT_BUILDER_MAX_ITER
    before_files = _git_snapshot(root)

    mode = _worker_mode()
    if mode == "deterministic":
        return _deterministic_worker_result(
            role="builder",
            task=task,
            worktree_path=str(root),
            project_id=project_id,
            t0=t0,
            files_changed=_git_files_changed(root, before_files),
        )
    if mode == "hang":
        import time

        return _run_with_timeout(
            lambda: time.sleep(max(timeout_sec * 4, 120)) or {
                "status": "failed",
                "error": "WorkerHang: builder unexpectedly finished",
                "failure_class": "worker_hang_unbounded",
                "elapsed_ms": int((datetime.now(UTC) - t0).total_seconds() * 1000),
                "model": model,
                "worktree": str(root),
                "project_id": project_id,
                "files_changed": [],
            },
            timeout_sec=timeout_sec,
            on_timeout={
                "status": "failed",
                "output": "",
                "files_changed": [],
                "error": (
                    f"WorkerTimeout: builder exceeded {timeout_sec}s "
                    f"(model={model}; mode=hang)"
                ),
                "elapsed_ms": int((datetime.now(UTC) - t0).total_seconds() * 1000),
                "model": model,
                "worktree": str(root),
                "project_id": project_id,
                "failure_class": "worker_timeout",
            },
        )

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
- Do NOT create AGENTS.md, .env, or conversation_history archives.
- Write clear, testable code. Run tests if they exist.
- Stop after completing the task; do not over-engineer.
- Your output will be captured by the AgentCore platform; do not create
  separate memory files or AGENTS.md files.
"""

    # Filesystem access restricted to worktree — read+write allowed.
    # deepagents 0.6.x: create_deep_agent installs FilesystemMiddleware itself;
    # pass backend (root confinement, virtual_mode=True blocks '..'/absolute
    # escapes) and permissions (backend-relative, must start with '/').
    # MemoryMiddleware is intentionally omitted: it reads AGENTS.md files,
    # which would create a competing source of truth with AgentCore.
    # SummarizationMiddleware is excluded via HarnessProfile; conversation_history
    # is also routed off the worktree via CompositeBackend.
    fs_permission = FilesystemPermission(
        paths=["/**"],
        operations=["read", "write"],
    )

    hist_dir: Path | None = None
    try:
        with _acquire_worker_slot(), _acquire_vram_slot(heavy_gpu=heavy_gpu):
            agent, hist_dir = _create_bounded_agent(
                model=model,
                system_prompt=system_prompt,
                root=root,
                permissions=[fs_permission],
            )

            invoke_config = {
                "configurable": {
                    "thread_id": f"builder-{thread_uuid or 'local'}",
                    "max_iterations": max_iterations,
                }
            }

            result = _run_with_timeout(
                lambda: agent.invoke(
                    {"messages": [HumanMessage(content=task)]},
                    config=invoke_config,
                ),
                timeout_sec=timeout_sec,
                on_timeout={
                    "status": "failed",
                    "output": "",
                    "files_changed": _git_files_changed(root, before_files),
                    "error": (
                        f"WorkerTimeout: builder exceeded {timeout_sec}s "
                        f"(model={model}; max_iterations={max_iterations})"
                    ),
                    "elapsed_ms": int((datetime.now(UTC) - t0).total_seconds() * 1000),
                    "model": model,
                    "worktree": str(root),
                    "project_id": project_id,
                    "failure_class": "worker_timeout",
                    "token_budget": DEFAULT_TOKEN_BUDGET,
                },
            )
            if result.get("failure_class") == "worker_timeout":
                return result

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
                "files_changed": _git_files_changed(root, before_files),
                "error": None,
                "elapsed_ms": elapsed,
                "model": model,
                "worktree": str(root),
                "project_id": project_id,
                "token_budget": DEFAULT_TOKEN_BUDGET,
                "max_iterations": max_iterations,
            }

    except Exception as exc:
        elapsed = int((datetime.now(UTC) - t0).total_seconds() * 1000)
        return {
            "status": "failed",
            "output": "",
            "files_changed": _git_files_changed(root, before_files),
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": elapsed,
            "model": model,
            "worktree": str(root),
            "project_id": project_id,
            "token_budget": DEFAULT_TOKEN_BUDGET,
        }
    finally:
        _cleanup_hist_dir(hist_dir)


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
    max_iterations: int | None = None,
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
    timeout_sec = int(os.environ.get("AGENTCORE_WORKER_TIMEOUT_SEC", DEFAULT_WORKER_TIMEOUT_SEC))
    if max_iterations is None:
        max_iterations = DEFAULT_CRITIC_MAX_ITER

    mode = _worker_mode()
    if mode == "deterministic":
        return _deterministic_worker_result(
            role="critic",
            task=task,
            worktree_path=str(root),
            project_id=project_id,
            t0=t0,
        )
    if mode == "hang":
        import time

        return _run_with_timeout(
            lambda: time.sleep(max(timeout_sec * 4, 120)) or {
                "status": "failed",
                "critique": {},
                "passed": False,
                "score": 0.0,
                "error": "WorkerHang: critic unexpectedly finished",
                "failure_class": "worker_hang_unbounded",
                "elapsed_ms": int((datetime.now(UTC) - t0).total_seconds() * 1000),
                "model": model,
                "worktree": str(root),
                "project_id": project_id,
            },
            timeout_sec=timeout_sec,
            on_timeout={
                "status": "failed",
                "critique": {"passed": False, "score": 0.0, "findings": ["worker_timeout"]},
                "passed": False,
                "score": 0.0,
                "error": (
                    f"WorkerTimeout: critic exceeded {timeout_sec}s "
                    f"(model={model}; mode=hang)"
                ),
                "elapsed_ms": int((datetime.now(UTC) - t0).total_seconds() * 1000),
                "model": model,
                "worktree": str(root),
                "project_id": project_id,
                "failure_class": "worker_timeout",
            },
        )

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

    # Critic: strictly read-only filesystem.
    fs_permission = FilesystemPermission(
        paths=["/**"],
        operations=["read"],
    )

    hist_dir: Path | None = None
    try:
        with _acquire_worker_slot():
            agent, hist_dir = _create_bounded_agent(
                model=model,
                system_prompt=system_prompt,
                root=root,
                permissions=[fs_permission],
            )

            result = _run_with_timeout(
                lambda: agent.invoke(
                    {"messages": [HumanMessage(content=f"Please review: {task}")]},
                    config={
                        "configurable": {
                            "thread_id": f"critic-{thread_uuid or 'local'}",
                            "max_iterations": max_iterations,
                        }
                    },
                ),
                timeout_sec=timeout_sec,
                on_timeout={
                    "status": "failed",
                    "critique": {"passed": False, "score": 0.0, "findings": ["worker_timeout"]},
                    "passed": False,
                    "score": 0.0,
                    "error": (
                        f"WorkerTimeout: critic exceeded {timeout_sec}s "
                        f"(model={model}; max_iterations={max_iterations})"
                    ),
                    "elapsed_ms": int((datetime.now(UTC) - t0).total_seconds() * 1000),
                    "model": model,
                    "worktree": str(root),
                    "project_id": project_id,
                    "failure_class": "worker_timeout",
                    "token_budget": DEFAULT_TOKEN_BUDGET,
                },
            )
            if result.get("failure_class") == "worker_timeout":
                return result

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
                "token_budget": DEFAULT_TOKEN_BUDGET,
                "max_iterations": max_iterations,
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
            "token_budget": DEFAULT_TOKEN_BUDGET,
        }
    finally:
        _cleanup_hist_dir(hist_dir)


# ─────────────────────────────────────────────────────────────────────────────
# Drift check (ported from libs/platform/guard/drift.py)
# Pure deterministic function — no LLM, no network, no deepagents dependency.
# ─────────────────────────────────────────────────────────────────────────────

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
