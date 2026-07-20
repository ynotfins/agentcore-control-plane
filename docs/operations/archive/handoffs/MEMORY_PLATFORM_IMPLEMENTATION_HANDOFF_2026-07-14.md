# Memory Platform Implementation Handoff — 2026-07-14

> **ARCHIVED 2026-07-20** under `docs/operations/archive/handoffs/`. Pointer stub: `docs/handoffs/MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md`.  
> **Historical implementation handoff — superseded for live facts.** Prefer `CONTEXT_BLOCK.md` §0a and current runbooks.

**For:** the agent that implements the AgentCore memory/context/database platform.
**Produced by:** the authority-reconciliation task (branch `task/authority-reconciliation`, HEAD commit `935b273`), which satisfies Milestone **M0 — Authority and Execution Foundation**.

> **Current-state update — 2026-07-16:** M0-M5 are complete. PostgreSQL 18.4 at
> `127.0.0.1:55433` is canonical; `agent_core` and `cognee_core` are recoverable;
> WAL/PITR is enabled and tested; PG18 service ownership is restored to
> `AgentCore-PostgreSQL18`; `NightlyBackup`, `NightlyRestoreTest`, and
> `WeeklyMaintenance` call repo-owned PG18 scripts. Use
> `audits/M5/M0-M5-HARDENING-EVIDENCE.md`,
> `audits/M5/elevated-closeout-20260716-015250.json`, and
> `docs/memory-platform/BACKUP_RESTORE_WAL_PITR.md` for current operational evidence.
> The original M1 startup facts below are retained as historical handoff context only.
>
> **Current-state update — 2026-07-20:** M6 workflow + capability leases + OpenRouter JIT
> bridge are live. Mutable posture: `CONTEXT_BLOCK.md` §0a. Ops runbooks:
> `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, `docs/operations/OPENROUTER_MCP.md`.
> Do not treat older “leases not built / memory degraded” phrasing in historical sections as current.

## 1. Exact authority read order (read nothing else first)

1. `PROJECT_ANCHOR.md` — constitution (incl. §0 Bifrost Gateway Override, §0.1 Project Execution Boundaries)
2. `DOC_AUTHORITY.md` — hierarchy and classification (seven levels; nothing overrides the chain)
3. `BLUEPRINT.md` — **locked implementation blueprint**: final goal, architecture, drive roles, allocation-unit targets, lossless guarantees, STATE model, Milestone exit criteria (M0–M8), change-control list. Cursor may optimize Macro/Micro steps but may not change locked items without explicit operator approval.
4. `CONTEXT_BLOCK.md` — current mutable state (where it conflicts with BLUEPRINT.md, BLUEPRINT wins)
5. `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` — detailed Milestone execution guidance (derives from BLUEPRINT.md)
6. Bifrost contracts, ops runbooks, and handoffs: `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json`, `docs/operations/OPENROUTER_MCP.md`, `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, `docs/bifrost/`, plus current dated handoffs under `docs/handoffs/` (2026-07-12 Bifrost handoff is historical cutover evidence)
7. `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md` — machine facts (hardware, drives, installed software, runtime snapshots)

