# Foundation Health Hardening — Phase 6

**Date:** 2026-07-25

## One-command owners

| Component | Owner / command |
| --- | --- |
| Bifrost status | `pwsh -File D:\github\agentcore-control-plane\ops\bifrost\Get-BifrostStatus.ps1` |
| Foundation health | `pwsh -File D:\github\agentcore-control-plane\ops\health-check.ps1` |
| Bifrost log rotation | `pwsh -File D:\github\agentcore-control-plane\ops\bifrost\Rotate-BifrostLogs.ps1` |
| Bifrost start/stop | scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` via existing `Start-/Stop-AgentCoreBifrostGateway.ps1` |

## Verified 2026-07-25

| Check | Result |
| --- | --- |
| `AgentCore-PostgreSQL18` | Running / Automatic; port `127.0.0.1:55433` open |
| Bifrost scheduled task | Running; launches `ops/bifrost/Launch-AgentCoreBifrostGateway.ps1` |
| Bifrost `/health` | ok |
| Tool groups | memory=10, router=4, skills_hub=3 (total tools observed 161) |
| Skills-Hub `start.mjs` | present at `H:\AgentRuntime\skills-hub\start.mjs` |
| `LANGSMITH_TRACING` | set User-scope `false` |
| `LANGGRAPH_CLI_NO_ANALYTICS` | set User-scope `1` |
| `E:\DatabaseBackups` | present |
| `G:\DatabaseBackups` | **MISSING** (WARN — second copy not present) |
| Latest restore-test artifact | `audits/M5/pg18-restore-test-20260724-033001.json` |
| OS reboot acceptance | **Not run** this phase (operator-gated) |

## Health script run

`ops/health-check.ps1` → `AGENTCORE_HEALTH_OK`  
`ops/bifrost/Get-BifrostStatus.ps1` → `BIFROST_STATUS_OK`

## Operator follow-ups

1. Create/sync second backup root `G:\DatabaseBackups` if drive available.
2. Reboot once and confirm PG18 Automatic + Bifrost logon task recover (document result).
3. Optionally schedule `Rotate-BifrostLogs.ps1` daily.

**Signal:** `FOUNDATION_HEALTH_SCRIPTS_LIVE`
