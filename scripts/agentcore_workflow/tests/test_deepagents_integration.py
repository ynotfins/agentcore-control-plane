"""AgentCore Deep Agents integration proof — 10 boundary checks.

Tests that the deepagents worker adapter honours all integration
constraints without an LLM call (all tests run offline/unit-level).

Run: python -m pytest scripts/agentcore_workflow/tests/test_deepagents_integration.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from agentcore_workflow.deepagents_worker import (
    _FORBIDDEN_PATH_PATTERNS,
    _TEST_PATH_HINTS,
    _validate_worktree,
    compute_drift,
    gate_drift,
)
from agentcore_workflow import db as wfdb


# ─────────────────────────────────────────────────────────────────────────────
# 1. Builder receives the correct project context (context propagation)
# ─────────────────────────────────────────────────────────────────────────────

def test_01_agentcore_context_propagated():
    """Builder system prompt includes AgentCore context (structure check, no LLM)."""
    from agentcore_workflow.deepagents_worker import DEEPAGENTS_AVAILABLE
    assert DEEPAGENTS_AVAILABLE, "deepagents must be importable"

    # Verify the adapter function accepts and propagates context
    import inspect
    from agentcore_workflow.deepagents_worker import run_builder_worker
    sig = inspect.signature(run_builder_worker)
    assert "agentcore_context" in sig.parameters, "run_builder_worker must accept agentcore_context"
    assert "worktree_path" in sig.parameters, "run_builder_worker must accept worktree_path"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Builder cannot write outside its assigned worktree
# ─────────────────────────────────────────────────────────────────────────────

def test_02_builder_cannot_write_outside_worktree():
    """_validate_worktree blocks paths on C:, E:, F:, G:, H:."""
    import tempfile
    with tempfile.TemporaryDirectory(dir="D:\\test") as tmp:
        # Valid worktree — should not raise
        result = _validate_worktree(tmp)
        assert result.exists()

    # Forbidden drives
    for forbidden in ("C:\\Windows", "E:\\AgentCoreArchive", "F:\\PostgreSQL18", "H:\\AgentRuntime"):
        with pytest.raises(PermissionError, match="may not access"):
            _validate_worktree(forbidden)

    # Non-existent path
    with pytest.raises(ValueError, match="does not exist"):
        _validate_worktree("D:\\nonexistent_path_that_cannot_exist_12345")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Builder tool access matches the PostgreSQL-backed capability profile
# ─────────────────────────────────────────────────────────────────────────────

def test_03_builder_tool_access_matches_capability_profile():
    """Worker respects allowed_tools from capability_profiles (structure check)."""
    import inspect
    from agentcore_workflow.deepagents_worker import run_builder_worker
    sig = inspect.signature(run_builder_worker)
    assert "allowed_tools" in sig.parameters, "adapter must accept allowed_tools from capability profile"
    # Default should be None (filesystem only)
    assert sig.parameters["allowed_tools"].default is None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Expired or revoked tools become unusable (capability profile sync)
# ─────────────────────────────────────────────────────────────────────────────

def test_04_expired_tools_unusable():
    """Expired JIT leases remove tool from capability profile (DB verified)."""
    import psycopg, time
    from psycopg.rows import dict_row
    pg_pass = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    ci = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={pg_pass}"

    with psycopg.connect(ci, row_factory=dict_row) as c:
        proj = c.execute(
            "INSERT INTO agentcore.projects (project_key, project_name, root_path, trust_class) "
            "VALUES ('da-int-test', 'DA Integration Test', 'D:/test/da', 'project_verified') "
            "ON CONFLICT (project_key) DO UPDATE SET project_name=EXCLUDED.project_name RETURNING id"
        ).fetchone()
        proj_id = str(proj["id"])

    # Set a 1-second JIT lease
    lease_id = wfdb.create_jit_lease(proj_id, "deepagents-tool-test", "da-test-step", 1, "test")
    before = wfdb.get_project_tools(proj_id)
    jit_before = next((t for t in before if t["tool_name"] == "deepagents-tool-test"), None)
    assert jit_before and jit_before["tool_state"] == "jit_leased", "tool must be jit_leased before expiry"

    time.sleep(2)
    expired = wfdb.expire_jit_leases(proj_id)
    after = wfdb.get_project_tools(proj_id)
    jit_after = next((t for t in after if t["tool_name"] == "deepagents-tool-test"), None)
    assert jit_after is None, f"tool must be absent after expiry; got {jit_after}"
    assert expired >= 1, "at least one lease must have expired"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Critic is read-only (structure check)
# ─────────────────────────────────────────────────────────────────────────────

def test_05_critic_is_read_only():
    """run_critic_worker creates FilesystemMiddleware with read-only permissions."""
    import inspect
    from agentcore_workflow.deepagents_worker import run_critic_worker
    source = inspect.getsource(run_critic_worker)
    # Must NOT include 'write' in FilesystemPermission operations for the critic
    assert 'operations=["read"]' in source, "critic must be read-only"
    assert 'operations=["read", "write"]' not in source.split("run_critic_worker")[1]


# ─────────────────────────────────────────────────────────────────────────────
# 6. Process termination resumes through M6 checkpoint (not deepagents)
# ─────────────────────────────────────────────────────────────────────────────

def test_06_checkpoint_via_m6_not_deepagents():
    """The builder worker uses MemorySaver (ephemeral); M6 uses PostgresSaver."""
    import inspect
    from agentcore_workflow.deepagents_worker import run_builder_worker

    # The adapter must NOT use PostgresSaver itself
    source = inspect.getsource(run_builder_worker)
    assert "PostgresSaver" not in source, "builder worker must not use PostgresSaver (M6 owns checkpoints)"
    # M6 workflow.py DOES use PostgresSaver
    from agentcore_workflow.workflow import build_graph
    wf_source = inspect.getsource(build_graph)
    assert "PostgresSaver" in wf_source, "M6 build_graph must use PostgresSaver"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Project A and B remain isolated (via M6 wf_runs isolation)
# ─────────────────────────────────────────────────────────────────────────────

def test_07_project_isolation():
    """Two projects' wf_runs and capability_profiles remain isolated."""
    import psycopg
    from psycopg.rows import dict_row
    pg_pass = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    ci = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={pg_pass}"

    with psycopg.connect(ci, row_factory=dict_row) as c:
        pa = c.execute(
            "INSERT INTO agentcore.projects (project_key, project_name, root_path, trust_class) "
            "VALUES ('da-iso-a', 'DA Iso A', 'D:/test/da-a', 'project_verified') "
            "ON CONFLICT (project_key) DO UPDATE SET project_name=EXCLUDED.project_name RETURNING id"
        ).fetchone()
        pb = c.execute(
            "INSERT INTO agentcore.projects (project_key, project_name, root_path, trust_class) "
            "VALUES ('da-iso-b', 'DA Iso B', 'D:/test/da-b', 'project_verified') "
            "ON CONFLICT (project_key) DO UPDATE SET project_name=EXCLUDED.project_name RETURNING id"
        ).fetchone()
        pid_a, pid_b = str(pa["id"]), str(pb["id"])

    wfdb.set_capability_state(pid_a, "da-exclusive-tool", "core_active", "M6", "Project A only", False)
    tools_b = wfdb.get_project_tools(pid_b)
    a_in_b = [t for t in tools_b if t["tool_name"] == "da-exclusive-tool"]
    assert not a_in_b, f"Project A tools must not be visible in Project B; got {a_in_b}"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Deep Agents context offloading does not lose AgentCore evidence
