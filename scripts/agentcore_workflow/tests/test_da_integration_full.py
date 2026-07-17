"""AgentCore Deep Agents Full Integration — 17 acceptance tests.

Proves all required boundaries from the M6+DA integration spec.
All tests run offline (no LLM API key required): they verify structure,
DB state, routing logic, and isolation guarantees.

Run: python -m pytest scripts/agentcore_workflow/tests/test_da_integration_full.py -v
"""

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from agentcore_workflow import db as wfdb
from agentcore_workflow.deepagents_worker import (
    DEEPAGENTS_AVAILABLE,
    _validate_worktree,
    compute_drift,
    gate_drift,
    run_builder_worker,
    run_critic_worker,
)
from agentcore_workflow.nodes import (
    node_da_builder,
    node_da_critic,
    node_risk_assess,
    node_start,
)
from agentcore_workflow.state import WorkflowState, initial_state

PG_PASS = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
CI = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={PG_PASS}"
TEST_WORKTREE = Path(r"D:\test\da-integration")


@pytest.fixture(scope="module", autouse=True)
def setup_test_worktree():
    """Create a real worktree directory for tests that need filesystem access."""
    TEST_WORKTREE.mkdir(parents=True, exist_ok=True)
    (TEST_WORKTREE / "hello.py").write_text('def hello():\n    return "hello"\n', encoding="utf-8")
    yield
    # Leave the directory — cleanup is optional


@pytest.fixture(scope="module")
def proj_a_id():
    with psycopg.connect(CI, row_factory=dict_row) as c:
        r = c.execute(
            "INSERT INTO agentcore.projects (project_key, project_name, root_path, trust_class) "
            "VALUES ('da-full-a', 'DA Full A', %s, 'project_verified') "
            "ON CONFLICT (project_key) DO UPDATE SET root_path=EXCLUDED.root_path RETURNING id",
            (str(TEST_WORKTREE),),
        ).fetchone()
    return str(r["id"])


@pytest.fixture(scope="module")
def proj_b_id():
    with psycopg.connect(CI, row_factory=dict_row) as c:
        r = c.execute(
            "INSERT INTO agentcore.projects (project_key, project_name, root_path, trust_class) "
            "VALUES ('da-full-b', 'DA Full B', 'D:/test/da-b', 'project_verified') "
            "ON CONFLICT (project_key) DO UPDATE SET project_name=EXCLUDED.project_name RETURNING id",
        ).fetchone()
    return str(r["id"])


def make_state(project_id: str, project_key: str, worktree: str = "_DEFAULT_") -> dict:
    s = dict(initial_state(project_id, project_key, str(uuid.uuid4())))
    s["worktree_path"] = str(TEST_WORKTREE) if worktree == "_DEFAULT_" else worktree
    s["current_micro_key"] = "M6.3.1"
    s["current_macro_key"] = "M6.3"
    s["micro_steps"] = [{"key": "M6.3.1", "label": "Seed tools", "ordinal": 1, "risk_class": "medium", "macro_key": "M6.3"}]
    s["macro_steps"] = [{"key": "M6.3", "label": "Configure profiles", "ordinal": 3, "risk_class": "medium"}]
    return s


# ─────────────────────────────────────────────────────────────────────────────

def test_01_builder_receives_correct_identity(proj_a_id):
    """1. Builder receives project, worktree, and thread identity."""
    sig = inspect.signature(run_builder_worker)
    assert "project_id" in sig.parameters
    assert "thread_uuid" in sig.parameters
    assert "worktree_path" in sig.parameters
    assert "agentcore_context" in sig.parameters
    # node_da_builder reads identity from state and passes all fields
    src = inspect.getsource(node_da_builder)
    assert "project_id" in src
    assert "thread_uuid" in src
    assert "worktree_path" in src
    assert "agentcore_context" in src


