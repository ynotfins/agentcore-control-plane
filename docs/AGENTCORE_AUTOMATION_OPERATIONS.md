# AgentCore Automation Operations

Generated: 2026-06-27

This document records the current automation and service-ownership model for AgentCore local memory, database, RAG, MCP drift, and context-window stabilization.

## Runtime Ownership

SwarmRecall is no longer intentionally hosted by Cursor background terminals.

Current service owners:

- `\AgentCore\PostgresRuntime`
  - launches `D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped`
  - owns cold-boot recovery for native PostgreSQL on `127.0.0.1:55432`
  - keeps the canonical `agent_core` and `swarmrecall` databases available before dependent memory runtimes validate as healthy
- `\AgentCore\SwarmRecallMeilisearch`
  - launches `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe`
  - binds `127.0.0.1:7700`
  - stores data under `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data`
  - uses `MEILI_MASTER_KEY` through the child environment, not command-line args
- `\AgentCore\SwarmRecallApi`
  - launches `D:\github\vendor\swarm\swarmrecall\packages\api\dist\index.js`
  - binds `127.0.0.1:3300`
  - uses the native PostgreSQL `swarmrecall` database on `127.0.0.1:55432`

These runtime scheduled tasks are current-user logon tasks with limited run level. Highest-runlevel registration is not required for the local-only runtime and failed from the non-elevated Codex inner shell.

## Operational Scripts

- `ops\Start-AgentCoreSwarmRecallComponent.ps1`
  - idempotently starts one SwarmRecall component
  - exits cleanly if the approved loopback listener is already healthy
  - gates API startup on PostgreSQL readiness so an API listener is not treated as healthy while `127.0.0.1:55432` is unavailable
- `ops\Install-AgentCoreSwarmRecallScheduledTasks.ps1`
  - registers or updates the AgentCore SwarmRecall scheduled tasks
  - sets component-specific working directories
- `ops\Install-AgentCoreOperationalScheduledTasks.ps1`
  - re-homes the remaining AgentCore scheduled tasks into the source-controlled repo
  - registers the projection and context-fabric readiness tasks
- `ops\Stop-AgentCoreSwarmRecallRuntime.ps1`
  - stops only process command lines matching the approved SwarmRecall config
- `ops\Test-AgentCoreRuntimeSuite.ps1`
  - validates Postgres readiness, SwarmRecall, SwarmVault, memory projection, and context-fabric readiness
  - add `-IncludeLiveClientAdoption` when you need the full rollout gate, including proof that clients restarted onto the governed config set
- `ops\Test-AgentCoreLiveClientAdoption.ps1`
  - validates live client config adoption for Codex, Cursor, Open Interpreter, OpenClaw, MiniMax, and Mavis
  - checks required governed servers, forbidden retired servers, and whether the running client processes were started after config rollout
- `ops\Rebuild-AgentCoreSwarmVaultProjection.ps1`
  - creates a rollback backup of current AgentCore projection-derived SwarmVault files
  - resets only the SwarmVault side of projection state
  - replays the curated projection from canonical Postgres memory into SwarmVault
- `ops\Test-AgentCoreContextFabricReadiness.ps1`
  - fails if `.context-fabric` exists outside a Git repo root
  - reports repo-scoped context-fabric roots that remain valid
- `ops\Repair-AgentCoreContextFabricState.ps1`
  - moves invalid non-repo `.context-fabric` state into a rollback backup
- `ops\Test-AgentCoreContextWindowPolicy.ps1`
  - validates the master MCP contract against the governed memory model and client server budgets
  - reports live client config drift when parseable without replacing the live adoption validator
- `ops\Test-AgentCorePluginExtensionSecurity.ps1`
  - scans user-owned IDE plugin, extension, skill, and MCP-wrapper roots for hostile or unexpected script patterns
  - writes report-only evidence under `artifacts\plugin-extension-security`

## ChaosCentral Workhorse

ChaosCentral is the local PC inventory and evidence workhorse:

- workhorse root: `D:\ChaosCentral-Current-Build`
- authority contract: `contracts\chaoscentral-workhorse-contract.json`
- integration doc: `docs\CHAOSCENTRAL_WORKHORSE_INTEGRATION.md`

Refresh and validate ChaosCentral before using its evidence to update AgentCore authority docs:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\ChaosCentral-Current-Build\scripts\Refresh-ChaosCentralInventory.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\ChaosCentral-Current-Build\scripts\Test-ChaosCentralInventory.ps1
```

## Validation Commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1 -IncludeLiveClientAdoption
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmRecall.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmVault.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreContextWindowPolicy.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCorePluginExtensionSecurity.ps1
powershell -ExecutionPolicy Bypass -File D:\MCP-Control-Plane\validators\validate-control-plane.ps1
powershell -ExecutionPolicy Bypass -File D:\Codex_Managed\scripts\global-memory-system.ps1 -Mode validate
```

