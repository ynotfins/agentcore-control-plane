# Morning Readiness After Cursor Cleanup — 2026-08-09 15:26 EDT

**Mode:** approved live Cursor global MCP cleanup plus read-only postflight.  
**Source head before evidence write:** `3700c89 isolate morning rollout child exit codes`  
**Result:** `NOT_READY` for production runtime work until approved Bifrost live rollout runs.

## Approved action

Operator approved live cleanup of:

`@C:\Users\ynotf\.cursor\mcp.json`

using the repo-owned cursor-only cutover helper, with timestamped backup/evidence under:

`F:\AgentCore\runtime\bifrost\backups`

## Cursor global MCP result

`ops\bifrost\Invoke-AgentCoreMorningRollout.ps1 -ApproveCursorCleanup` ran.

Evidence directory:

`F:\AgentCore\runtime\bifrost\backups\cursor-mcp-20260809-152432`

Postflight:

- Cursor global MCP has exactly one server entry.
- Cursor global MCP contains `agentcore-gateway`.
- Cursor global MCP endpoint matches gateway.
- Cursor global MCP uses the environment-variable virtual-key placeholder.
- Cursor global MCP has no obvious secret literal.
- Full `Test-AgentCoreBifrostGateway.ps1` postflight returned `RESULT: PASSED`.

## Project-level MCP preservation

The `@D:\github\nfa-alerts-enterprise\.cursor\mcp.json` project-level MCP config was inspected after global cleanup and was not removed by AgentCore.

Observed project-level MCP servers:

1. `mcp-codebase-search`
2. `code-search`
3. `codebase-memory`
4. `claude-context`
5. `codegraph`
6. `repomix`

Independent stdio handshake smoke tests for the two newly moved project-level servers:

- `codegraph` version `1.5.0`: initialize OK; `tools/list` OK; 1 tool: `codegraph_explore`.
- `repomix` version `1.18.0`: initialize OK; `tools/list` OK; 6 tools: `pack_codebase`, `read_repomix_output`, `grep_repomix_output`, `pack_remote_repository`, `generate_skill`, `attach_packed_output`.

## Readiness summary after cleanup

`ops\bifrost\Test-AgentCoreMorningReadiness.ps1 -Json` returned:

- `status`: `NOT_READY`
- `pass`: `21`
- `warn`: `0`
- `fail`: `2`

## Remaining blockers

1. `bifrost_config_drift`
   - Source config hash differs from live/projection hash.
   - Required phase: approved Bifrost live rollout through the governed installer.

2. `task_AgentCore-Bifrost-Watchdog`
   - Scheduled task not installed live.
   - Required phase: approved Bifrost live rollout through the governed installer.

## Still pending after Bifrost rollout

- Sally full SwarmRecall/SwarmVault/autonomous-runtime acceptance.
- LangGraph production canary.
- SwarmClaw autonomous canary through Sally.
- Final restore-point evidence preflight.
