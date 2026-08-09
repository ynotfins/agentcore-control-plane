# Goal Completion Checklist — 2026-08-09

**Purpose:** prevent drift while moving from source-prepared to production-ready runtime execution.

**Start file:** `@D:\github\agentcore-control-plane\docs\current\MORNING_START_HERE_2026-08-09.md`
**Execution packet:** `@D:\github\agentcore-control-plane\docs\handoffs\MORNING_OPERATOR_APPROVAL_PACKET_2026-08-09.md`
**Latest evidence:** `@D:\github\agentcore-control-plane\audits\BIFROST_ROLLOUT_READY_2026-08-09_1801.md`

## Drift rules

- Do not redefine the goal around a passing subset.
- Do not treat Sally's `ORCHESTRATOR_OK` as full Swarm acceptance.
- Do not edit Swarm runtime state from AgentCore.
- Do not remove project-level MCP servers from `@D:\github\nfa-alerts-enterprise` during AgentCore global cleanup.
- Do not expose raw SwarmRecall, SwarmVault, PostgreSQL, Meilisearch, or direct SQL credentials to ordinary IDEs.
- Do not start real production project work until this checklist reaches final restore-point evidence.

## Milestone checklist

| Milestone | Status | Required evidence |
| --- | --- | --- |
| M0 — Source lock | Done | Current docs, helper fixes, and checklist committed/pushed to `origin/main`. |
| M1 — Cursor global MCP cleanup | Done | Global `@C:\Users\ynotf\.cursor\mcp.json` has only `agentcore-gateway`; `Test-AgentCoreBifrostGateway.ps1` passed. |
| M2 — Project MCP preservation | Done | `@D:\github\nfa-alerts-enterprise\.cursor\mcp.json` still has project-level servers; `codegraph` and `repomix` stdio handshake tests passed. |
| M3 — Bifrost live rollout | Done | `Test-AgentCoreMorningReadiness.ps1` returned `SUMMARY status=READY pass=23 warn=0 fail=0`; config drift cleared via source-rendered runtime candidate; `AgentCore-Bifrost-Watchdog` installed and healthy. |
| M4 — Sally full Swarm acceptance | Pending Sally report | Sally produces a full Swarm acceptance report and `Test-SallyAcceptanceEvidence.ps1` returns `SUMMARY status=READY`. |
| M5 — LangGraph canary | Pending runtime canary | Production LangGraph canary evidence exists and uses the AgentCore workflow runtime/checkpoint authority. |
| M6 — SwarmClaw canary | Pending Sally-owned canary | SwarmClaw autonomous canary evidence exists and proves writes stayed inside Swarm-owned boundaries. |
| M7 — Final evidence preflight | Pending final gate | `Test-AgentCoreFinalAcceptanceEvidence.ps1` returns `SUMMARY status=READY`. |
| M8 — Restore point report | Pending final artifact | `New-AgentCoreRestorePointReport.ps1` generates the final restore-point report after M7 passes. |

## Current next action

Continue to M4: Sally full Swarm acceptance. Give Sally:

`@D:\github\agentcore-control-plane\docs\prompts\SALLY_FULL_SWARM_ACCEPTANCE_PROMPT_2026-08-09.md`

## Completion condition

The goal is complete only when:

1. Cursor global MCP has exactly one server: `agentcore-gateway`.
2. Bifrost config drift is gone.
3. `AgentCore-Bifrost-Watchdog` is installed and postflight-verified.
4. Sally full Swarm acceptance passes the structural validator.
5. LangGraph production canary evidence exists.
6. SwarmClaw autonomous canary evidence exists.
7. Final acceptance evidence preflight passes.
8. Final restore-point report is generated and committed/pushed if source-controlled.
