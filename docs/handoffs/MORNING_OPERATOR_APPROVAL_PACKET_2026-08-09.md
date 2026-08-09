# Morning Operator Approval Packet — 2026-08-09

**Purpose:** concise execution packet for moving from source-ready to live-ready.

**Full runbook:** `@D:\github\agentcore-control-plane\docs\operations\BIFROST_LIVE_ROLLOUT_AND_RUNTIME_ACCEPTANCE_2026-08-09.md`

**Current source-only status:** pushed through commit `69c0e1a add restore point report generator`.

## Current known state

- Bifrost is currently healthy, but live runtime config has not been rolled forward to the merged source config.
- Cursor global MCP currently has extra global entries and must be returned to only `agentcore-gateway`.
- `\AgentCore\AgentCore-Bifrost-Watchdog` is not installed live.
- Sally returned `ORCHESTRATOR_OK`; treat that as orchestrator health only, not full SwarmRecall/SwarmVault/autonomous-team acceptance.
- No live Cursor, Bifrost scheduled task, Bifrost runtime config, Swarm runtime, database, or IDE configuration mutation has been performed by this packet.

## First command after operator returns

Run from `@D:\github\agentcore-control-plane`:

```powershell
.\ops\bifrost\Invoke-AgentCoreMorningRollout.ps1
```

Expected before approvals:

```text
SUMMARY status=NOT_READY
```

Expected failures before approvals:

1. `cursor_global_mcp`
2. `bifrost_config_drift`
3. `task_AgentCore-Bifrost-Watchdog`

Any additional failure is a stop condition.

The helper above is read-only unless explicit approval switches are supplied.
For direct checker output only, run:

```powershell
.\ops\bifrost\Test-AgentCoreMorningReadiness.ps1
```

## Approval 1 — Cursor global MCP cleanup

Approve this exact live action:

```text
I approve live cleanup of @C:\Users\ynotf\.cursor\mcp.json back to the single agentcore-gateway entry, using the repo-owned cursor-only cutover helper, with timestamped backup/evidence under F:\AgentCore\runtime\bifrost\backups.
```

After approval, run from `@D:\github\agentcore-control-plane`:

```powershell
.\ops\bifrost\Invoke-AgentCoreMorningRollout.ps1 -ApproveCursorCleanup
```

Equivalent expanded command:

```powershell
.\ops\bifrost\Invoke-AgentCoreIdeGatewayCutover.ps1 `
  -RepoRoot ('D:' + '\github\agentcore-control-plane') `
  -EvidenceRoot ('F:' + "\AgentCore\runtime\bifrost\backups\cursor-mcp-$(Get-Date -Format 'yyyyMMdd-HHmmss')") `
  -Clients cursor `
  -CursorConfigPath ('C:' + '\Users\ynotf\.cursor\mcp.json')

.\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

Pass condition:

- `Test-AgentCoreBifrostGateway.ps1` passes.
- Cursor global MCP has exactly one server: `agentcore-gateway`.

## Approval 2 — Bifrost live rollout

Approve this exact live action:

```text
I approve governed Bifrost live rollout from @D:\github\agentcore-control-plane main to @F:\AgentCore\runtime\bifrost, including both config projections, AgentCore-Bifrost-Watchdog scheduled task installation, Task Scheduler Operational logging enablement, rollback backups, and postflight validation.
```

Run in elevated PowerShell from `@D:\github\agentcore-control-plane`:

```powershell
.\ops\bifrost\Invoke-AgentCoreMorningRollout.ps1 -ApproveBifrostRollout
```

Equivalent expanded commands:

```powershell
.\ops\bifrost\Install-AgentCoreBifrostGateway.ps1 `
  -RuntimeRoot ('F:' + '\AgentCore\runtime\bifrost') `
  -RepoRoot ('D:' + '\github\agentcore-control-plane')

.\ops\bifrost\Start-AgentCoreBifrostGateway.ps1 `
  -RuntimeRoot ('F:' + '\AgentCore\runtime\bifrost')

.\ops\bifrost\Get-BifrostStatus.ps1
.\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
.\ops\bifrost\Test-AgentCoreMorningReadiness.ps1
```

Pass condition:

- `Get-BifrostStatus.ps1` returns `BIFROST_STATUS_OK`.
- `Test-AgentCoreBifrostGateway.ps1` passes.
- `Test-AgentCoreMorningReadiness.ps1` has no AgentCore-side Bifrost/Cursor failures.

## Sally full Swarm acceptance prompt

Give Sally the Phase 4 prompt from the full runbook:

`@D:\github\agentcore-control-plane\docs\operations\BIFROST_LIVE_ROLLOUT_AND_RUNTIME_ACCEPTANCE_2026-08-09.md`

Tell Sally to write the final report using this template:

`@D:\github\agentcore-control-plane\docs\templates\SALLY_FULL_SWARM_ACCEPTANCE_REPORT_TEMPLATE_2026-08-09.md`

Accept Sally's result only if it includes:

- Swarm service table;
- SwarmRecall write/read/search canary;
- SwarmVault search/context-pack canary;
- autonomous team canary;
- no AgentCore/Bifrost/LangGraph/IDE writes;
- Swarm-side restore point path.

`ORCHESTRATOR_OK` alone is not enough.

After Sally gives the final report path, run the read-only structural gate from `@D:\github\agentcore-control-plane`:

```powershell
.\ops\bifrost\Test-SallyAcceptanceEvidence.ps1 -Path '<path from Sally final acceptance>'
```

Only continue to runtime canaries if the gate returns `SUMMARY status=READY`. This checks report completeness and obvious secret leakage; it does not replace Sally's Swarm-owned validation.

## Runtime canaries

LangGraph canary must use:

```powershell
Set-Location -LiteralPath ('D:' + '\github\agentcore-control-plane\scripts')
.\.venv\Scripts\python.exe -m agentcore workflow topology --json
```

Do not start a real production project until the project goal and acceptance file are supplied by the operator.

SwarmClaw canary must run through Sally and keep writes inside Swarm-owned roots.

## Final restore-point report

After all acceptance evidence exists, run from `@D:\github\agentcore-control-plane`:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outFile = "audits\RESTORE_POINT_RUNTIME_ACCEPTANCE_$stamp.md"

.\ops\bifrost\New-AgentCoreRestorePointReport.ps1 `
  -SallyAcceptancePath '<path from Sally final acceptance>' `
  -LangGraphCanaryPath '<path from LangGraph production canary>' `
  -SwarmClawCanaryPath '<path from Sally SwarmClaw autonomous canary>' `
  -OutFile $outFile
```

Commit the generated restore-point report only if:

- `Test-AgentCoreMorningReadiness.ps1` reports `READY`;
- all three evidence paths are present;
- the generated report says the restore point is production-ready by evidence, not by assumption.
