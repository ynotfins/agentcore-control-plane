# Morning Readiness Recheck — AgentCore / Bifrost / Swarm

**Timestamp:** 2026-08-09T09:52Z  
**Scope:** read-only recheck from `@D:\github\agentcore-control-plane` after adding the live rollout runbook.  
**Mutation statement:** no live Cursor, Bifrost scheduled task, Bifrost runtime config, Swarm runtime, database, or IDE configuration was modified by this recheck.

## Source state

| Item | Result |
| --- | --- |
| Repository branch | `main...origin/main` |
| Latest task-owned commit before this audit | `c343d95 add bifrost live rollout runbook` |
| Inherited dirty state | still present; not touched or staged |
| Live rollout runbook | `@D:\github\agentcore-control-plane\docs\operations\BIFROST_LIVE_ROLLOUT_AND_RUNTIME_ACCEPTANCE_2026-08-09.md` |

Inherited dirty/untracked work still exists in M6/M7/M8 summaries, `scripts\agentcore_workflow\requirements.txt`, `.agentcore\rollback\`, `.agents\skills\`, Langfuse/IDE profile work, `tools\caveman-docs\`, and other pre-existing artifacts. This audit does not classify or clean those files.

## Live evidence

| Area | Command / probe | Result |
| --- | --- | --- |
| Bifrost status | `.\ops\bifrost\Get-BifrostStatus.ps1` | `BIFROST_STATUS_OK`; maintenance marker absent; task Running; 10 `agentcore-memory` tools; 0 ordinary project-router tools; 34 total tools |
| Bifrost health | `GET http://127.0.0.1:8080/health` | HTTP 200, `status:ok`, `db_pings:ok` |
| SwarmRecall API | `GET http://127.0.0.1:3300/api/v1/health` | HTTP 200, `status:ok`, database service true |
| Meilisearch | `GET http://127.0.0.1:7700/health` | HTTP 200, `status:available` |
| SwarmClaw | `GET http://127.0.0.1:3456/api/healthz` | HTTP 200, `ok:true`, `service:swarmclaw` |
| SwarmRecall web | `GET http://127.0.0.1:3400` | HTTP 200, HTML served |
| LangGraph topology | `.\.venv\Scripts\python.exe -m agentcore workflow topology --json` from `@D:\github\agentcore-control-plane\scripts` | fingerprint `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32`; 15 nodes; production PostgresSaver |
| Loopback listeners | `netstat` filtered for key ports | `:3300`, `:3456`, `:7700`, `:8080`, `:55433`, and `:65432` listening on `127.0.0.1` |
| Required roots | `Test-Path` | `@H:\SwarmData`, `@H:\SwarmRuntime`, `@E:\SwarmBackups`, `@F:\AgentCore`, `@F:\AgentCore\runtime\bifrost`, and `@F:\PostgreSQL18` exist |

## Current blockers

### 1. Cursor global MCP is still dirty

Read-only shape check of `@C:\Users\ynotf\.cursor\mcp.json`:

```text
CURSOR_MCP exists=true count=3 names=agentcore-gateway,codegraph,repomix
```

Full gateway validator result:

```text
FAIL  Cursor global MCP has exactly one server entry
RESULT: FAILED
```

All other visible `Test-AgentCoreBifrostGateway.ps1` checks passed, including authenticated MCP initialize, authenticated `tools/list`, 34 tools returned, expected Code Mode meta-tools, expected active builder tool prefixes, and forbidden `swarm` / `postgres` / `psql` / `whole_drive` / `bifrost_admin` tool patterns absent.

Required action: operator approval for live cleanup of `@C:\Users\ynotf\.cursor\mcp.json` back to the single `agentcore-gateway` entry, preserving a timestamped backup.

### 2. Bifrost source-to-live config drift remains

Current hashes:

| Path | SHA-256 | Bytes |
| --- | --- | --- |
| `@D:\github\agentcore-control-plane\renderers\bifrost\config.json` | `062EF7694DF7316D60379E020328696A6D861BF699AB01113508274F8089D3E0` | 24485 |
| `@F:\AgentCore\runtime\bifrost\config.json` | `AF5797CF0E62922AAABD5E8C9259C48452B9213622E21603A9FA1795626717F5` | 19805 |
| `@F:\AgentCore\runtime\bifrost\config\config.json` | `AF5797CF0E62922AAABD5E8C9259C48452B9213622E21603A9FA1795626717F5` | 19805 |

Required action: operator approval for governed Bifrost live rollout through `Install-AgentCoreBifrostGateway.ps1` and postflight validation.

### 3. Bifrost watchdog is not installed live

Task Scheduler evidence:

```text
TASK AgentCore-Bifrost-Gateway state=Running lastResult=2147946720 lastRun=8/8/2026 2:49:02 PM
TASK AgentCore-Bifrost-Watchdog missing_or_error=No matching MSFT_ScheduledTask objects found
```

Required action: install `\AgentCore\AgentCore-Bifrost-Watchdog` through the governed Bifrost installer during approved live rollout.

### 4. Sally/Swarm evidence is health-only

Operator-provided Sally result:

```text
Canary passed cleanly. No tasks queued, no active schedules, all agents idle. System is healthy.

ORCHESTRATOR_OK
```

Treat this as SwarmClaw orchestrator health evidence only. It does not prove:

- SwarmRecall write/read/search canary;
- SwarmVault search/context-pack canary;
- autonomous Builder -> QA/Reviewer team canary;
- no-cross-write proof against AgentCore/Bifrost/LangGraph/IDE configs;
- current Swarm restore point.

Required action: give Sally the full acceptance prompt in `@D:\github\agentcore-control-plane\docs\operations\BIFROST_LIVE_ROLLOUT_AND_RUNTIME_ACCEPTANCE_2026-08-09.md`.

## Morning execution order

1. Approve Cursor global MCP cleanup.
2. Run `.\ops\bifrost\Test-AgentCoreBifrostGateway.ps1`; expected blocker should clear.
3. Approve governed Bifrost live rollout.
4. Run Bifrost postflight: `Get-BifrostStatus.ps1` and `Test-AgentCoreBifrostGateway.ps1`.
5. Run Sally full Swarm acceptance.
6. Run LangGraph production canary.
7. Run SwarmClaw autonomous canary through Sally.
8. Create final restore-point report.

## Readiness decision

**Status: source-ready, live-approval-gated.**

The machine is not yet fully production-ready for autonomous project execution because the current evidence still shows:

- Cursor global MCP has duplicate project/indexer entries;
- Bifrost live config/watchdog rollout is pending;
- Sally has only provided orchestrator health, not full SwarmRecall/SwarmVault/autonomous-runtime acceptance.

No further repo-only documentation is required before asking the operator for the live approvals above.
