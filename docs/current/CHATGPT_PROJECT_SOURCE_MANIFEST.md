# ChatGPT Project Source Manifest — Retired Export Path

**Status:** `RETIRED SOURCE EXPORT`
**Retired:** 2026-08-04
**Approval:** `AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION`

The July 25 static source bundle is retired. It embedded mutable SHA-256 values and promoted a dated dual-ecosystem handoff into the default context set. That design became stale whenever an authority document changed and could give an agent contradictory current state.

Do not upload or ingest the former bundle as current AgentCore context. Git history and the rollback bundle preserve the old manifest as point-in-time evidence.

## Current source order

For AgentCore work, read live repository files in this order:

1. `PROJECT_ANCHOR.md`
2. `DOC_AUTHORITY.md`
3. `BLUEPRINT.md`
4. `CONTEXT_BLOCK.md`
5. `contracts/bifrost-upstream-mcp-registry.json`
6. `contracts/agentcore-gateway-client.json`
7. `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md`
8. `SERENA.md`
9. `MASTER_CONFIG_AND_PROMPT.md`

For memory/database work, also read `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`. For LangGraph operation, use `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md` and `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md`.

Historical audits and handoffs are evidence only. They must not be included in default rolling context unless a current authority document cites them for a specific fact.

## Replacement contract

The source of truth is the checked-out repository plus live `agentcore-memory` recovery, not a copied static package. Any future portable source-package feature requires a separately approved generated manifest that derives hashes at export time and never promotes historical evidence to current authority.
