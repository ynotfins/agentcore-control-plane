# Bifrost Live Rollout And Runtime Acceptance — 2026-08-09

**Purpose:** turn the current source-ready state into a live production baseline without relying on chat history.

**Current authority:** `@D:\github\agentcore-control-plane\audits\OVERNIGHT_READINESS_STATUS_2026-08-09.md`

**Companion plan:** `@D:\github\agentcore-control-plane\docs\current\NEXT_GOAL_EXECUTION_PLAN_2026-08-09.md`

**Companion handoff:** `@D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_NEXT_GOAL_HANDOFF_2026-08-09.md`

## Boundary

This runbook is approval-gated. It documents the next live actions; it does not authorize an agent to perform them without the operator's explicit approval.

- AgentCore owns Bifrost, `agentcore-gateway`, `agentcore-memory`, PG18 exact evidence/recovery/policy, Context Engine, and LangGraph checkpoints.
- SwarmClaw/Sally owns Swarm runtime, agents, sessions, tasks, recovery, SwarmVault, and Swarm lifecycle.
- Neutral SwarmRecall is the shared semantic memory/context service only through bounded server-side adapters.
- Ordinary IDEs use one MCP entry: `agentcore-gateway`.
- Ordinary IDEs must not receive raw SwarmRecall, SwarmVault, Meilisearch, PostgreSQL, direct SQL, or duplicate memory MCP entries.

## Known pre-rollout state

The source hardening work is merged to `main`, but live Bifrost has not yet been rolled forward.

Required live drift to resolve:

1. `@C:\Users\ynotf\.cursor\mcp.json` contains extra global MCP entries and must be returned to only `agentcore-gateway`.
2. `@F:\AgentCore\runtime\bifrost\config.json` and `@F:\AgentCore\runtime\bifrost\config\config.json` do not yet match the merged source renderer.
3. `\AgentCore\AgentCore-Bifrost-Watchdog` is not installed live.
4. Sally's `ORCHESTRATOR_OK` is health evidence only; it is not full SwarmRecall, SwarmVault, and autonomous-team acceptance.

## Phase 1 — read-only preflight

Run from `@D:\github\agentcore-control-plane`.

Single-command gate:

```powershell
.\ops\bifrost\Test-AgentCoreMorningReadiness.ps1
```

The expected pre-approval status is `NOT_READY` if Cursor global MCP cleanup, Bifrost config rollout, or watchdog installation is still pending. Use `-Json` when another agent or script needs machine-readable output:

```powershell
.\ops\bifrost\Test-AgentCoreMorningReadiness.ps1 -Json
```

Expanded manual checks:

```powershell
git status --short --branch

.\ops\bifrost\Get-BifrostStatus.ps1

.\scripts\.venv\Scripts\python.exe -m agentcore workflow topology --json

Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway' -ErrorAction Stop |
  Select-Object TaskPath,TaskName,State

Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Watchdog' -ErrorAction SilentlyContinue |
  Select-Object TaskPath,TaskName,State

Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3300/api/v1/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:7700/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3456/api/healthz

netstat -ano | Select-String ':55433|:65432|:8080|:3300|:7700|:3456'
```

Stop if:

- `@H:\SwarmData` is not readable.
- Bifrost `:8080` is down and the operator has not approved restart.
- PG18 `:55433` is down.
- Swarm services are down and Sally has not been asked to own recovery.

## Phase 2 — approved Cursor global MCP cleanup

Do this only after the operator approves live Cursor config cleanup.

Expected final state:

- one server only;
- server name `agentcore-gateway`;
- URL `http://127.0.0.1:8080/mcp`;
- Authorization header uses `${env:BIFROST_MCP_VIRTUAL_KEY}`;
- no `codegraph`, `repomix`, `command-runner`, `memory-bank`, raw Recall, raw Vault, raw database, or project-local indexer entries.

Operator-approved dry run:

```powershell
.\ops\bifrost\Invoke-AgentCoreIdeGatewayCutover.ps1 `
  -RepoRoot ('D:' + '\github\agentcore-control-plane') `
  -EvidenceRoot ('F:' + '\AgentCore\runtime\bifrost\backups\cursor-mcp-dry-run') `
  -Clients cursor `
  -CursorConfigPath ('C:' + '\Users\ynotf\.cursor\mcp.json') `
  -DryRun
