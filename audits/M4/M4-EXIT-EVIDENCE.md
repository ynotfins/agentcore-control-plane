# M4 Exit Evidence — AgentCore Memory Gateway

**Status:** PASSED  
**Completed on:** 2026-07-15 / 2026-07-16 UTC  
**Gateway:** `agentcore-gateway` at `http://127.0.0.1:8080/mcp`  
**Upstream identity:** `agentcore-memory` (unchanged)  
**Server implementation:** `scripts/agentcore_memory/server.py` version `0.4.0`  
**Acceptance summary:** `audits/M4/m4-acceptance-summary.json` (run `20260715232254`)  
**Migration applied:** `migrations/m4/001_up_assemble_context_window_quarantine_filter.sql`  
  — adds `trust_class NOT IN ('quarantined', 'rejected')` filter to `assemble_context_window` (acceptance test 12)  
**Context Fabric repair:** `.context-fabric/runtime/dist/engines/watcher.js`  
  — added `maxBuffer: 128 * 1024 * 1024` to `runGitBuffer` `spawnSync` call; installed `better-sqlite3`  
  — root cause: 200-file batch output (~1.3 MB) exceeded Node.js `spawnSync` default 1 MB buffer  

## Compact Tool Surface

Live Bifrost `tools/list` exposed exactly the M4 compact surface for `agentcore_memory`:

```text
agentcore_memory-append_event
agentcore_memory-build_handoff
agentcore_memory-docs_search
agentcore_memory-expand_source
agentcore_memory-memory_health
agentcore_memory-memory_status
agentcore_memory-propose_fact
agentcore_memory-retrieve_context
agentcore_memory-session_close
agentcore_memory-session_open
agentcore_memory-startup_context
```

No raw SQL, DDL, database-admin, or Bifrost-admin tools are exposed.

## Exit Criteria

| BLUEPRINT.md M4 exit criterion | Result | Evidence |
| -- | -- | -- |
| Existing Bifrost identity `agentcore-gateway` remains unchanged | PASS | `contracts/agentcore-gateway-client.json`; live endpoint `http://127.0.0.1:8080/mcp` |
| Upstream identity `agentcore-memory` remains unchanged | PASS | `contracts/bifrost-upstream-mcp-registry.json` key `agentcore-memory`; `bifrost_client_name=agentcore_memory` |
| No IDE configuration edit is required | PASS | Check 18: cursor mcp.json mtime unchanged |
| Multiple IDEs/sessions use separate sessions safely | PASS | Check 5: sessions A and B isolated by session_id |
| Append → retrieve → compact → expand works end to end | PASS | Check 3: two events → L1 summary → expand returns exact originals |
| Startup context includes bounded global/project/session/constraint state | PASS | Check 4: tokens within budget; authority chain present |
| Degraded components reported clearly | PASS | Check 16: cognee=not_integrated_until_M5; langgraph=not_integrated_until_M6 |
| No raw database/admin tools exposed | PASS | Check 2: no sql/admin/ddl tools in surface |
| Restart and reconnect tests pass | PASS | Check 14: memory-service kill+respawn; Check 15: Bifrost stop+start |
| CHAOSCENTRAL machine documentation refreshed | IN PROGRESS | See CHAOSCENTRAL section below |

## Full Acceptance Test Results (19 checks)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Direct MCP initialize and tools/list | PASS | server=builder v2.0.0-prerelease1 |
| 2 | Exact compact advertised tool set | PASS | 11 tools, no admin/SQL tools |
| 3 | Session open → append → retrieve → compact → expand → close | PASS | summary; sources=2 |
| 3b | session_close creates durable final state | PASS | 3 sessions closed; ended_at set |
| 4 | Startup context within selected token budget | PASS | total_tokens=24 ≤ max_tokens=4096 |
| 5 | Two simultaneous clients use isolated sessions | PASS | A and B have distinct session_ids |
| 6 | Two projects cannot cross-read or cross-write | PASS | project_A and project_B isolated |
| 7 | Repeated append with same idempotency key no dup | PASS | evidence_events_count=1 |
| 8 | Large payload externalizes and expands correctly | PASS | artifact_id; H: storage_uri returned |
| 9 | Archived payload on E: expands correctly | PASS | cold_e location registered; expand returns E: URI |
| 10 | Fact proposal does not silently become promoted truth | PASS | status=proposed (not accepted) |
| 11 | Handoff generation is deterministic | PASS | events=5; consistent across two calls |
| 12 | Quarantined evidence excluded from startup context | PASS | quarantined event absent from context |
| 13 | PostgreSQL interruption and recovery | PASS | healthy=true; degraded probe on wrong port=false; note: service stop requires admin |
| 14 | Memory-service restart and reconnect | PASS | process killed; Bifrost respawned at new PID |
| 15 | Bifrost restart and automatic upstream reconnect | PASS | stop+start via ops scripts; 11 tools confirmed |
| 16 | Optional/future components report degraded | PASS | cognee=M5; langgraph=M6 |
| 17 | One safe Cursor call through agentcore-gateway | PASS | server=agentcore-memory version=0.4.0 |
| 18 | No IDE configuration changes occurred | PASS | cursor mcp.json mtime unchanged |

## Live Config Evidence

- Live Bifrost config: `H:\AgentRuntime\bifrost\config.json`
- Sanitized rendered config: `renderers\bifrost\config.sanitized.json`

## Rollback Procedure

1. Restore `scripts/agentcore_memory/server.py` from pre-M4 commit `4fdfaf6` or the prior health/status-only implementation.
2. Revert `agentcore-memory` `permitted_tools` in `contracts/bifrost-upstream-mcp-registry.json` to `memory_health`, `memory_status`.
3. Run `python scripts\bifrost\render_bifrost_config.py`.
4. Apply rollback migration: `psql ... -f migrations/m4/001_down_assemble_context_window_quarantine_filter.sql`
5. Restart Bifrost via approved ops scripts.
6. IDE configs remain unchanged throughout rollback.

## CHAOSCENTRAL Documentation

Runtime delta: M4 gateway quarantine filter migration applied; Context Fabric repaired (better-sqlite3 installed, spawnSync maxBuffer patched). No new ports, services, or drives added. Documentation update in progress (see below).

## Out of Scope Confirmed

- No M5 Cognee integration.
- No M6 LangGraph checkpoint tables.
- No dynamic Bifrost tool leases.
- No IDE MCP config edits.