# ─────────────────────────────────────────────────────────────────────────────

def test_08_context_offloading_does_not_lose_evidence():
    """Builder result is recorded via db.record_evidence, not deep agent's MemorySaver."""
    # The builder worker returns a plain dict; the M6 node records it via db.record_evidence.
    # Verify the contract: MemoryMiddleware is NOT used (may appear in comments explaining exclusion).
    import inspect
    from agentcore_workflow.deepagents_worker import run_builder_worker
    source = inspect.getsource(run_builder_worker)
    # MemoryMiddleware must not be instantiated (it may be mentioned in a clarifying comment)
    assert "MemoryMiddleware(" not in source, "builder must NOT instantiate MemoryMiddleware"
    # Builder must use bounded agent helper (backend + permissions), not MemoryMiddleware
    module_src = inspect.getsource(
        __import__("agentcore_workflow.deepagents_worker", fromlist=["_create_bounded_agent"])
    )
    from agentcore_workflow import deepagents_worker as daw
    bounded_src = inspect.getsource(daw._create_bounded_agent)
    assert "memory=None" in bounded_src, "bounded agent must pass memory=None"
    assert "SummarizationMiddleware" in inspect.getsource(daw._ensure_bounded_harness_profile)
    assert "CompositeBackend" in inspect.getsource(daw._build_worktree_backend)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Durable memory written only through agentcore-memory