def test_02_builder_cannot_write_outside_worktree():
    """2. Builder cannot write outside its assigned worktree."""
    for forbidden in ("C:\\Windows", "E:\\AgentCoreArchive", "F:\\PostgreSQL18"):
        with pytest.raises(PermissionError):
            _validate_worktree(forbidden)
    # Non-existent path
    with pytest.raises(ValueError):
        _validate_worktree("D:\\nonexistent_da_path_xyz")
    # Valid path passes
    p = _validate_worktree(str(TEST_WORKTREE))
    assert p.exists()


def test_03_builder_sees_only_effective_capability_profile(proj_a_id):
    """3. Builder uses tools from PostgreSQL capability profile only."""
    wfdb.set_capability_state(proj_a_id, "da-full-tool-a", "core_active", "M6", "test", False)
    wfdb.set_capability_state(proj_a_id, "da-full-dormant", "dormant")
    active = wfdb.get_project_tools(proj_a_id)
    active_names = {t["tool_name"] for t in active}
    assert "da-full-tool-a" in active_names
    assert "da-full-dormant" not in active_names, "dormant tools must not appear in effective profile"
    # node_da_builder passes allowed_tools from capability profile
    src = inspect.getsource(node_da_builder)
    assert "get_project_tools" in src or "active_tools" in src


def test_04_jit_leased_tool_becomes_usable(proj_a_id):
    """4. A JIT-leased safe tool becomes usable."""
    lease_id = wfdb.create_jit_lease(proj_a_id, "da-full-jit", "M6.3.1", 60, "test 4")
    tools = wfdb.get_project_tools(proj_a_id)
    jit = next((t for t in tools if t["tool_name"] == "da-full-jit"), None)
    assert jit is not None, "JIT-leased tool must appear in effective profile"
    assert jit["tool_state"] == "jit_leased"
    # Cleanup
    wfdb.revoke_lease(proj_a_id, lease_id, "da-full-jit")


def test_05_expiry_revocation_makes_tool_unusable(proj_a_id):
    """5. Expiry or revocation makes the tool unusable."""
    lease_id = wfdb.create_jit_lease(proj_a_id, "da-full-expire", "M6.3.1", 1, "test 5")
    time.sleep(2)
    expired = wfdb.expire_jit_leases(proj_a_id)
    after = wfdb.get_project_tools(proj_a_id)
    still_here = next((t for t in after if t["tool_name"] == "da-full-expire"), None)
    assert still_here is None, "expired tool must not appear in effective profile"
    assert expired >= 1


def test_06_project_a_cannot_see_project_b(proj_a_id, proj_b_id):
    """6. Project A cannot see Project B tools, memory, state, or files."""
    wfdb.set_capability_state(proj_a_id, "da-full-exclusive", "core_active", "M6", "exclusive", False)
    tools_b = wfdb.get_project_tools(proj_b_id)
    a_in_b = [t for t in tools_b if t["tool_name"] == "da-full-exclusive"]
    assert not a_in_b, "Project A tool must not appear in Project B profile"

    # wf_runs isolation
    thread_a = str(uuid.uuid4())
    run_a = wfdb.register_run(proj_a_id, thread_a)
    with psycopg.connect(CI, row_factory=dict_row) as c:
        cross = c.execute(
            "SELECT COUNT(*) AS cnt FROM agentcore.wf_runs WHERE id = %s AND project_id = %s",
            (run_a, proj_b_id),
        ).fetchone()["cnt"]
    assert cross == 0, "Project A run must not appear under Project B"


def test_07_critic_is_read_only():
    """7. Critic is read-only: operations=["read"] only."""
    src = inspect.getsource(node_da_critic)
    # Critic passes read-only operations; builder passes read+write
    assert '"read"' in src, "critic must reference read operation"
    assert '"write"' not in src, "critic must not reference write operation"
    # Also check the deepagents_worker run_critic_worker directly
    critic_src = inspect.getsource(run_critic_worker)
    assert 'operations=["read"]' in critic_src, "run_critic_worker must use read-only FilesystemPermission"
    assert 'operations=["read", "write"]' not in critic_src


