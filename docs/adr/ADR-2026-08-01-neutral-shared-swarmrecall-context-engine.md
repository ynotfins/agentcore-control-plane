# ADR-2026-08-01 — Neutral Shared SwarmRecall + Portable Context Engine

**Status:** Accepted (operator-final)  
**Date:** 2026-08-01  
**Approval ID:** `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`  
**Authority:** Amends `PROJECT_ANCHOR.md`, `BLUEPRINT.md`, foreign Swarm boundary contracts, and `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`

## Context

AgentCore and Swarm previously treated SwarmRecall as Swarm-owned exclusive infrastructure. Dual-Recall (separate AgentCore-owned + Swarm-owned instances) and AgentCore-only (no shared Recall) were evaluated and rejected. Ordinary IDEs already use a single `agentcore-gateway` entry and a stable ten-tool `agentcore-memory` facade. Exact evidence and LangGraph checkpoints already live on PostgreSQL 18.

## Decision

1. Deploy **one** SwarmRecall API + PostgreSQL 16/pgvector + Meilisearch stack as a **neutral machine-level semantic-memory data plane** (not AgentCore-owned runtime, not Swarm-owned runtime).
2. **Reject** dual-Recall and AgentCore-only alternatives.
3. AgentCore remains authority for: Bifrost/`agentcore-gateway`, ten-tool `agentcore-memory`, non-Swarm IDE lifecycle policy, PG18 exact evidence/identity/provenance/LangGraph checkpoints, and Cognee curated KG processing.
4. Swarm remains authority for: SwarmClaw SQLite operational state, SwarmVault, and Swarm’s bounded Recall client adapter.
5. Shared SwarmRecall owns only curated cross-client semantic memory (global pool + per-project pools; summaries/decisions/learnings/skills/relations/source refs). PG+pgvector is canonical for those rows; Meilisearch is a rebuildable lexical projection with durable outbox/retry/rebuild.
6. Portable **AgentCore Context Engine** lives at `D:\github\agentcore-context-engine` (dedicated repository — not under `agentcore-control-plane/packages/`). It orchestrates session identity, rolling context, compaction, retrieval, token budgets, provenance, handoff, and recovery **above** `agentcore-memory` and SwarmRecall. It does not replace Cognee, PG18 evidence, LangGraph checkpoints, SwarmClaw SQLite, or SwarmRecall.
7. Ordinary IDEs expose only `agentcore-gateway`. No raw SwarmRecall MCP tools or credentials in IDE configs.
8. Explicit `sessionId` + external idempotency keys required for automatic durable semantic writes; do not use `sessions/current` for write targeting.
9. Loopback-only listeners; no cross-device sync in this phase. Secrets remain Windows User-scope env + child-process mapping.
10. Physical placement (this PC, verified 2026-08-01): reclassify live SwarmRecall on loopback `:3300` / PG16 `:65432` / Meili `:7700` in place as the neutral plane; LangGraph/PG18 remain AgentCore on `:55433`; SwarmClaw remains on `:3456` with H: operational data; cold backups under `E:\`.

## Consequences

- Foreign-boundary language must change from “AgentCore must not consume SwarmRecall” to “AgentCore may consume the **neutral** SwarmRecall plane only through the `agentcore-memory` server-side adapter; raw SwarmRecall remains excluded from IDE baselines.”
- Swarm contracts must reclassify Recall/PG16/Meili as neutral shared services.
- Context Engine is the first real governed LangGraph project (`agentcore-context-engine`).
- Rollback: restore authority files from `E:\AgentCore-Backups\authority-unlock-AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE\` and Swarm copies under `E:\SwarmBackups\...`; disable Recall adapter; PG18 evidence/checkpoints remain authoritative.

## Non-goals

- Second Recall instance for AgentCore.
- Replacing Cognee.
- Non-loopback exposure or cross-device synchronization.
- Installing SwarmRecall MCP into ordinary IDE profiles.
- Storing LangGraph checkpoints or raw transcripts in SwarmRecall.

## Linked evidence

- Plan: `C:\Users\ynotf\.cursor\plans\memory_architecture_audit_2cf0706b.plan.md`
- SwarmRecall hardening commit (ynotfins fork): `b272130f45354570ee5e355125dce36ef6257411`
- Context Engine initial commit (local): `cc21747c8715889b7e91c0322de5899ddbe2ad6d`
- Rollback manifest timestamp: `20260801-172118`
