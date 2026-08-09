# Morning Start Here — 2026-08-09

Use this file as the first operator pointer for the morning live-readiness flow.

## First file to open

Open the morning approval packet:

`@D:\github\agentcore-control-plane\docs\handoffs\MORNING_OPERATOR_APPROVAL_PACKET_2026-08-09.md`

That packet contains the exact command order, approval boundaries, Sally prompt path, evidence gates, canary sequence, and final restore-point preflight.

Checklist and drift guard:

`@D:\github\agentcore-control-plane\docs\current\GOAL_COMPLETION_CHECKLIST_2026-08-09.md`

## Latest read-only evidence snapshot

Latest audit:

`@D:\github\agentcore-control-plane\audits\BIFROST_ROLLOUT_READY_2026-08-09_1801.md`

## Current known live state

The governed Bifrost rollout is complete. `Test-AgentCoreMorningReadiness.ps1` returned `SUMMARY status=READY pass=23 warn=0 fail=0`.

Current blockers:

None for Bifrost readiness. Continue to Sally full Swarm acceptance before production project work.

Current good evidence:

- Bifrost health is OK.
- `AgentCore-Bifrost-Watchdog` is installed and healthy.
- Cursor global MCP now has only `agentcore-gateway`.
- `@D:\github\nfa-alerts-enterprise` project-level MCP still has `mcp-codebase-search`, `code-search`, `codebase-memory`, `claude-context`, `codegraph`, and `repomix`.
- `codegraph` and `repomix` project-level MCP servers passed independent stdio initialize + tools/list smoke tests.
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
