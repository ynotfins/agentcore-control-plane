# M4 Exit Evidence — AgentCore Memory Gateway

**Status:** PASSED  
**Completed on:** 2026-07-15 / 2026-07-16 UTC  
**Gateway:** `agentcore-gateway` at `http://127.0.0.1:8080/mcp`  
**Upstream identity:** `agentcore-memory` (unchanged)  
**Server implementation:** `scripts/agentcore_memory/server.py` version `0.4.0`  
**Acceptance summary:** `audits/M4/m4-acceptance-summary.json` (run `20260715212207`)
**CHAOSCENTRAL documentation sync:** `56ba566` in `D:\ChaosCentral-Current-Build` (`docs: sync machine docs after AgentCore M4 gateway expansion`). This local commit added runtime snapshot `PC_RUNTIME_SNAPSHOT_20260715-212243` and passed `scripts\Test-PCDocumentation.ps1` (30/30). The repository has no configured remote, so push is not available.

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
| No IDE configuration edit is required | PASS | Only Bifrost registry/rendered config and upstream server implementation changed; IDE gateway client remains one `agentcore-gateway` entry |
| Multiple IDEs/sessions use separate sessions safely | PASS | Harness opened two sessions (`cursor-m4-a`, `cursor-m4-b`) and wrote events independently |
| Append → retrieve → compact → expand works end to end | PASS | Harness appended two events through gateway, created compact summary internally, retrieved context, expanded summary back to exact source events |
| Startup context includes bounded global/project/session/constraint state | PASS | `startup_context` returned authority-aware bounded packet |
| Degraded components reported clearly | PASS | `memory_status` reports Cognee `not_integrated_until_M5`, LangGraph `not_integrated_until_M6` |
| No raw database/admin tools exposed | PASS | Live tool-list check rejects SQL/admin tool names |
| Restart and reconnect tests pass | PASS | Bifrost restarted via `ops/bifrost/Stop-AgentCoreBifrostGateway.ps1` + `Start-AgentCoreBifrostGateway.ps1`; endpoint healthy; tools-list refreshed |
| CHAOSCENTRAL machine documentation refreshed after MCP/runtime topology change | PASS | `D:\ChaosCentral-Current-Build` commit `56ba566`; new runtime snapshot `PC_RUNTIME_SNAPSHOT_20260715-212243`; validation 30/30 |

## Live Config Evidence

- Live Bifrost config: `H:\AgentRuntime\bifrost\config.json`, SHA-256 `01CEAB34A23D44B0290817FB0307929D2CF0EC9EC3CF4743AA08146B72D1F254`
- Sanitized rendered config: `renderers\bifrost\config.sanitized.json`, SHA-256 `47D67E6083B7452AA8C24D9D9DCCADB623DA19A48DD9FB6180773DD009B5F0FE`

## Rollback Procedure

1. Restore `scripts/agentcore_memory/server.py` from pre-M4 commit `4fdfaf6` or the prior health/status-only implementation.
2. Revert `agentcore-memory` `permitted_tools` in `contracts/bifrost-upstream-mcp-registry.json` to `memory_health`, `memory_status`.
3. Run `python scripts\bifrost\render_bifrost_config.py`.
4. Restart Bifrost via approved ops scripts.
5. IDE configs remain unchanged throughout rollback.

## Out of Scope Confirmed

- No M5 Cognee integration.
- No M6 LangGraph checkpoint tables.
- No dynamic Bifrost tool leases.
- No IDE MCP config edits.