## Codex Automations

Active stabilization monitors:

- `agentcore-context-window-optimizer`
  - audits context-window pressure, MCP duplication, and tool-routing drift
  - runs `ops\Test-AgentCoreContextWindowPolicy.ps1` and pushes toward larger effective context by reducing unnecessary direct tool exposure
- `agentcore-plugin-and-extension-security-monitor`
  - scans plugin, extension, skill, and MCP-wrapper roots for hostile indicators and unexpected recent changes
  - report-only by default; no automatic deletion, quarantine, or rewrite
- `agentcore-pgvector-database-monitor`
  - checks PostgreSQL/pgvector readiness, backup posture, WAL/archive status, and disk pressure
- `agentcore-rag-runtime-monitor`
  - checks SwarmRecall, Meilisearch, SwarmVault, local-only posture, and service restarts
- `agentcore-mcp-drift-monitor`
  - checks MCP governance, retired server names, gateway routing, and drift prevention
- `agentcore-memory-projection-monitor`
  - checks projector backlog, failed sync state, and downstream SwarmRecall/SwarmVault materialization
- `agentcore-context-fabric-readiness-monitor`
  - checks repo-scoped context-fabric readiness and flags invalid `.context-fabric` state outside Git roots
- `agentcore-live-client-adoption-monitor`
  - checks whether governed MCP config changes were actually adopted by live Codex, Cursor, Open Interpreter, OpenClaw, MiniMax, and Mavis processes
- `agentcore-chaoscentral-spec-sync`
  - refreshes ChaosCentral evidence and updates AgentCore authority docs when live machine facts change
- `agentcore-daily-drift-sync`
  - runs the source-controlled drift synchronization job on the same daily cadence as the legacy Windows task
- `agentcore-nightly-backup`
  - runs the source-controlled pgvector base-backup job on the same nightly cadence as the legacy Windows task
- `agentcore-nightly-restore-test`
  - runs the source-controlled restore validation job on the same nightly cadence as the legacy Windows task
- `agentcore-weekly-maintenance`
  - runs the source-controlled maintenance job on the same weekly cadence as the legacy Windows task

Initial cadence is every two hours for stabilization. After several clean cycles, reduce to a lower cadence.

## Windows Scheduled Tasks

Source-controlled scheduled task installer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Install-AgentCoreOperationalScheduledTasks.ps1
```

Managed tasks:

- `\AgentCore\PostgresRuntime`
- `\AgentCore\DailyDriftCheck`
- `\AgentCore\NightlyBackup`
- `\AgentCore\NightlyRestoreTest`
- `\AgentCore\WeeklyMaintenance`
- `\AgentCore\SwarmRecallApi`
- `\AgentCore\SwarmRecallMeilisearch`

Current ownership note:

- `\AgentCore\PostgresRuntime`, `\AgentCore\SwarmRecallApi`, and `\AgentCore\SwarmRecallMeilisearch` are directly source-controlled runtime ownership tasks.
- The remaining legacy Windows tasks may still point at `D:\MCP-Control-Plane\ops\...` until elevated re-registration is approved.
- Those live-op task entrypoints are now thin delegates into `D:\github\agentcore-control-plane\ops\...`, so they execute current source-controlled logic.
- Codex cron automations also mirror the drift, backup, restore-test, and maintenance jobs, so elevated Task Scheduler migration is no longer a functional prerequisite for operational coverage.
- `agentcore-memory-projection-monitor` and `agentcore-context-fabric-readiness-monitor` are currently Codex automations, not observed `\AgentCore\...` Windows scheduled tasks in the latest ChaosCentral machine evidence.

## Boundaries

- `global-memory-gateway` remains the governed cross-project memory writer.
- If a currently running Codex thread still reports `fe_sendauth: no password supplied` from `global-memory-gateway`, restart Codex so the MCP process reloads the corrected environment contract. Do not bypass the gateway with ad hoc direct SQL for normal memory writes.
- SwarmRecall is local-only memory/search/runtime support and does not replace the gateway.
- SwarmVault is local knowledge/wiki/RAG support and does not replace the gateway.
- SwarmVault receives only the curated, governed projection subset. It does not mirror every canonical memory row.
- If SwarmVault source pages drift from projection state, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Rebuild-AgentCoreSwarmVaultProjection.ps1
```

- Full rollout proof requires a live client restart pass after config changes. Use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreLiveClientAdoption.ps1
```

- Live IDE MCP config rollout must go through control-plane validation; do not hand-edit every IDE config independently.
- Do not store secrets in docs, reports, memory, prompts, screenshots, or process command lines.
