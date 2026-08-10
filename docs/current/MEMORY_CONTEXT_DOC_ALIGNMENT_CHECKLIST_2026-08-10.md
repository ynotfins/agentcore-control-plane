# Memory / Context Doc Alignment Checklist — 2026-08-10

**Purpose:** stop drift before the first real production comparison run by making every current AgentCore authority document say the same memory/context ownership model. Cursor-facing authority path: `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`.

**Approval:** `AUTH-2026-08-10-SWARMRECALL-NATIVE-CONTEXT-DOC-ALIGNMENT`

## Locked ownership model

- SwarmRecall is the PC-native semantic memory/context plane.
- `agentcore-memory` is the AgentCore-governed access facade and lifecycle surface behind `agentcore-gateway`; it is not the top semantic-memory authority.
- AgentCore PG18 remains canonical for exact evidence, recovery, policy, leases, generated projections, and LangGraph checkpoints.
- LangGraph may use semantic memory through the AgentCore facade, but LangGraph checkpoints remain PG18 PostgresSaver.
- SwarmClaw/Sally owns Swarm runtime operation and reaches neutral SwarmRecall through Swarm-owned bounded adapters.
- Ordinary IDEs receive one MCP entry: `agentcore-gateway`; they never receive raw SwarmRecall, SwarmVault, PostgreSQL, or Meilisearch credentials.

## Checklist

| Step | Status | Evidence |
| --- | --- | --- |
| M0 — Restore baseline verified | Done | `@D:\github\agentcore-control-plane\audits\RESTORE_POINT_RUNTIME_ACCEPTANCE_20260809-220421.md`; `@D:\github\agentcore-control-plane\docs\current\GOAL_COMPLETION_CHECKLIST_2026-08-09.md` |
| M1 — Protected docs backed up and unlocked | Done | `@D:\github\agentcore-control-plane\audits\rollback\AUTH-2026-08-10-SWARMRECALL-NATIVE-CONTEXT-DOC-ALIGNMENT\20260810-160956\before-hashes.json` |
| M2 — Anchored wording corrected | Done | `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`, `@D:\github\agentcore-control-plane\BLUEPRINT.md`, `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`, `@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md`, `@D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md`; generated IDE rules refreshed from `@D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml` |
| M3 — Cross-doc contradiction audit | Done | `@D:\github\agentcore-control-plane\audits\MEMORY_CONTEXT_DOC_ALIGNMENT_AUDIT_2026-08-10.md` |
| M4 — Validators and live readiness | Done | `python scripts\validate_authority_lock.py`; `python scripts\bifrost\validate_contracts.py`; `python scripts\render_ide_rules.py --check`; `python scripts\validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md docs\current\CURRENT_CONTEXT_HANDOFF_2026-08-10.md docs\current\MEMORY_CONTEXT_DOC_ALIGNMENT_CHECKLIST_2026-08-10.md`; `.\ops\bifrost\Test-AgentCoreMorningReadiness.ps1` SUMMARY READY 23/23; `.\ops\bifrost\Test-SallyAcceptanceEvidence.ps1` SUMMARY READY 16/16; `.\ops\bifrost\Test-AgentCoreFinalAcceptanceEvidence.ps1` SUMMARY READY 7/7 |
| M5 — Relock and source checkpoint | Done | Protected read-only attributes restored; before/after hashes recorded under `@D:\github\agentcore-control-plane\audits\rollback\AUTH-2026-08-10-SWARMRECALL-NATIVE-CONTEXT-DOC-ALIGNMENT\20260810-160956`; bounded commit and push complete |
| M6 — Fast rolling-context audit before first project | Pending | Codex/Cursor AgentCore memory lifecycle proof plus Sally Swarm-side audit prompt |

## First production comparison gate

Do not start the Android notification app comparison until M3-M6 are complete or explicitly waived by the operator.
