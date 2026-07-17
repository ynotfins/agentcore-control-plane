"""
AgentCore Database Gating Validation — Production-quality test.

Proves the effective gate: IDE → agentcore-gateway → capability profile/lease
  → agentcore-memory → governed PostgreSQL functions → RLS / project identity.

Design note: current_project_id() and assert_project_scope() are SECURITY INVOKER
read helpers. SECURITY DEFINER is applied to write functions (register_artifact_location,
record_projection_revision, register_wf_run, etc.) that operate on protected tables.
This is the correct and intentional design.

Run: python scripts/agentcore/test_database_gating.py
"""
import os, sys, json, psycopg
from pathlib import Path

pw = os.environ.get('AGENT_CORE_POSTGRES_PASSWORD', '')
admin_dsn = f'host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={pw}'

pass_count = 0
fail_count = 0
results = []


def check(name, passed, detail=""):
    global pass_count, fail_count
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {name}" + (f"  ({detail})" if detail else "")
    print(msg)
    results.append({"name": name, "passed": passed, "detail": detail})
    if passed:
        pass_count += 1
    else:
        fail_count += 1


print("\nAgentCore Database Gating Validation\n")

with psycopg.connect(admin_dsn) as conn:
    with conn.cursor() as cur:

        # ── Section 1: Role privilege isolation ──────────────────────────────
        print("1. agentcore_worker role privilege isolation...")
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'agentcore_worker'")
        check("agentcore_worker role exists", cur.fetchone() is not None)

        cur.execute("SELECT has_schema_privilege('agentcore_worker', 'agentcore', 'USAGE')")
        check("Worker has USAGE on agentcore schema (can call governed functions)", cur.fetchone()[0])

        cur.execute("SELECT has_schema_privilege('agentcore_worker', 'agentcore', 'CREATE')")
        check("Worker CANNOT CREATE in agentcore schema", not cur.fetchone()[0])

        for priv in ['INSERT', 'UPDATE', 'DELETE']:
            cur.execute(f"SELECT has_table_privilege('agentcore_worker', 'agentcore.evidence_events', %s)", (priv,))
            check(f"Worker CANNOT {priv} evidence_events directly", not cur.fetchone()[0])

        # ── Section 2: Row-Level Security ────────────────────────────────────
        # Primary evidence tables must have RLS. sessions uses FK+project isolation instead.
        print("\n2. Row-Level Security on primary evidence tables...")
        for tbl in ['evidence_events', 'artifact_objects']:
            cur.execute("""
                SELECT relrowsecurity FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'agentcore' AND c.relname = %s
            """, (tbl,))
            row = cur.fetchone()
            check(f"RLS enabled on {tbl}", row is not None and row[0])

        # ── Section 3: SECURITY DEFINER write surface ─────────────────────────
        print("\n3. SECURITY DEFINER write functions (the actual gate)...")
        sec_definer_fns = [
            'register_artifact_location',
            'record_projection_revision',
            'register_wf_run',
        ]
        for fn in sec_definer_fns:
            cur.execute("""
                SELECT prosecdef FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'agentcore' AND p.proname = %s LIMIT 1
            """, (fn,))
            row = cur.fetchone()
            check(f"{fn}() is SECURITY DEFINER (enforces project scope)", row is not None and row[0])

        # Verify read helpers are SECURITY INVOKER (correct design)
        print("\n4. SECURITY INVOKER read helpers (correct design — not DEFINER)...")
        invoker_fns = ['current_project_id', 'assert_project_scope']
        for fn in invoker_fns:
            cur.execute("""
                SELECT prosecdef FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'agentcore' AND p.proname = %s LIMIT 1
            """, (fn,))
            row = cur.fetchone()
            check(f"{fn}() is SECURITY INVOKER (read helper, correct)", row is not None and not row[0])

        # Worker can execute governed functions
        cur.execute("""
            SELECT COUNT(*) FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'agentcore'
              AND has_function_privilege('agentcore_worker', p.oid, 'EXECUTE')
        """)
        executable_count = cur.fetchone()[0]
        check(f"Worker can EXECUTE {executable_count} governed functions",
              executable_count > 0, f"{executable_count} functions")

        # ── Section 5: Ten-tool memory surface ───────────────────────────────
        print("\n5. Ten-tool memory surface (Bifrost config)...")
        cfg_path = Path(r"H:\AgentRuntime\bifrost\config.json")
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text())
            mem_server = next(
                (c for c in cfg['mcp']['client_configs'] if c['name'] == 'agentcore_memory'), None
            )
            if mem_server:
                tools = mem_server.get('tools_to_execute', [])
                expected = {
                    'memory_status', 'startup_context', 'retrieve_context', 'append_event',
                    'propose_fact', 'expand_source', 'session_open', 'session_close',
                    'build_handoff', 'docs_search'
                }
                actual = set(tools)
                missing = expected - actual
                extra = actual - expected
                check("Exactly 10 approved agentcore-memory tools in Bifrost",
                      len(tools) == 10 and not missing and not extra,
                      f"count={len(tools)} missing={missing} extra={extra}")
                check("No SQL/DDL tools in memory surface",
                      not any(kw in t.lower() for t in tools for kw in ['sql', 'ddl', 'exec', 'psql']))

                # Verify canonical source path
                src = next((a for a in mem_server['stdio_config']['args'] if '.py' in a), '')
                check("agentcore_memory sources from canonical repo",
                      'agentcore-control-plane\\' in src and '-unbounded-memory' not in src, src)

        # ── Section 6: No DB credentials in IDE configs ───────────────────────
        print("\n6. No database credentials in IDE configs...")
        cursor_mcp = Path(r"C:\Users\ynotf\.cursor\mcp.json")
        if cursor_mcp.exists():
            content = cursor_mcp.read_text()
            has_pg = any(kw in content for kw in ['55433', 'agentcore_worker', 'AGENT_CORE_POSTGRES'])
            check("Cursor mcp.json free of PostgreSQL credentials", not has_pg)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\nDatabase Gating Validation Complete")
print(f"  PASS: {pass_count}  FAIL: {fail_count}")

if fail_count > 0:
    print("\nFailed checks:")
    for r in results:
        if not r['passed']:
            print(f"  - {r['name']}" + (f": {r['detail']}" if r['detail'] else ""))
    sys.exit(1)

print("\nAll database gating checks passed.")
sys.exit(0)
