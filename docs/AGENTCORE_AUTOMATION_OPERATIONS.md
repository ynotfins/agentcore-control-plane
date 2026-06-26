# AgentCore Automation Operations

Generated: 2026-06-26

This document records the current automation and service-ownership model for AgentCore local memory, database, RAG, MCP drift, and context-window stabilization.

## Runtime Ownership

SwarmRecall is no longer intentionally hosted by Cursor background terminals.

Current service owners:

- `\AgentCore\SwarmRecallMeilisearch`
  - launches `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe`
  - binds `127.0.0.1:7700`
  - stores data under `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data`
  - uses `MEILI_MASTER_KEY` through the child environment, not command-line args
- `\AgentCore\SwarmRecallApi`
  - launches `D:\github\vendor\swarm\swarmrecall\packages\api\dist\index.js`
  - binds `127.0.0.1:3300`
  - uses the native PostgreSQL `swarmrecall` database on `127.0.0.1:55432`

Both scheduled tasks are current-user logon tasks with limited run level. Highest-runlevel registration is not required for the local-only runtime and failed from the non-elevated Codex inner shell.

## Operational Scripts

- `ops\Start-AgentCoreSwarmRecallComponent.ps1`
  - idempotently starts one SwarmRecall component
  - exits cleanly if the approved loopback listener is already healthy
- `ops\Install-AgentCoreSwarmRecallScheduledTasks.ps1`
  - registers or updates the AgentCore SwarmRecall scheduled tasks
  - sets component-specific working directories
- `ops\Stop-AgentCoreSwarmRecallRuntime.ps1`
  - stops only process command lines matching the approved SwarmRecall config
- `ops\Test-AgentCoreRuntimeSuite.ps1`
  - validates Postgres readiness, SwarmRecall, and SwarmVault

## Validation Commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmRecall.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmVault.ps1
powershell -ExecutionPolicy Bypass -File D:\MCP-Control-Plane\validators\validate-control-plane.ps1
powershell -ExecutionPolicy Bypass -File D:\Codex_Managed\scripts\global-memory-system.ps1 -Mode validate
```

## Codex Automations

Active stabilization monitors:

- `agentcore-context-window-optimizer`
  - audits context-window pressure, MCP duplication, and tool-routing drift
- `agentcore-pgvector-database-monitor`
  - checks PostgreSQL/pgvector readiness, backup posture, WAL/archive status, and disk pressure
- `agentcore-rag-runtime-monitor`
  - checks SwarmRecall, Meilisearch, SwarmVault, local-only posture, and service restarts
- `agentcore-mcp-drift-monitor`
  - checks MCP governance, retired server names, gateway routing, and drift prevention

Initial cadence is every two hours for stabilization. After several clean cycles, reduce to a lower cadence.

## Boundaries

- `global-memory-gateway` remains the governed cross-project memory writer.
- If a currently running Codex thread still reports `fe_sendauth: no password supplied` from `global-memory-gateway`, restart Codex so the MCP process reloads the corrected environment contract. Do not bypass the gateway with ad hoc direct SQL for normal memory writes.
- SwarmRecall is local-only memory/search/runtime support and does not replace the gateway.
- SwarmVault is local knowledge/wiki/RAG support and does not replace the gateway.
- Live IDE MCP config rollout must go through control-plane validation; do not hand-edit every IDE config independently.
- Do not store secrets in docs, reports, memory, prompts, screenshots, or process command lines.
