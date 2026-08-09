# Morning Readiness Live Snapshot — 2026-08-09 06:35 EDT

Source-only audit. No live Cursor, Bifrost, Swarm, database, scheduled-task, runtime, or IDE configuration mutation was performed.

## Repository state

- Repository: `@D:\github\agentcore-control-plane`
- Current pushed source status at capture: `efc3c95 update morning packet source status`
- Prior guardrail commits:
  - `d831e3b add final acceptance evidence preflight`
  - `935d239 harden sally acceptance placeholder gate`
  - `8d34059 add standalone sally acceptance prompt`

Inherited dirty/untracked worktree files remain outside this audit scope and were preserved.

## Read-only readiness result

Command:

```powershell
.\ops\bifrost\Test-AgentCoreMorningReadiness.ps1 -Json
```

Result:

- Status: `NOT_READY`
- Pass: `20`
- Warn: `0`
- Fail: `3`

Expected blockers:

| Gate | Status | Detail | Required operator phase |
| --- | --- | --- | --- |
| `cursor_global_mcp` | FAIL | expected only `agentcore-gateway`; found `agentcore-gateway,codegraph,repomix` | Phase 2 Cursor global MCP cleanup |
| `bifrost_config_drift` | FAIL | source hash differs from both live Bifrost config projections | Phase 3 Bifrost live rollout |
| `task_AgentCore-Bifrost-Watchdog` | FAIL | watchdog scheduled task missing | Phase 3 Bifrost live rollout |

Important passes:

- `bifrost_status_script`: `BIFROST_STATUS_OK`
- `bifrost_health`: HTTP 200
- `task_AgentCore-Bifrost-Gateway`: Running
- `swarmrecall_api_health`: HTTP 200
- `meilisearch_health`: HTTP 200
- `swarmclaw_health`: HTTP 200
- `swarmrecall_web`: HTTP 200
- `swarm_data_root`: `H:\SwarmData` exists
- `swarm_runtime_root`: `H:\SwarmRuntime` exists
- `swarm_backup_root`: `E:\SwarmBackups` exists
- `port_3300`, `port_3456`, `port_7700`, `port_8080`, `port_55433`, `port_65432`: listening on loopback
- `langgraph_topology`: fingerprint `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32`; nodes `15`

## Bifrost status

Command:

```powershell
.\ops\bifrost\Get-BifrostStatus.ps1
```

Result:

- Maintenance marker: absent
- Scheduled task: Running
- HTTP health: `status=ok`
- `agentcore_memory`: `10` tools as expected
- `agentcore_project_router`: `0` tools as expected
- `skills_hub`: `3` tools, meets minimum
- Total visible tools: `34`
- Final status: `BIFROST_STATUS_OK`

## Swarm endpoint spot check

Read-only endpoint checks:

| Endpoint | HTTP status | Response length |
| --- | --- | --- |
| `http://127.0.0.1:3300/api/v1/health` | 200 | 83 |
| `http://127.0.0.1:7700/health` | 200 | 22 |
| `http://127.0.0.1:3456/api/healthz` | 200 | 54 |
| `http://127.0.0.1:3400` | 200 | 36302 |

## Morning action order

1. Run the guarded morning helper without approval switches to reconfirm the same three blockers:

   ```powershell
   .\ops\bifrost\Invoke-AgentCoreMorningRollout.ps1
   ```

2. With explicit operator approval, run Cursor global MCP cleanup.
3. With explicit operator approval and elevation, run Bifrost live rollout so config projections match source and the watchdog task is installed.
4. Give Sally the standalone prompt:

   `@D:\github\agentcore-control-plane\docs\prompts\SALLY_FULL_SWARM_ACCEPTANCE_PROMPT_2026-08-09.md`

5. Validate Sally's final report:

   ```powershell
   .\ops\bifrost\Test-SallyAcceptanceEvidence.ps1 -Path '<path from Sally final acceptance>'
   ```

6. Run LangGraph and SwarmClaw canaries.
7. Run final evidence preflight:

   ```powershell
   .\ops\bifrost\Test-AgentCoreFinalAcceptanceEvidence.ps1 `
     -SallyAcceptancePath '<path from Sally final acceptance>' `
     -LangGraphCanaryPath '<path from LangGraph production canary>' `
     -SwarmClawCanaryPath '<path from Sally SwarmClaw autonomous canary>'
   ```

8. Generate the final restore-point report only after the preflight returns `SUMMARY status=READY`.

## Conclusion

The PC is source-prepared for the morning flow, but not live-ready yet. The three remaining blockers are known, expected, and mapped to the existing guarded approval phases. Sally's `ORCHESTRATOR_OK` remains orchestrator health evidence only.