```

Operator-approved cleanup command:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$evidenceRoot = ('F:' + "\AgentCore\runtime\bifrost\backups\cursor-mcp-$stamp")

.\ops\bifrost\Invoke-AgentCoreIdeGatewayCutover.ps1 `
  -RepoRoot ('D:' + '\github\agentcore-control-plane') `
  -EvidenceRoot $evidenceRoot `
  -Clients cursor `
  -CursorConfigPath ('C:' + '\Users\ynotf\.cursor\mcp.json')
```

Post-cleanup validation:

```powershell
.\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

Stop if:

- the backup was not created;
- `agentcore-gateway` was missing before cleanup;
- the validator still fails for anything other than a known transient IDE discovery issue.

## Phase 3 — approved Bifrost live rollout

Do this only after the operator approves live Bifrost scheduled-task/config rollout.

Run in an elevated PowerShell from `@D:\github\agentcore-control-plane`.

```powershell
.\ops\bifrost\Install-AgentCoreBifrostGateway.ps1 `
  -RuntimeRoot ('F:' + '\AgentCore\runtime\bifrost') `
  -RepoRoot ('D:' + '\github\agentcore-control-plane')

.\ops\bifrost\Start-AgentCoreBifrostGateway.ps1 `
  -RuntimeRoot ('F:' + '\AgentCore\runtime\bifrost')

.\ops\bifrost\Get-BifrostStatus.ps1

.\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

The installer must:

- render and activate both live config projections:
  - `@F:\AgentCore\runtime\bifrost\config.json`
  - `@F:\AgentCore\runtime\bifrost\config\config.json`
- validate staged Bifrost config semantics before activation;
- create rollback backups for both config projections;
- preserve/replace scheduled tasks transactionally;
- install `\AgentCore\AgentCore-Bifrost-Watchdog`;
- enable Task Scheduler Operational logging;
- avoid printing secrets.

Stop if:

- installer privilege preflight fails;
- task backup/export fails;
- config semantic validation fails;
- rollback reports failure;
- `Get-BifrostStatus.ps1` does not return `BIFROST_STATUS_OK`;
- `Test-AgentCoreBifrostGateway.ps1` fails after Cursor global MCP cleanup.

## Phase 4 — Sally current Swarm acceptance

Give Sally this prompt after Bifrost/Cursor are stable, or earlier if Swarm recovery is the active blocker. Ask Sally to write the final report using the template at `@D:\github\agentcore-control-plane\docs\templates\SALLY_FULL_SWARM_ACCEPTANCE_REPORT_TEMPLATE_2026-08-09.md`.

```text
SALLY GOAL MODE — CURRENT SWARM RUNTIME READINESS AND AUTONOMOUS TEAM ACCEPTANCE

You are Sally, the SwarmClaw Orchestrator and authority for the Swarm ecosystem on this PC.

Goal:
Restore and certify the SwarmClaw ecosystem as production-ready for autonomous development work, with SwarmRecall as the neutral machine-wide semantic memory/context service and SwarmVault as the Swarm document/wiki/RAG corpus.

Authority boundaries:
- SwarmClaw/Sally owns Swarm runtime orchestration, agents, sessions, tasks, recovery, lifecycle, SwarmRecall operational use, and SwarmVault operational use.
- AgentCore owns Bifrost, agentcore-gateway, LangGraph, exact IDE evidence, project identity, recovery, and PG18 checkpoints.
- Do not edit AgentCore, Bifrost, LangGraph, Cursor, Codex, or IDE configs.
- Do not write to C: except normal Swarm app/runtime behavior already required by installed Swarm software.
- Do not move or redesign Swarm internals. Follow installed SwarmClaw/SwarmRecall/SwarmVault best practices and current installed-version behavior.

Required storage boundary:
- Current Swarm hot/runtime storage is `@H:\SwarmData` and `@H:\SwarmRuntime`.
- Swarm backups/archive should use `@E:\SwarmBackups` unless current Swarm authority says otherwise.
- Do not use LangGraph-owned or AgentCore-owned runtime paths for Swarm state.
- Do not write into AgentCore/Bifrost/LangGraph repos except read-only evidence inspection if needed.