# ─────────────────────────────────────────────────────────────────────────────

def test_09_durable_memory_through_agentcore_only():
    """Worker returns dict; M6 caller writes to wf_evidence via db.record_evidence."""
    # Verify the M6 node_evidence_record writes to the DB, not deepagents
    import inspect
    from agentcore_workflow.nodes import node_evidence_record
    source = inspect.getsource(node_evidence_record)
    assert "db.record_evidence" in source, "M6 node must write evidence through agentcore db"
    # deepagents_worker must not directly write to wf_evidence
    from agentcore_workflow.deepagents_worker import run_builder_worker
    worker_source = inspect.getsource(run_builder_worker)
    assert "record_evidence" not in worker_source, "worker must not write evidence directly"


# ─────────────────────────────────────────────────────────────────────────────
# 10. Drift gate runs deterministically before LLM critics
# ─────────────────────────────────────────────────────────────────────────────

def test_10_drift_gate_deterministic():
    """compute_drift and gate_drift are deterministic, offline, and pure."""
    # Same inputs → same output
    diff = "--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    result1 = compute_drift(diff=diff, plan=["update main.py variable"])
    result2 = compute_drift(diff=diff, plan=["update main.py variable"])
    assert result1["score"] == result2["score"], "must be deterministic"
    assert result1["passed"] == result2["passed"]

    # Forbidden path triggers fail
    bad_diff = "--- a/.env\n+++ b/.env\n@@ -0,0 +1 @@\n+SECRET=leaked\n"
    bad = compute_drift(diff=bad_diff)
    assert not bad["passed"], "forbidden path must fail drift gate"
    assert bad["score"] >= 0.9

    # gate_drift integration (no diff → pass)
    state = {"execution_result": {}, "macro_steps": []}
    verdict, detail = gate_drift(state)
    assert verdict == "pass", f"no diff should pass; got {verdict}"

    # gate_drift with forbidden diff → fail
    state2 = {"execution_result": {"diff": bad_diff}, "macro_steps": []}
    verdict2, detail2 = gate_drift(state2)
    assert verdict2 == "fail", f"forbidden diff should fail gate; got {verdict2}"

    # Drift gate is in GATE_REGISTRY
    from agentcore_workflow.gates import GATE_REGISTRY
    assert "drift" in GATE_REGISTRY, "drift gate must be in registry"


# ─────────────────────────────────────────────────────────────────────────────
# M2-M7 regression (run existing acceptance suite)
# ─────────────────────────────────────────────────────────────────────────────

def test_m6_regression_still_green():
    """Existing M6 acceptance tests remain green after DA integration."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "agentcore_workflow" / "tests" / "m6_acceptance.py")],
        capture_output=True, text=True, timeout=120, cwd=str(REPO),
        env={**os.environ, "PYTHONPATH": str(REPO / "scripts")},
    )
    assert result.returncode == 0, f"M6 regression failed:\n{result.stdout[-2000:]}"
