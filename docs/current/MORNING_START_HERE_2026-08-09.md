# Morning Start Here — 2026-08-09

Use this file as the first operator pointer for the morning live-readiness flow.

## First file to open

Open the morning approval packet:

`@D:\github\agentcore-control-plane\docs\handoffs\MORNING_OPERATOR_APPROVAL_PACKET_2026-08-09.md`

That packet contains the exact command order, approval boundaries, Sally prompt path, evidence gates, canary sequence, and final restore-point preflight.

## Latest read-only evidence snapshot

Latest audit:

`@D:\github\agentcore-control-plane\audits\MORNING_READINESS_LIVE_SNAPSHOT_2026-08-09_0644.md`

## Current known live state

The latest source-only snapshot found the workstation is source-prepared but still `NOT_READY` for production runtime work until the approved live phases run.

Expected blockers:

1. Cursor global MCP still has extra entries: `agentcore-gateway`, `codegraph`, `repomix`; it must be reduced to only `agentcore-gateway`.
2. Bifrost live config has not been rolled forward to the merged source config.
3. `AgentCore-Bifrost-Watchdog` is not installed live.

Current good evidence:

- Bifrost health is OK.
- SwarmRecall, Meilisearch, SwarmClaw, and SwarmVault/Swarm UI endpoints are up on loopback.
- `H:\SwarmData`, `H:\SwarmRuntime`, and `E:\SwarmBackups` exist.
- Swarm PG on `127.0.0.1:65432` is now listening.
- LangGraph topology is the expected 15-node production fingerprint.

## Guardrail

Do not treat Sally's current `ORCHESTRATOR_OK` as full acceptance. It is orchestrator health only. Full Swarm acceptance must use:

`@D:\github\agentcore-control-plane\docs\prompts\SALLY_FULL_SWARM_ACCEPTANCE_PROMPT_2026-08-09.md`

and must pass:

```powershell
.\ops\bifrost\Test-SallyAcceptanceEvidence.ps1 -Path '<path from Sally final acceptance>'
```

Before final restore-point generation, all evidence must pass:

```powershell
.\ops\bifrost\Test-AgentCoreFinalAcceptanceEvidence.ps1 `
  -SallyAcceptancePath '<path from Sally final acceptance>' `
  -LangGraphCanaryPath '<path from LangGraph production canary>' `
  -SwarmClawCanaryPath '<path from Sally SwarmClaw autonomous canary>'
```
