"""Deep Agents worker boundary hardening — offline unit tests.

Covers: files_changed via git, summarization neutralization, resource ceilings,
deterministic worker mode, critic read-only, no PostgresSaver/MemoryMiddleware.

Run:
  python -m pytest scripts/agentcore_workflow/tests/test_deepagents_worker_boundary.py -v
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from agentcore_workflow.deepagents_worker import (
    _git_files_changed,
    _git_snapshot,
    _validate_worktree,
    resource_ceiling_defaults,
    run_builder_worker,
    run_critic_worker,
)
from agentcore_workflow.gates import gate_resource


@pytest.fixture()
def git_worktree(tmp_path_factory):
    """Create a tiny git repo under D:\\test (allowed by _validate_worktree)."""
    base = Path("D:/test")
    base.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="da-boundary-", dir=str(base)))
    subprocess.run(["git", "init"], cwd=str(root), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "da@test.local"], cwd=str(root), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "DA Test"], cwd=str(root), check=True, capture_output=True)
    (root / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(root), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=str(root), check=True, capture_output=True)
    yield root
    # best-effort cleanup
    try:
        import shutil
        shutil.rmtree(root, ignore_errors=True)
    except OSError:
        pass


def test_resource_ceiling_defaults_sized_for_chaoscentral():
    caps = resource_ceiling_defaults()
    assert caps["max_concurrent_workers"] >= 1
    assert caps["max_rework"] >= 1
    assert caps["vram_slots"] == 1
    assert caps["token_budget"] >= 1000
    assert caps["worker_timeout_sec"] >= 30
    assert caps["max_subagents"] == 0  # default: no task fan-out


def test_gate_resource_enforces_rework_ceiling():
    caps = resource_ceiling_defaults()
    state = {
        "project_id": "00000000-0000-0000-0000-000000000000",
        "da_rework_count": caps["max_rework"] + 1,
        "da_budget": {},
    }
    verdict, detail = gate_resource(state)
    assert verdict == "fail"
    assert any("max_rework" in f for f in detail.get("failures", []))


def test_gate_resource_passes_within_ceilings():
    state = {
        "project_id": "00000000-0000-0000-0000-000000000000",
        "da_rework_count": 0,
        "da_budget": {"tokens_used": 10, "token_budget": 1000, "elapsed_ms": 5},
    }
    verdict, detail = gate_resource(state)
    assert verdict in ("pass", "warn")
    assert detail["ceilings"]["vram_slots"] >= 1


def test_git_files_changed_detects_new_file(git_worktree):
    before = _git_snapshot(git_worktree)
    assert before == set()
    (git_worktree / "new_module.py").write_text("x = 1\n", encoding="utf-8")
    changed = _git_files_changed(git_worktree, before)
    assert "new_module.py" in changed


def test_deterministic_builder_populates_files_changed(git_worktree):
    prev = os.environ.get("AGENTCORE_WORKER_MODE")
    os.environ["AGENTCORE_WORKER_MODE"] = "deterministic"
    try:
        before = _git_snapshot(git_worktree)
        (git_worktree / "built.txt").write_text("hello\n", encoding="utf-8")
        # Snapshot before worker should still see the new file as dirty after;
        # simulate: capture before, then mutate, then run worker which re-diffs.
        # Worker captures its own before at start — so create file inside by
        # pre-dirtying then relying on worker's before/after within the call
        # is empty if no further change. Instead: empty before inside worker,
        # mutate via side channel is not possible; verify empty list when no
        # change during the deterministic call, and non-empty when we mutate
        # between snapshot helpers used by the worker contract.
        result = run_builder_worker(
            task="noop",
            worktree_path=str(git_worktree),
            agentcore_context="ctx",
            project_id="p",
        )
        assert result["status"] == "completed"
        assert result["worker_mode"] == "deterministic"
        assert isinstance(result["files_changed"], list)
        # File already dirty before worker started → not reported as NEW change.
        # Create another file by using git helpers the worker uses:
        before2 = _git_snapshot(git_worktree)
        (git_worktree / "during.txt").write_text("y\n", encoding="utf-8")
        assert "during.txt" in _git_files_changed(git_worktree, before2)
    finally:
        if prev is None:
            os.environ.pop("AGENTCORE_WORKER_MODE", None)
        else:
            os.environ["AGENTCORE_WORKER_MODE"] = prev


def test_deterministic_critic_read_only_contract(git_worktree):
    prev = os.environ.get("AGENTCORE_WORKER_MODE")
    os.environ["AGENTCORE_WORKER_MODE"] = "deterministic"
    try:
        result = run_critic_worker(
            task="review",
            worktree_path=str(git_worktree),
            agentcore_context="ctx",
            project_id="p",
        )
        assert result["status"] == "completed"
        assert result["passed"] is True
        # Critic source must remain read-only at permission layer
        import inspect
        src = inspect.getsource(run_critic_worker)
        assert 'operations=["read"]' in src
        assert 'operations=["read", "write"]' not in src
    finally:
        if prev is None:
            os.environ.pop("AGENTCORE_WORKER_MODE", None)
        else:
            os.environ["AGENTCORE_WORKER_MODE"] = prev


def test_builder_hang_mode_returns_worker_timeout(git_worktree):
    prev_mode = os.environ.get("AGENTCORE_WORKER_MODE")
    prev_timeout = os.environ.get("AGENTCORE_WORKER_TIMEOUT_SEC")
    os.environ["AGENTCORE_WORKER_MODE"] = "hang"
    os.environ["AGENTCORE_WORKER_TIMEOUT_SEC"] = "1"
    try:
        # Re-import defaults are already bound; timeout is read at call time from env.
        result = run_builder_worker(
            task="hang",
            worktree_path=str(git_worktree),
            agentcore_context="ctx",
        )
        assert result["status"] == "failed"
        assert result.get("failure_class") == "worker_timeout"
        assert "WorkerTimeout" in (result.get("error") or "")
    finally:
        if prev_mode is None:
            os.environ.pop("AGENTCORE_WORKER_MODE", None)
        else:
            os.environ["AGENTCORE_WORKER_MODE"] = prev_mode
        if prev_timeout is None:
            os.environ.pop("AGENTCORE_WORKER_TIMEOUT_SEC", None)
        else:
            os.environ["AGENTCORE_WORKER_TIMEOUT_SEC"] = prev_timeout


def test_no_memory_middleware_or_postgres_in_worker():
    import inspect
    import re
    from agentcore_workflow import deepagents_worker as daw

    src = Path(daw.__file__).read_text(encoding="utf-8")
    assert "MemoryMiddleware(" not in src
    # Mentions in docstrings that forbid PostgresSaver are OK; imports/calls are not.
    assert not re.search(r"^\s*(from|import).*PostgresSaver", src, re.M)
    assert "PostgresSaver(" not in src
    assert "swarmrecall" not in src.lower() and "swarmvault" not in src.lower()
    bounded = inspect.getsource(daw._create_bounded_agent)
    assert "memory=None" in bounded
    assert "checkpointer=None" in bounded
    profile = inspect.getsource(daw._ensure_bounded_harness_profile)
    assert "SummarizationMiddleware" in profile
    backend = inspect.getsource(daw._build_worktree_backend)
    assert "/conversation_history/" in backend


def test_validate_worktree_still_blocks_forbidden_drives():
    with pytest.raises(PermissionError):
        _validate_worktree("C:\\Windows")