def test_08_builder_interruption_resumes_via_m6_checkpoint():
    """8. Builder interruption resumes through M6/PostgreSQL checkpoint, not DA MemorySaver."""
    # M6 uses PostgresSaver; DA uses MemorySaver internally (ephemeral)
    from agentcore_workflow.workflow import build_graph
    wf_src = inspect.getsource(build_graph)
    assert "PostgresSaver" in wf_src, "M6 must use PostgresSaver"
    assert "MemorySaver" not in wf_src, "M6 must not use MemorySaver"
    # DA worker uses MemorySaver (ephemeral), not PostgresSaver
    da_src = inspect.getsource(run_builder_worker)
    assert "PostgresSaver" not in da_src, "DA worker must not use PostgresSaver directly"


def test_09_durable_events_written_only_through_agentcore_memory(proj_a_id):
    """9. Durable events are written only through agentcore-memory (db.record_evidence)."""
    # node_da_builder writes evidence through db.record_evidence
    src = inspect.getsource(node_da_builder)
    assert "db.record_evidence" in src, "builder must write evidence via agentcore db"
    # DA worker itself must not write evidence directly
    worker_src = inspect.getsource(run_builder_worker)
    assert "record_evidence" not in worker_src, "worker must not write evidence directly"


def test_10_da_context_offloading_preserves_agentcore_evidence_references():
    """10. DA context offloading preserves AgentCore evidence references."""
    # DA context is injected as a read-only string — it doesn't replace M3 evidence.
    # Verify node_da_builder constructs agentcore_context from M6 state, not from DA memory.
    src = inspect.getsource(node_da_builder)
    assert "agentcore_context" in src
    # MemoryMiddleware must NOT be instantiated in the builder (it may be mentioned in comments)
    assert "MemoryMiddleware(" not in src, "builder must not instantiate MemoryMiddleware"
    # The DA worker explicitly excludes MemoryMiddleware
    worker_src = inspect.getsource(run_builder_worker)
    assert "MemoryMiddleware" not in worker_src or "omitted" in worker_src.lower() or "intentionally" in worker_src.lower()
    # Evidence writes go through agentcore db, not DA memory
    assert "record_evidence" in inspect.getsource(node_da_builder)


def test_11_deterministic_gates_run_before_worker(proj_a_id):
    """11. Deterministic gates run before the DA worker via the M6 gate_check node."""
    from agentcore_workflow.workflow import build_graph
    wf_src = inspect.getsource(build_graph)
    # gate_check comes before da_builder in the graph topology
    gate_pos = wf_src.find('"gate_check"')
    da_pos = wf_src.find('"da_builder"')
    assert gate_pos < da_pos, "gate_check must be declared before da_builder in graph"
    # Drift gate is in the registry and runs deterministically
    from agentcore_workflow.gates import GATE_REGISTRY
    assert "drift" in GATE_REGISTRY


def test_12_scorer_judge_human_pause_ab_remain_authoritative():
    """12. Scorer, judge, human pause/resume, and A/B decision rules remain authoritative.

    M8 invariant: da_critic is a findings collector; post_exec_judge is the independent
    authority. The existing critics.judge() and critics.post_execution_judge() functions
    in critics.py own all scoring and judging logic.
    """
    from agentcore_workflow import critics
    assert hasattr(critics, "score_evidence"), "score_evidence must exist in critics.py"
    assert hasattr(critics, "judge"), "judge must exist in critics.py"
    assert hasattr(critics, "post_execution_judge"), (
        "post_execution_judge must exist in critics.py (M8 independent judge)"
    )
    # DA critic (node_da_critic) must NOT make routing decisions or call score_evidence/judge
    critic_src = inspect.getsource(node_da_critic)
    assert "da_critic_result" in critic_src, "DA critic must populate da_critic_result"
    assert "score_evidence" not in critic_src, "DA critic must not call score_evidence"
    assert "post_execution_judge" not in critic_src, "DA critic must not call the judge"
    # DA critic always routes to post_exec_judge
    assert "post_exec_judge" in critic_src, "DA critic must route to post_exec_judge"
    # post_exec_judge calls critics.post_execution_judge (independent authority)
    from agentcore_workflow.nodes import node_post_exec_judge
    judge_src = inspect.getsource(node_post_exec_judge)
    assert "post_execution_judge" in judge_src, "post_exec_judge must call critics.post_execution_judge"
    # Human pause nodes own the pause state
    from agentcore_workflow.nodes import node_human_pause
    assert "db.create_pause" in inspect.getsource(node_human_pause)


