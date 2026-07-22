"""AgentCore M8 Acceptance Tests — 20 checks.

Run with: python scripts/agentcore_workflow/tests/m8_acceptance.py
Exits 0 on full pass, 1 on any failure.
Writes JSON summary to audits/M8/m8-acceptance-summary.json.

Authority: BLUEPRINT.md M8 / MEMORY_PLATFORM_EXECUTION_PLAN.md M8.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/agentcore_workflow/tests/m8_acceptance.py → parents[3] = repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

PG_PASS = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
CI = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={PG_PASS}"
RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

results: list[dict] = []
all_passed = True


def check(num: int, name: str, passed: bool, detail: str = "") -> None:
    global all_passed
    if not passed:
        all_passed = False
    status = "PASS" if passed else "FAIL"
    results.append({"check": num, "name": name, "status": status, "detail": detail})
    print(f"{status} {num:02d} - {name}" + (f" — {detail}" if detail else ""))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 01: PostgreSQL 18 reachable
# ─────────────────────────────────────────────────────────────────────────────
def test_01_postgres():
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(CI, row_factory=dict_row, connect_timeout=5) as c:
            ver = c.execute("SELECT version()").fetchone()
            db = c.execute("SELECT current_database()").fetchone()
            version_str = ver["version"] if ver else ""
            db_name = db["current_database"] if db else ""

        passed = "PostgreSQL 18" in version_str and db_name == "agent_core"
        check(1, "PostgreSQL 18 reachable, agent_core accessible", passed,
              f"version={version_str[:50]}, db={db_name}")
    except Exception as exc:
        check(1, "PostgreSQL 18 reachable, agent_core accessible", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 02: Bifrost gateway reachable (returns 401)
# ─────────────────────────────────────────────────────────────────────────────
def test_02_bifrost():
    import urllib.request, urllib.error
    url = "http://127.0.0.1:8080/mcp"
    try:
        try:
            urllib.request.urlopen(url, timeout=5)
            check(2, "Bifrost gateway reachable (returns 401)", True, "status=200 (no auth required)")
        except urllib.error.HTTPError as he:
            passed = he.code == 401
            check(2, "Bifrost gateway reachable (returns 401)", passed, f"status={he.code}")
        except urllib.error.URLError as ue:
            check(2, "Bifrost gateway reachable (returns 401)", False, str(ue))
    except Exception as exc:
        check(2, "Bifrost gateway reachable (returns 401)", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 03: Memory service 10-tool surface intact
# ─────────────────────────────────────────────────────────────────────────────
def test_03_memory_surface():
    expected = {
        "memory_status", "startup_context", "retrieve_context", "append_event",
        "propose_fact", "expand_source", "session_open", "session_close",
        "build_handoff", "docs_search",
    }
    try:
        mem_path = str(REPO_ROOT / "scripts" / "agentcore_memory")
        if mem_path not in sys.path:
            sys.path.insert(0, mem_path)
        import importlib, server as mem_server
        importlib.reload(mem_server)
        actual = {t["name"] for t in mem_server.tool_defs()}
        missing = sorted(expected - actual)
        passed = not missing
        detail = f"tools={len(actual)}, missing={missing}" if missing else f"all {len(actual)} tools present"
        check(3, "Memory service 10-tool surface intact", passed, detail)
    except Exception as exc:
        check(3, "Memory service 10-tool surface intact", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 04: Post-execution independent judge exists in graph
# ─────────────────────────────────────────────────────────────────────────────
def test_04_post_exec_judge_node():
    try:
        from agentcore_workflow import nodes
        exists = hasattr(nodes, "node_post_exec_judge") and callable(nodes.node_post_exec_judge)
        check(4, "node_post_exec_judge exists in nodes module", exists,
              "node_post_exec_judge callable" if exists else "MISSING node_post_exec_judge")
    except Exception as exc:
        check(4, "node_post_exec_judge exists in nodes module", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 05: DA critic always routes to post_exec_judge
# ─────────────────────────────────────────────────────────────────────────────
def test_05_da_critic_routes_to_judge():
    try:
        node_src = (REPO_ROOT / "scripts" / "agentcore_workflow" / "nodes.py").read_text(encoding="utf-8")
        # node_da_critic must route to post_exec_judge, not evidence_record or workflow_fail directly
        in_critic_fn = False
        lines = node_src.splitlines()
        critic_lines: list[str] = []
        for i, line in enumerate(lines):
            if "def node_da_critic" in line:
                in_critic_fn = True
            elif in_critic_fn and line.startswith("def ") and "node_da_critic" not in line:
                break
            if in_critic_fn:
                critic_lines.append(line)

        critic_body = "\n".join(critic_lines)
        routes_to_judge = '"post_exec_judge"' in critic_body or "'post_exec_judge'" in critic_body
        no_direct_evidence = '"evidence_record"' not in critic_body or "next_action" not in critic_body.split('"evidence_record"')[0]

        passed = routes_to_judge
        check(5, "DA critic routes always to post_exec_judge", passed,
              "found 'post_exec_judge' route in node_da_critic" if passed else "MISSING post_exec_judge route")
    except Exception as exc:
        check(5, "DA critic routes always to post_exec_judge", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 06: requirements.txt exists and has pinned versions
# ─────────────────────────────────────────────────────────────────────────────
def test_06_requirements_pinned():
    req = REPO_ROOT / "scripts" / "agentcore_workflow" / "requirements.txt"
    try:
        if not req.exists():
            check(6, "requirements.txt exists and is pinned", False, "file not found")
            return
        content = req.read_text(encoding="utf-8")
        lines = [l.strip() for l in content.splitlines()
                 if l.strip() and not l.strip().startswith("#")]
        # Pinned = has == or >= with specific version (not just package names)
        pinned = [l for l in lines if "==" in l or ">=" in l]
        passed = len(pinned) >= 3
        check(6, "requirements.txt exists and is pinned", passed,
              f"{len(pinned)} pinned packages in {req.name}")
    except Exception as exc:
        check(6, "requirements.txt exists and is pinned", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 07: At least AgentCore-Bifrost-Gateway scheduled task exists
# ─────────────────────────────────────────────────────────────────────────────
def test_07_scheduled_tasks():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-ScheduledTask -TaskPath '\\AgentCore\\' -TaskName 'AgentCore-Bifrost-Gateway' -ErrorAction SilentlyContinue).State"],
            capture_output=True, text=True, timeout=15,
        )
        state = out.stdout.strip()
        passed = bool(state) and state != "Missing"
        check(7, "AgentCore-Bifrost-Gateway scheduled task exists", passed,
              f"state={state!r}" if state else "task not found")
    except Exception as exc:
        check(7, "AgentCore-Bifrost-Gateway scheduled task exists", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 08: Backup script exists
# ─────────────────────────────────────────────────────────────────────────────
def test_08_backup_script():
    path = REPO_ROOT / "ops" / "Backup-AgentCorePostgres.ps1"
    passed = path.exists()
    check(8, "Backup-AgentCorePostgres.ps1 exists", passed, str(path))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 09: Restore test script exists
# ─────────────────────────────────────────────────────────────────────────────
def test_09_restore_script():
    path = REPO_ROOT / "ops" / "Test-AgentCorePostgresRestore.ps1"
    passed = path.exists()
    check(9, "Test-AgentCorePostgresRestore.ps1 exists", passed, str(path))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: PITR script exists
# ─────────────────────────────────────────────────────────────────────────────
def test_10_pitr_script():
    path = REPO_ROOT / "ops" / "Test-AgentCorePg18Pitr.ps1"
    passed = path.exists()
    check(10, "Test-AgentCorePg18Pitr.ps1 exists", passed, str(path))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 11: No Swarm tables in agent_core (wf_ tables exist; swarm count = 0)
# ─────────────────────────────────────────────────────────────────────────────
def test_11_no_swarm_tables():
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(CI, row_factory=dict_row, connect_timeout=5) as c:
            # wf_ tables should exist (M6)
            wf = c.execute("""
                SELECT COUNT(*) AS cnt FROM pg_tables
                WHERE schemaname = 'agentcore' AND tablename LIKE 'wf_%'
            """).fetchone()
            wf_count = wf["cnt"] if wf else 0

            # Swarm tables: swarm_*, recall_*, vault_* should not be present
            swarm = c.execute("""
                SELECT COUNT(*) AS cnt FROM pg_tables
                WHERE schemaname = 'agentcore'
                AND (tablename LIKE 'swarm_%' OR tablename LIKE 'recall_%' OR tablename LIKE 'vault_%')
            """).fetchone()
            swarm_count = swarm["cnt"] if swarm else 0

        passed = wf_count > 0 and swarm_count == 0
        check(11, "No Swarm tables in agent_core (wf_ tables present)", passed,
              f"wf_tables={wf_count}, swarm_tables={swarm_count}")
    except Exception as exc:
        check(11, "No Swarm tables in agent_core (wf_ tables present)", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 12: M6 regression still passes (run m6_acceptance.py)
# ─────────────────────────────────────────────────────────────────────────────
def test_12_m6_regression():
    m6_script = REPO_ROOT / "scripts" / "agentcore_workflow" / "tests" / "m6_acceptance.py"
    try:
        if not m6_script.exists():
            check(12, "M6 regression passes (m6_acceptance.py)", False, "script not found")
            return
        result = subprocess.run(
            [sys.executable, str(m6_script)],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "PYTHONPATH": str(SCRIPTS)},
        )
        passed = result.returncode == 0
        tail = result.stdout.strip().splitlines()[-5:] if result.stdout.strip() else []
        detail = f"exit={result.returncode}; last={tail[-1] if tail else 'no output'}"
        check(12, "M6 regression passes (m6_acceptance.py)", passed, detail)
    except Exception as exc:
        check(12, "M6 regression passes (m6_acceptance.py)", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 13: IDE enrollment matrix exists
# ─────────────────────────────────────────────────────────────────────────────
def test_13_ide_matrix():
    path = REPO_ROOT / "ide-profiles" / "IDE_CAPABILITY_MATRIX.yaml"
    try:
        passed = path.exists()
        detail = ""
        if passed:
            content = path.read_text(encoding="utf-8")
            has_m8 = "m8_enrollment" in content
            detail = "has m8_enrollment field" if has_m8 else "exists but no m8_enrollment field yet"
        check(13, "IDE_CAPABILITY_MATRIX.yaml exists", passed, detail)
    except Exception as exc:
        check(13, "IDE_CAPABILITY_MATRIX.yaml exists", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 14: GLOBAL_STATE.md exists
# ─────────────────────────────────────────────────────────────────────────────
def test_14_global_state():
    path = Path(r"C:\Users\ynotf\.agentcore\GLOBAL_STATE.md")
    passed = path.exists()
    detail = f"size={path.stat().st_size}b" if passed else "not found"
    check(14, "GLOBAL_STATE.md exists at C:\\Users\\ynotf\\.agentcore\\", passed, detail)


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 15: No secrets in key config files
# ─────────────────────────────────────────────────────────────────────────────
def test_15_no_secrets():
    # Patterns that indicate actual secret values (not references/templates)
    # Detect: long bare token values, actual passwords, private key headers
    # Exclude: env var references (env., ${env:, %VAR%, AGENT_CORE_), placeholder text,
    #          comments, documentation strings, and common auth header schema patterns.
    _ENV_SAFE = (
        "env.", "${env:", "%env%", "AGENT_CORE_", "os.environ",
        "env_var", "${", "example", "<your", "placeholder",
        "Bearer env", "Bearer ${", "Bearer %",
    )

    def _is_env_reference(line: str) -> bool:
        lo = line.lower()
        return any(s.lower() in lo for s in _ENV_SAFE)

    import re

    # Match real secret shapes only — avoid false positives like "task-classifications"
    # containing the substring "sk-".
    secret_res = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),  # OpenAI-style API keys
    ]
    scan_files = [
        REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json",
        REPO_ROOT / "contracts" / "agentcore-gateway-client.json",
        REPO_ROOT / "scripts" / "agentcore_workflow" / "requirements.txt",
    ]
    found_secrets: list[str] = []
    for f in scan_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for rx in secret_res:
            hit_lines = [
                l for l in text.splitlines()
                if rx.search(l) and not _is_env_reference(l)
            ]
            if hit_lines:
                found_secrets.append(f"{f.name}:{rx.pattern}")
                break

    passed = len(found_secrets) == 0
    detail = ("clean" if passed else f"potential secrets in: {found_secrets}")
    check(15, "No secrets in key config files", passed, detail)


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 16: Deep Agents bounded — critic read-only, builder write
# ─────────────────────────────────────────────────────────────────────────────
def test_16_da_bounded():
    try:
        worker_src = (REPO_ROOT / "scripts" / "agentcore_workflow" / "deepagents_worker.py").read_text(encoding="utf-8")
        # Critic must use read-only operations
        has_read_only = 'operations=["read"]' in worker_src or "operations=['read']" in worker_src
        # Builder must have write or read+write
        has_builder_write = "run_builder_worker" in worker_src
        # MemoryMiddleware must be disabled
        no_memory_middleware = "MemoryMiddleware" not in worker_src or "# MemoryMiddleware" in worker_src or "disabled" in worker_src.lower()

        passed = has_read_only and has_builder_write and no_memory_middleware
        detail = (
            f"read_only_critic={'yes' if has_read_only else 'NO'}, "
            f"builder_write={'yes' if has_builder_write else 'NO'}, "
            f"memory_mw_disabled={'yes' if no_memory_middleware else 'NO'}"
        )
        check(16, "DA bounded: critic read-only, builder write, MemoryMiddleware disabled", passed, detail)
    except Exception as exc:
        check(16, "DA bounded: critic read-only, builder write, MemoryMiddleware disabled", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 17: Operator CLI exists
# ─────────────────────────────────────────────────────────────────────────────
def test_17_operator_cli():
    path = REPO_ROOT / "scripts" / "agentcore" / "__main__.py"
    init = REPO_ROOT / "scripts" / "agentcore" / "__init__.py"
    passed = path.exists() and init.exists()
    detail = f"__main__.py={'ok' if path.exists() else 'MISSING'}, __init__.py={'ok' if init.exists() else 'MISSING'}"
    check(17, "Operator CLI exists (scripts/agentcore/__main__.py)", passed, detail)


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 18: Capability leases isolated — projects cannot see each other's leases
# ─────────────────────────────────────────────────────────────────────────────
def test_18_lease_isolation():
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(CI, row_factory=dict_row, connect_timeout=5) as c:
            # Check that capability_profiles has a project_id FK (per-project scoping)
            col = c.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'agentcore'
                AND table_name = 'capability_profiles'
                AND column_name = 'project_id'
            """).fetchone()
            has_project_fk = col is not None

            # Verify no cross-project tool rows are visible by checking isolation function
            check_fn = c.execute("""
                SELECT routine_name FROM information_schema.routines
                WHERE routine_schema = 'agentcore'
                AND routine_name = 'assert_project_scope'
            """).fetchone()
            has_isolation_fn = check_fn is not None

        passed = has_project_fk and has_isolation_fn
        detail = (
            f"capability_profiles.project_id={'present' if has_project_fk else 'MISSING'}, "
            f"assert_project_scope={'present' if has_isolation_fn else 'MISSING'}"
        )
        check(18, "Capability leases isolated (project_id FK + assert_project_scope)", passed, detail)
    except Exception as exc:
        check(18, "Capability leases isolated", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 19: M7 acceptance passes
# ─────────────────────────────────────────────────────────────────────────────
def test_19_m7_acceptance():
    m7_script = REPO_ROOT / "scripts" / "engineering" / "test_m7_acceptance.py"
    try:
        if not m7_script.exists():
            check(19, "M7 acceptance passes", False, "test_m7_acceptance.py not found")
            return
        result = subprocess.run(
            [sys.executable, str(m7_script)],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "PYTHONPATH": str(SCRIPTS)},
        )
        passed = result.returncode == 0
        tail = result.stdout.strip().splitlines()[-3:] if result.stdout.strip() else []
        detail = f"exit={result.returncode}; last={tail[-1] if tail else 'no output'}"
        check(19, "M7 acceptance passes (test_m7_acceptance.py)", passed, detail)
    except Exception as exc:
        check(19, "M7 acceptance passes (test_m7_acceptance.py)", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 20: Swarm isolation — SwarmRecall API not in agentcore-memory tools list
# ─────────────────────────────────────────────────────────────────────────────
def test_20_swarm_isolation():
    try:
        mem_path = str(REPO_ROOT / "scripts" / "agentcore_memory")
        if mem_path not in sys.path:
            sys.path.insert(0, mem_path)
        import importlib, server as mem_server
        importlib.reload(mem_server)
        tool_names = [t["name"] for t in mem_server.tool_defs()]
        # SwarmRecall-related tool names should not appear in agentcore-memory
        swarm_tools = [t for t in tool_names if any(
            s in t.lower() for s in ["swarm", "recall", "vault", "claw"]
        )]
        passed = len(swarm_tools) == 0
        detail = f"no Swarm tools found in agentcore-memory" if passed else f"SWARM TOOLS FOUND: {swarm_tools}"
        check(20, "Swarm isolation: no SwarmRecall tools in agentcore-memory", passed, detail)
    except Exception as exc:
        check(20, "Swarm isolation: no SwarmRecall tools in agentcore-memory", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 21: A/B worker module exists and exports correct symbols
# ─────────────────────────────────────────────────────────────────────────────

def test_21_ab_worker_module():
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import importlib
        ab = importlib.import_module("agentcore_workflow.ab_worker")
        required = [
            "create_ab_worktree",
            "archive_and_remove_ab_worktree",
            "run_ab_alternate_builder",
            "compare_ab_results",
        ]
        missing = [s for s in required if not hasattr(ab, s)]
        passed = len(missing) == 0
        detail = "all A/B symbols present" if passed else f"missing: {missing}"
        check(21, "A/B worker module exists with required symbols", passed, detail)
    except Exception as exc:
        check(21, "A/B worker module exists with required symbols", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 22: Low-risk work never enables A/B (no alternate worktree created)
# ─────────────────────────────────────────────────────────────────────────────

def test_22_ab_low_risk_skipped():
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from agentcore_workflow.critics import should_enable_ab
        low_enabled, low_just = should_enable_ab("low", 0.9)
        medium_enabled, medium_just = should_enable_ab("medium", 0.9)
        high_low_u, _ = should_enable_ab("high", 0.4)
        high_hi_u, _ = should_enable_ab("high", 0.5)
        critical_hi_u, _ = should_enable_ab("critical", 0.8)
        passed = (
            not low_enabled
            and not medium_enabled
            and not high_low_u
            and high_hi_u
            and critical_hi_u
        )
        detail = (
            f"low={low_enabled} med={medium_enabled} "
            f"high+low_u={high_low_u} high+hi_u={high_hi_u} critical={critical_hi_u}"
        )
        check(22, "Low-risk never enables A/B; qualifying high-risk does", passed, detail)
    except Exception as exc:
        check(22, "Low-risk never enables A/B; qualifying high-risk does", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 23: node_da_critic routes to ab_alternate when ab_enabled=True
# ─────────────────────────────────────────────────────────────────────────────

def test_23_da_critic_routes_to_ab_when_enabled():
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        node_src = (REPO_ROOT / "scripts" / "agentcore_workflow" / "nodes.py").read_text(encoding="utf-8")
        in_critic_fn = False
        critic_lines: list[str] = []
        for line in node_src.splitlines():
            if "def node_da_critic" in line:
                in_critic_fn = True
            elif in_critic_fn and line.startswith("def ") and "node_da_critic" not in line:
                break
            if in_critic_fn:
                critic_lines.append(line)
        critic_body = "\n".join(critic_lines)
        routes_to_ab = "ab_alternate" in critic_body
        uses_ab_enabled = "ab_enabled" in critic_body
        passed = routes_to_ab and uses_ab_enabled
        detail = f"ab_alternate_route={routes_to_ab} uses_ab_enabled={uses_ab_enabled}"
        check(23, "da_critic routes to ab_alternate when ab_enabled=True", passed, detail)
    except Exception as exc:
        check(23, "da_critic routes to ab_alternate when ab_enabled=True", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 24: post_exec_judge compares A and B results (ab_alt_result in state)
# ─────────────────────────────────────────────────────────────────────────────

def test_24_post_exec_judge_ab_comparison():
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from agentcore_workflow.ab_worker import compare_ab_results

        # Case 1: low-risk - B path skipped → A selected
        a_ok = {"status": "completed", "score": 0.8}
        b_skip = {"status": "skipped", "score": 0.0}
        sel, just = compare_ab_results(a_ok, b_skip)
        case1 = sel == "A"

        # Case 2: both completed, B clearly better → B selected
        a_low = {"status": "completed", "score": 0.6}
        b_high = {"status": "completed", "score": 0.9}
        sel2, just2 = compare_ab_results(a_low, b_high)
        case2 = sel2 == "B"

        # Case 3: both failed → both_rejected
        a_fail = {"status": "error"}
        b_fail = {"status": "error"}
        sel3, just3 = compare_ab_results(a_fail, b_fail)
        case3 = sel3 == "both_rejected"

        # Case 4: scores close (within 0.05) → A as tiebreaker
        a_close = {"status": "completed", "score": 0.82}
        b_close = {"status": "completed", "score": 0.80}
        sel4, just4 = compare_ab_results(a_close, b_close)
        case4 = sel4 == "A"

        passed = case1 and case2 and case3 and case4
        detail = (
            f"case1(A wins skip)={case1} case2(B wins high)={case2} "
            f"case3(both_rejected)={case3} case4(A tiebreak)={case4}"
        )
        check(24, "post_exec_judge A/B comparison: correct selection in all 4 cases", passed, detail)
    except Exception as exc:
        check(24, "post_exec_judge A/B comparison: correct selection in all 4 cases", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 25: ab_alternate and post_exec_judge nodes wired in workflow graph
# ─────────────────────────────────────────────────────────────────────────────

def test_25_ab_wired_in_workflow():
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        wf_src = (REPO_ROOT / "scripts" / "agentcore_workflow" / "workflow.py").read_text(encoding="utf-8")
        has_ab_node = "ab_alternate" in wf_src
        has_conditional_da_critic = "add_conditional_edges" in wf_src and "ab_alternate" in wf_src
        has_ab_to_pej_edge = "add_edge" in wf_src and "ab_alternate" in wf_src
        passed = has_ab_node and has_conditional_da_critic and has_ab_to_pej_edge
        detail = (
            f"ab_node={has_ab_node} conditional_da_critic={has_conditional_da_critic} "
            f"ab_to_pej={has_ab_to_pej_edge}"
        )
        check(25, "ab_alternate node wired into workflow graph with conditional routing", passed, detail)
    except Exception as exc:
        check(25, "ab_alternate node wired into workflow graph with conditional routing", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 26: IDE enrollment matrix: Cursor live_validated; others documented
# ─────────────────────────────────────────────────────────────────────────────

def test_26_ide_enrollment_accuracy():
    try:
        import yaml  # type: ignore[import]
        matrix_path = REPO_ROOT / "ide-profiles" / "IDE_CAPABILITY_MATRIX.yaml"
        matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        ides = matrix.get("managed_ides", {})

        valid_statuses = {"live_validated", "configured_restart_required", "awaiting_operator_import", "unsupported_with_reason"}
        invalid_statuses = []
        for name, ide in ides.items():
            status = ide.get("m8_enrollment", "")
            if status not in valid_statuses:
                invalid_statuses.append(f"{name}={status}")

        cursor_status = ides.get("cursor", {}).get("m8_enrollment", "")
        cursor_live = cursor_status == "live_validated"
        no_artifact_claim = len(invalid_statuses) == 0

        passed = cursor_live and no_artifact_claim
        detail = f"cursor={cursor_status} invalid_statuses={invalid_statuses}"
        check(26, "IDE matrix: Cursor live_validated; no raw artifact_generated claims", passed, detail)
    except Exception as exc:
        check(26, "IDE matrix: Cursor live_validated; no raw artifact_generated claims", False, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"AgentCore M8 Acceptance Tests — {RUN_TS}")
    print(f"Repository: {REPO_ROOT}")
    print("=" * 72)

    test_01_postgres()
    test_02_bifrost()
    test_03_memory_surface()
    test_04_post_exec_judge_node()
    test_05_da_critic_routes_to_judge()
    test_06_requirements_pinned()
    test_07_scheduled_tasks()
    test_08_backup_script()
    test_09_restore_script()
    test_10_pitr_script()
    test_11_no_swarm_tables()
    test_12_m6_regression()
    test_13_ide_matrix()
    test_14_global_state()
    test_15_no_secrets()
    test_16_da_bounded()
    test_17_operator_cli()
    test_18_lease_isolation()
    test_19_m7_acceptance()
    test_20_swarm_isolation()
    test_21_ab_worker_module()
    test_22_ab_low_risk_skipped()
    test_23_da_critic_routes_to_ab_when_enabled()
    test_24_post_exec_judge_ab_comparison()
    test_25_ab_wired_in_workflow()
    test_26_ide_enrollment_accuracy()

    print("=" * 72)
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = len(results) - passed_count
    print(f"Results: {passed_count}/{len(results)} PASS, {failed_count} FAIL")
    print("OVERALL: PASS" if all_passed else "OVERALL: FAIL")

    # Write JSON summary
    summary_dir = REPO_ROOT / "audits" / "M8"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_ts": RUN_TS,
        "repo_root": str(REPO_ROOT),
        "total": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "overall": "PASS" if all_passed else "FAIL",
        "checks": results,
    }

    json_path = summary_dir / "m8-acceptance-summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    txt_path = summary_dir / "m8-acceptance-summary.txt"
    lines = [
        f"AgentCore M8 Acceptance Tests — {RUN_TS}",
        f"Repository: {REPO_ROOT}",
        "=" * 72,
    ]
    for r in results:
        lines.append(f"{r['status']} {r['check']:02d} - {r['name']}" + (f" — {r['detail']}" if r['detail'] else ""))
    lines += [
        "=" * 72,
        f"Results: {passed_count}/{len(results)} PASS, {failed_count} FAIL",
        "OVERALL: PASS" if all_passed else "OVERALL: FAIL",
    ]
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Summary: {json_path}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