Plus for execution mechanics: `docs/agent-policy/` (Milestone entry/exit gates, checklist evidence rules, tool audits) and `MILESTONES.md` + `BLUEPRINT.md` §8 (operator's verbatim locked Milestones — evidence for the execution plan).

## 1a. Key BLUEPRINT.md facts to load immediately (from live evidence 2026-07-14)

- **I: allocation units:** 512 bytes (target: 64KB; I: is empty — correction authorized and planned for M1)
- **E:, F:, H: allocation units:** already 65536 (64KB) — no format needed
- **F: used:** ~3.4 GB total (PG16 cluster 172 MB + PG16 binaries 778 MB + Swarm runtime 367 MB); 3722 GB free
- **H: used:** ~3.9 GB (Bifrost runtime 110 MB binary + DBs + logs); 1857 GB free
- **PG16 cluster:** stopped (port 55432 not listening); data at `F:\AgentCore\database_cluster`; PG16.6 binaries at `F:\AgentCore\postgres_runtime_engine\pgsql`
- **No PG18 installer present** — download required in M1
- **Existing ops:** `ops/Backup-AgentCorePostgres.ps1`, `ops/Start-AgentCorePostgres.ps1`, `ops/Test-AgentCorePostgresRestore.ps1` — already written, use them

## 2. What M0 established (do not re-litigate)

- One authority hierarchy; `database-plan.md` and `AGENT_DATABASE_BOOTSTRAP.md` are historical evidence with banners — **never implement their schemas, tool names, or Swarm memory planes**.
- All Swarm-first, old-database, direct-IDE-SQL, telemetry-off, and `global-memory-gateway` instructions are neutralized (bannered or corrected). If you find a document contradicting the hierarchy, the hierarchy wins.
- Global project-execution policy (`docs/agent-policy/`), governance templates (`templates/project-governance/`), machine-readable contracts (`contracts/global-agent-policy.yaml`, `contracts/project-execution-policy.json`, `contracts/project-tool-lifecycle.json`), and per-IDE rule profiles (`ide-profiles/`) exist and validate.
- Validators enforce the above: `python scripts/bifrost/validate_contracts.py`, `python scripts/bifrost/test_contracts.py`, `powershell -File validators/validate-control-plane.ps1 -DryRun [-SourceOnly]`. Keep them green.

## 3. Starting live state (verify, don't assume)

- **Bifrost gateway is live**: `agentcore-gateway` at `http://127.0.0.1:8080/mcp`, runtime `H:\AgentRuntime\bifrost`, owned by scheduled task `\AgentCore\AgentCore-Bifrost-Gateway`. Config renders from the registry via `scripts/bifrost/render_bifrost_config.py`; restart only through the scheduled-task owner. **Never format or re-provision H:.**
- **`agentcore-memory` is degraded by design**: `scripts/agentcore_memory/server.py` exposes only `memory_health`/`memory_status`. M4 replaces its internals behind the same identity — no IDE config change, no renaming.
- **PG16 cluster is live** at `127.0.0.1:55432` (`F:\AgentCore\database_cluster`) and must be preserved and backed up before any PG18 work (M1 gates). PG18 gets a **new data directory** on F:; never point PG18 at the PG16 directory.
- Archive tier: `E:\AgentCoreArchive` (canonical); second backup copy to `G:`.
- The worktree `D:\AgentSwarm\runs\agentcore-memory-v1\worktree` (branch `ai/global-memory-platform-v1`) predates the locked Milestones. Reconcile it against the execution plan before reusing it, or start a fresh branch from the reconciled main line — do not blindly continue its diff.
- `D:\github\memory-context-database` holds corpus/template planning only (`DOCS_PLAN.md`, `DEPWIRE.md`) — supporting evidence, not architecture. Do not modify that repo.

## 4. Locked decisions you cannot change without operator approval

Milestone purposes, exit criteria, ordering; PostgreSQL 18 + pgvector as canonical store; AgentCore-owned evidence/context/projections; Cognee (not Mem0 — **Mem0 must not be installed**); Bifrost `agentcore-gateway` and `agentcore-memory` identities; Swarm independence; no Docker/WSL core dependency; no second canonical memory store; the nine lossless guarantees; the four generated STATE projections written atomically by the projection worker only.

Macro/Micro steps are yours to refine per Milestone (add/remove/split/reorder, choose APIs and package structure) — refine the current Milestone immediately before starting it, using repository state, Context Fabric, Arabold exact-version docs, Serena, Depwire, Tentra, and machine evidence.

## 5. Out of scope until their Milestone

- Runtime tool leases / dynamic tool exposure → **M6** (PostgreSQL-backed; the registry's wildcard grants stay transitional until then; `TOOL_MANIFEST.yaml` files are policy-only until M6).
- Cognee install → M5 (behind `KnowledgeMemoryPort`, own `cognee_core` DB, promoted knowledge only).
- LangGraph → M6.
- Any live IDE config change: **never required** — that is an M4 exit criterion.
- Any Swarm/OpenClaw/ClawX modification: never.

## 6. First actions for M1

1. Run the Milestone entry gate (`docs/agent-policy/MILESTONE_EXECUTION_STANDARD.md`): confirm M0 passed (this handoff + `audits/VALIDATION_REPORT_2026-07-14.md`), Context Fabric capture/drift, Arabold checkpoint for exact PG18/pgvector versions (baseline: PG 18.4, pgvector 0.8.5 — re-verify), Depwire/Serena/Tentra structural check.
2. Inventory the live PG16 cluster; create logical + physical backups to `E:\AgentCoreArchive` and `G:`; pass a restore test into a disposable database.
3. Only then install PG18 side-by-side on F: per the M1 exit criteria.