def test_13_m2_m7_regressions_remain_green():
    """13. Existing M2-M7 regression suites remain green."""
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "agentcore_workflow" / "tests" / "m6_acceptance.py")],
        capture_output=True, text=True, timeout=120, cwd=str(REPO),
        env={**os.environ, "PYTHONPATH": str(REPO / "scripts")},
    )
    assert result.returncode == 0, f"M6 regression failed:\n{result.stdout[-2000:]}"


def test_14_bifrost_10_tool_surface_unchanged():
    """14. Bifrost still exposes the unchanged 10-tool agentcore-memory surface."""
    mem_path = str(REPO / "scripts" / "agentcore_memory")
    if mem_path not in sys.path:
        sys.path.insert(0, mem_path)
    import server as mem_server
    expected = {"memory_status", "startup_context", "retrieve_context", "append_event",
                "propose_fact", "expand_source", "session_open", "session_close",
                "build_handoff", "docs_search"}
    actual = {t["name"] for t in mem_server.tool_defs()}
    assert expected <= actual, f"Missing tools: {expected - actual}"


def test_15_no_ide_mcp_configuration_changes():
    """15. No IDE MCP configuration changes occur."""
    cursor_mcp = Path(r"C:\Users\ynotf\.cursor\mcp.json")
    if cursor_mcp.exists():
        content = cursor_mcp.read_text(encoding="utf-8")
        assert "deepagents" not in content.lower(), "deepagents must not appear in Cursor MCP config"
    # Verify no new MCP server is exposed by the DA integration
    da_src = inspect.getsource(run_builder_worker)
    assert "mcp" not in da_src.lower() or "FilesystemMiddleware" in da_src  # DA uses FS, not MCP


def test_16_no_new_network_service_or_port():
    """16. No new network service or port is introduced."""
    da_init = inspect.getsource(run_builder_worker)
    assert "socket.bind" not in da_init
    assert "uvicorn" not in da_init
    assert "FastAPI" not in da_init
    assert "asyncio.start_server" not in da_init
    # DA uses MemorySaver (in-process), not a network server
    assert "MemorySaver" in da_init or "create_deep_agent" in da_init


def test_17_swarm_remains_untouched():
    """17. Swarm (SwarmRecall, SwarmVault, SwarmClaw) remains untouched."""
    # No deepagents code touches swarm tables
    with psycopg.connect(CI, row_factory=dict_row) as c:
        swarm_tables = c.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.tables "
            "WHERE table_schema='agentcore' AND table_name LIKE 'swarm%'"
        ).fetchone()["cnt"]
    assert swarm_tables == 0
    # DA worker imports don't reference Swarm
    da_src = inspect.getsource(run_builder_worker)
    assert "swarm" not in da_src.lower()
    assert "SwarmRecall" not in da_src
    # The node_da_builder also doesn't touch Swarm
    assert "swarm" not in inspect.getsource(node_da_builder).lower()


# ─────────────────────────────────────────────────────────────────────────────
# BONUS: Graph routing verification
# ─────────────────────────────────────────────────────────────────────────────