Acceptance evidence required:
1. Current service table:
   - SwarmClaw UI/API health
   - SwarmRecall health
   - SwarmVault health
   - Meilisearch health
   - Swarm PostgreSQL/listener health
   Include endpoint, status, and timestamp.

2. SwarmRecall canary:
   - Write one harmless test fact/event through the supported Swarm path.
   - Read it back.
   - Prove exact match.
   - Do not expose raw credentials.

3. SwarmVault canary:
   - Confirm source count or corpus status.
   - Run a small search/context-pack test.
   - Report token/context-pack size if available.

4. Autonomous team canary:
   - Run a small delegated Swarm team task using Sally -> Builder -> QA/Reviewer or the installed recommended equivalent.
   - The task must be harmless and bounded.
   - Prove task creation, delegation, result, review, and completion.

5. Drift and boundary proof:
   - Prove no writes were made to AgentCore, Bifrost, LangGraph, or IDE configs.
   - Prove Swarm runtime paths stayed under the approved Swarm roots.
   - List any residuals clearly.

6. Restore point:
   - Create a Swarm-side restore/backup evidence point using the installed Swarm best-practice mechanism.
   - Report exact backup/restore-point path and files, without secrets.

Final output:
- PASS / FAIL / PARTIAL.
- Exact evidence paths.
- What is ready now.
- What still needs operator action.
- Whether a SwarmClaw restart is required.
- Whether a new Sally chat is required or this chat can continue safely.
```

Accept Sally's result only if it includes evidence for SwarmRecall, SwarmVault, autonomous delegation, and no-cross-write boundaries. `ORCHESTRATOR_OK` alone is not enough.

After Sally provides the final report path, run the read-only structural gate from `@D:\github\agentcore-control-plane`:

```powershell
.\ops\bifrost\Test-SallyAcceptanceEvidence.ps1 -Path '<path from Sally final acceptance>'
```

This gate checks evidence coverage and obvious secret leakage only. It does not replace Sally's Swarm-owned runtime validation or operator review.

## Phase 5 — runtime canaries

Run only after Cursor cleanup, Bifrost rollout, and Sally acceptance are green or explicitly waived.

LangGraph production canary:

```powershell
Set-Location -LiteralPath ('D:' + '\github\agentcore-control-plane\scripts')
.\.venv\Scripts\python.exe -m agentcore workflow topology --json
.\.venv\Scripts\python.exe -m agentcore workflow start --help
```

Do not start a real production project until the operator supplies the project goal and acceptance file.

SwarmClaw canary:

- run through Sally;
- keep all Swarm writes inside Swarm-owned roots;
- require no AgentCore PG18, Bifrost, LangGraph checkpoint, or IDE profile writes.

## Phase 6 — closeout restore point

Create a final evidence report after all accepted phases.

Report generator:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outFile = "audits\RESTORE_POINT_RUNTIME_ACCEPTANCE_$stamp.md"

.\ops\bifrost\New-AgentCoreRestorePointReport.ps1 `
  -SallyAcceptancePath '<path from Sally final acceptance>' `
  -LangGraphCanaryPath '<path from LangGraph production canary>' `
  -SwarmClawCanaryPath '<path from Sally SwarmClaw autonomous canary>' `
  -OutFile $outFile
```

The generator defaults to stdout if `-OutFile` is omitted. Do not commit a generated restore-point report unless morning readiness is `READY` and all three acceptance evidence paths are present.

Required contents:

- current commit SHA for `@D:\github\agentcore-control-plane`;
- Bifrost config hashes for both live projections;
- scheduled-task status for gateway and watchdog;
- `Get-BifrostStatus.ps1` result;
- `Test-AgentCoreBifrostGateway.ps1` result;
- Sally full acceptance result path;
- LangGraph canary result path;
- SwarmClaw canary result path;
- residuals and assigned owners.

Do not mark the workstation production-ready until every item is backed by current evidence, not memory or prior chat.
