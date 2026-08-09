# Morning Readiness Live Snapshot — 2026-08-09 06:44 EDT

**Mode:** read-only evidence refresh.
**Source head:** `e7f4925 link morning pointer in readiness plan`
**Result:** `NOT_READY` for production runtime work until approved live phases run.

## Readiness summary

`ops\bifrost\Test-AgentCoreMorningReadiness.ps1 -Json` returned:

- `status`: `NOT_READY`
- `pass`: `20`
- `warn`: `0`
- `fail`: `3`

## Expected blockers still present

1. `cursor_global_mcp`
   - Expected: only `agentcore-gateway`.
   - Observed: `agentcore-gateway`, `codegraph`, `repomix`.
   - Required phase: approved Cursor global MCP cleanup.

2. `bifrost_config_drift`
   - Source config hash differs from live/projection hash.
   - Required phase: approved Bifrost live rollout through the governed installer.

3. `task_AgentCore-Bifrost-Watchdog`
   - Scheduled task not installed live.
   - Required phase: approved Bifrost live rollout through the governed installer.

## Passing live evidence

- Bifrost gateway scheduled task is running.
- Bifrost `/health` returns HTTP 200.
- `agentcore-memory` exposes the expected 10 tools.
- `agentcore_project_router` exposes 0 tools.
- Skills Hub exposes at least the expected minimum tools.
- SwarmRecall API health returns HTTP 200 on loopback.
- Meilisearch health returns HTTP 200 on loopback.
- SwarmClaw health returns HTTP 200 on loopback.
- Swarm UI/web endpoint returns HTTP 200 on loopback.
- `H:\SwarmData` exists.
- `H:\SwarmRuntime` exists.
- `E:\SwarmBackups` exists.
- `F:\AgentCore` exists.
- `F:\PostgreSQL18` exists.
- Ports listening on `127.0.0.1`: `3300`, `3456`, `7700`, `8080`, `55433`, `65432`.
- LangGraph topology fingerprint remains `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` with 15 nodes.

## Sally/SwarmClaw health evidence

Operator reported Sally returned:

```text
Canary passed cleanly. No tasks queued, no active schedules, all agents idle. System is healthy.

ORCHESTRATOR_OK
```

This is SwarmClaw orchestrator health evidence only. It is not full SwarmRecall, SwarmVault, or autonomous-runtime acceptance. Full acceptance must still use:

`@D:\github\agentcore-control-plane\docs\prompts\SALLY_FULL_SWARM_ACCEPTANCE_PROMPT_2026-08-09.md`

and pass:

```powershell
.\ops\bifrost\Test-SallyAcceptanceEvidence.ps1 -Path '<path from Sally final acceptance>'
```

## Operator start point

Start the morning flow from:

`@D:\github\agentcore-control-plane\docs\current\MORNING_START_HERE_2026-08-09.md`