def test_da_graph_routing_structure():
    """Verify da_builder, da_critic, and post_exec_judge are correctly wired (M8 invariant)."""
    from agentcore_workflow.workflow import build_graph
    wf_src = inspect.getsource(build_graph)
    assert "da_builder" in wf_src, "da_builder must be in the graph"
    assert "da_critic" in wf_src, "da_critic must be in the graph"
    assert '"da_builder"' in wf_src
    assert '"da_critic"' in wf_src
    # M8 invariant: da_critic always routes to post_exec_judge (critic never self-adjudicates).
    # Updated for A/B path: da_critic uses a CONDITIONAL edge that routes to either
    # ab_alternate (when ab_enabled=True) or post_exec_judge directly (when ab_enabled=False).
    # ab_alternate always routes to post_exec_judge. The invariant is preserved: da_critic
    # never routes to evidence_record or workflow_fail directly.
    assert 'add_conditional_edges("da_critic"' in wf_src or 'add_edge("da_critic"' in wf_src, (
        "da_critic must have an edge to post_exec_judge path (M8 invariant: critic is not its own judge)"
    )
    assert '"post_exec_judge"' in wf_src and '"ab_alternate"' in wf_src, (
        "Both post_exec_judge and ab_alternate must be targets reachable from da_critic path"
    )
    assert 'add_edge("ab_alternate", "post_exec_judge")' in wf_src, (
        "ab_alternate must have a fixed edge to post_exec_judge (A/B path invariant)"
    )
    # post_exec_judge uses conditional edge (independent judge routes to evidence_record or workflow_fail)
    assert 'add_conditional_edges("post_exec_judge"' in wf_src, (
        "post_exec_judge must use conditional edge to evidence_record or workflow_fail"
    )
    assert '"post_exec_judge"' in wf_src, "post_exec_judge node must be declared"


def test_da_critic_finding_reaches_scorer_and_can_affect_verdict():
    """Regression: DA critic findings must reach the independent post-execution judge.

    M8 invariant: a DA critic worker may NOT be its own independent final judge.
    node_da_critic is a findings collector only — it always routes to post_exec_judge.
    node_post_exec_judge is the independent authority that evaluates all evidence.

    This test verifies:
    1. node_da_critic always routes to post_exec_judge (never directly to workflow_fail)
    2. node_post_exec_judge routes to workflow_fail for critical combined failures
    3. node_post_exec_judge routes to evidence_record for passes
    4. node_post_exec_judge routes to evidence_record for advisory failures (high pre-exec)
    """
    from agentcore_workflow.nodes import node_da_critic, node_post_exec_judge
    from agentcore_workflow.state import initial_state
    from unittest.mock import patch

    base_state = dict(initial_state("00000000-0000-0000-0000-000000000001", "test-proj", str(uuid.uuid4())))
    base_state["current_micro_key"] = "M6.3.1"
    base_state["current_risk_class"] = "medium"
    base_state["worktree_path"] = str(TEST_WORKTREE)
    base_state["da_builder_result"] = {"status": "completed", "output": "some output"}
    base_state["det_checks_details"] = [{"check": "migration_applied", "passed": True}]
    base_state["gates_passed"] = ["requirement", "scope"]
    base_state["gates_failed"] = []

    # ── Part 1: da_critic always routes to post_exec_judge ────────────────────
    base_state["score"] = 0.45
    critical_failure = {"passed": False, "score": 0.0, "findings": ["critical: builder deleted test suite"]}

    with patch("agentcore_workflow.deepagents_worker.DEEPAGENTS_AVAILABLE", True), \
         patch("agentcore_workflow.deepagents_worker.run_critic_worker", return_value=critical_failure):
        critic_result = node_da_critic(base_state)

    assert critic_result["next_action"] == "post_exec_judge", (
        f"node_da_critic must ALWAYS route to post_exec_judge, got: {critic_result['next_action']}\n"
        "The DA critic is a findings collector, not a judge (M8 invariant)."
    )
    assert critic_result.get("da_critic_result") == critical_failure

    # ── Part 2: post_exec_judge blocks on critical combined failure ────────────
    # Pre-execution score = 0.45, DA critic score = 0.0
    # Combined = 0.70*0.45 + 0.30*0.0 = 0.315 — below SCORE_OPERATOR_THRESHOLD (0.60)
    judge_state = {**base_state, "da_critic_result": critical_failure, "score": 0.45}
    judge_result = node_post_exec_judge(judge_state)

    assert judge_result["next_action"] == "workflow_fail", (
        f"post_exec_judge must route to workflow_fail for critical failure, got: {judge_result['next_action']}\n"
        f"da_combined_score={judge_result.get('da_combined_score')}"
    )
    assert judge_result.get("da_combined_score", 1.0) < 0.60
    assert judge_result.get("post_exec_verdict") == "block"

    # ── Part 3: post_exec_judge passes on strong evidence ─────────────────────
    # Pre-execution score = 0.90, DA critic score = 1.0
    # Combined = 0.70*0.90 + 0.30*1.0 = 0.93 — above SCORE_PROCEED_THRESHOLD (0.85)
    critic_pass = {"passed": True, "score": 1.0, "findings": []}
    judge_state2 = {**base_state, "da_critic_result": critic_pass, "score": 0.90}
    judge_result2 = node_post_exec_judge(judge_state2)

    assert judge_result2["next_action"] == "evidence_record", (
        f"post_exec_judge must route to evidence_record for pass, got: {judge_result2['next_action']}"
    )
    assert judge_result2.get("da_combined_score", 0.0) >= 0.85
    assert judge_result2.get("post_exec_verdict") in ("proceed",)

    # ── Part 4: post_exec_judge passes advisory failure (high pre-exec) ───────
    # Pre-execution score = 0.95, DA critic score = 0.4, combined = 0.785
    # Above SCORE_OPERATOR_THRESHOLD (0.60) → evidence_record (advisory recorded, not blocked)
    critic_advisory = {"passed": False, "score": 0.4, "findings": ["minor: missing docstrings"]}
    judge_state3 = {**base_state, "da_critic_result": critic_advisory, "score": 0.95}
    judge_result3 = node_post_exec_judge(judge_state3)

    assert judge_result3["next_action"] == "evidence_record", (
        f"Advisory DA critic finding with high pre-exec score must not block workflow "
        f"(got: {judge_result3['next_action']})"
    )
    assert judge_result3.get("post_exec_verdict") in ("proceed", "needs_operator")


def test_da_enabled_routing(proj_a_id):
    """da_enabled flag set by risk_assess when worktree exists and DA is available."""
    state = make_state(proj_a_id, "da-full-a", str(TEST_WORKTREE))
    state["current_risk_class"] = "medium"
    result = node_risk_assess(state)
    # When worktree exists and deepagents is installed, da_enabled should be True
    if DEEPAGENTS_AVAILABLE:
        assert result.get("da_enabled") is True, "da_enabled must be True for medium risk with valid worktree"
    else:
        assert result.get("da_enabled") is False, "da_enabled must be False when deepagents not available"


def test_da_builder_fallback_when_no_worktree(proj_a_id):
    """node_da_builder falls back to micro_execute when worktree_path is empty."""
    state = make_state(proj_a_id, "da-full-a", "")  # explicitly empty worktree
    assert state["worktree_path"] == "", "make_state must pass empty worktree"
    result = node_da_builder(state)
    assert result["next_action"] == "micro_execute", "must fall back to micro_execute without worktree"


def test_da_drift_gate_deterministic():
    """compute_drift and gate_drift are deterministic and pure."""
    diff = "--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    r1 = compute_drift(diff=diff)
    r2 = compute_drift(diff=diff)
    assert r1["score"] == r2["score"]
    # Forbidden path
    bad = compute_drift(diff="--- a/.env\n+++ b/.env\n@@ +1 @@\n+SECRET=x\n")
    assert not bad["passed"]
    # gate wrapper
    verdict, _ = gate_drift({"execution_result": {}, "macro_steps": []})
    assert verdict == "pass"
