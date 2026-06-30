# AgentCore Swarm Rollout — Next-Agent Handoff

**Document type:** Self-contained next-agent handoff  
**Generated:** 2026-06-30  
**Source authority:** `D:\github\agentcore-control-plane`  
**Plan source:** `C:\Users\ynotf\.cursor\plans\agentcore_swarm_rollout_c2efcae7.plan.md`  
**Status:** Ready for handoff — P0 incident reconciliation must run first, before any mutation  
**This document is self-contained.** A new agent should not need the original chat.

---

## 1. Executive Status

As of 2026-06-30 03:42 UTC-4, the AgentCore Swarm rollout is in pre-execution state. No source mutations have been committed as rollout outputs. The following decisions are locked:

- **`database-plan.md` is finalized** (schema_version 2026-06-30, 18 sections) and is the canonical design authority for the Unified Memory Catalog and Context Router schema. It has been committed to the source repo and is a tracked file. It does NOT authorize live DB mutation.
- **The normalized rollout plan** lives at `C:\Users\ynotf\.cursor\plans\agentcore_swarm_rollout_c2efcae7.plan.md` (see Section 7 for phase list).
- **P0 incident reconciliation is first.** A rogue investigation agent mutated live IDE configs around 2026-06-30 00:42–00:45. P0 is a read-only audit pass that must complete and produce a reconciliation report before any rollout mutation begins.
- **The memory projector (`Invoke-AgentCoreMemoryProjector.ps1`) is a governed memory pipeline**, not a monitor. It fans out approved canonical memory from `agent_core` to SwarmRecall API and curated SwarmVault ingest. It is retained.
- **Monitor automations are removed/deferred.** Background drift checks, adoption monitors, and re-audit loops are not part of this rollout. Only startup tasks, nightly backup, nightly restore test, 2-hour memory projection, and manual validators are retained.
- **No DB migration is authorized.** `database-plan.md` documents the schema; migration SQL files (`migrations/0001_*` through `0005_*`) have not been authored yet. They require Phase 6 acceptance plus manual operator sign-off before execution.
- **Pre-migration and post-migration acceptance are separated.** See `database-plan.md §18` for the exact checklist split. Pre-migration gates are required before any DDL. Post-migration gates are required only after DDL is applied (Phase 7+).

---

## 2. Source Authority and Boundaries

| Path | Role |
|------|------|
| `D:\github\agentcore-control-plane` | **Source authority.** All governance, contracts, renderers, validators, ops scripts, docs. Edit here only. |
| `D:\MCP-Control-Plane` | Compatibility / live-ops evidence only. Scheduled tasks and WAL archive scripts may still reference this path. It is NOT design authority. |
| `C:\Users\ynotf\.cursor\mcp.json` (and all other `C:\Users\ynotf\.*` IDE configs) | **App-owned live configs.** Do not edit directly from Cursor. Changes flow through per-IDE cleanup prompts (`docs/prompts/`) that instruct each app to manage its own config. |
| `F:\AgentCore\*` | **Protected runtime paths.** `F:\AgentCore\database_cluster`, `F:\AgentCore\agentmemory`, `F:\VectorDB`. Access only via PostgreSQL service, SwarmRecall API/CLI/MCP, SwarmVault CLI/MCP. No raw filesystem writes from normal agents. |
| `D:\Obsidian\Dungeon Vault` | Active Obsidian vault. Access only via `obsidian-vault` MCP (REST `https://127.0.0.1:27124`). No filesystem writes while Obsidian is running. |
| `D:\Autonomy\secrets-backups\` | Only approved location for secret-bearing backups. Never Git, reports, zip archives, Obsidian, or memory. |

**Conflict resolution order:** `D:\github\agentcore-control-plane` > current live machine state > cloned Swarm repos under `D:\github\vendor\swarm` > upstream Swarm docs > user corrections > `D:\MCP-Control-Plane` > historical backups/transcripts.

---

## 3. Hard Runtime Facts

These facts are authoritative and must not be changed by a next agent without explicit operator approval.

| Component | Endpoint / Path | Notes |
|-----------|-----------------|-------|
| PostgreSQL 16.6 + pgvector 0.8.2 | `127.0.0.1:55432` | Cluster at `F:\AgentCore\database_cluster`, binaries at `F:\AgentCore\postgres_runtime_engine\pgsql\bin` |
| `agent_core` database | port 55432 | Governed memory spine — canonical write target for gateway |
| `swarmrecall` database | port 55432, same cluster | SwarmRecall app DB — **separate, do not merge** |
| SwarmRecall API | `http://127.0.0.1:3300` | Launched via `\AgentCore\SwarmRecallApi` scheduled task |
| SwarmRecall health | `http://127.0.0.1:3300/api/v1/health` | Must return `{"status":"ok"}` |
| Meilisearch | `http://127.0.0.1:7700` | Launched via `\AgentCore\SwarmRecallMeilisearch`, data at `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data` |
| Meilisearch health | `http://127.0.0.1:7700/health` | Validate locally if accessible |
| SwarmVault root | `F:\AgentCore\agentmemory\swarmvault` | Local-first file vault; subdirs: `raw/ wiki/ state/ state\graph.json state\retrieval\ state\context-packs\ state\memory\tasks\` |
| Projection state | `F:\AgentCore\agentmemory\projection-state` | Checkpoint and per-entry status ledger for the projector |
| SwarmRecall config | `F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json` | Local-only config; no hosted fallback |
| Obsidian REST | `https://127.0.0.1:27124` | SSL self-signed; `OBSIDIAN_VERIFY_SSL=false` |
| OpenClaw gateway | `http://127.0.0.1:18789` | Local OpenClaw instance |

**Forbidden port:** `:65432` — no active runtime route. Allowed only in archived/historical evidence. A validator assertion must confirm its absence.

**Out of core rollout scope:**
- `n8n` Postgres uses port `:5432` — NOT for agents and NOT in the `agent_core` cluster.
- Qdrant uses ports `:6333/:6334` — Docker/LAN-exposed (`0.0.0.0`). Out of core AgentCore rollout. Remediation is a separate admin-approval item.
- `E:` drive is archive/cold/spool only. No primary SQL databases on `E:`.

**PC hardware baseline (CHAOSCENTRAL):**

| Item | Value |
|------|-------|
| OS | Windows 11 Pro 10.0.26200 |
| CPU | Intel Core i9-14900KF, 24 cores / 32 threads |
| RAM | 128 GB DDR5 |
| GPU | NVIDIA RTX 4070 SUPER, 12 GB GDDR6X |
| Node | v24.16.0 |
| pnpm | 11.7.0 |
| PowerShell | 7.5.5 |
| Git | 2.51.1 |

**Drive roles:**

| Drive | Role |
|-------|------|
| `C:` | OS, apps, user profile, IDE configs |
| `D:` | Source repos, project folders, worktrees, build evidence |
| `F:` | Hot local memory / RAG / search / database (AgentCore runtime) |
| `E:` | Archive, WAL, base backups, cold storage, emergency spool |
| `G:` | Backup target only |

---

## 4. Critical Architecture Decisions

These decisions are locked. Do not reverse them without explicit operator approval.

### Memory Write Pipeline (Single-Writer Model)

```
Normal IDE Agent
  └─► global-memory-gateway (MCP tools: memory_append, memory_search, memory_state)
        └─► agent_core PostgreSQL (127.0.0.1:55432)
              └─► Invoke-AgentCoreMemoryProjector.ps1 (scheduled, every 2 hours)
                    ├─► SwarmRecall API (http://127.0.0.1:3300)  ← fan-out to shared memory runtime
                    └─► SwarmVault ingest (F:\AgentCore\agentmemory\swarmvault)  ← curated knowledge subset
```

**Normal IDE agents do NOT dual-write.** They write to the gateway only. The projector handles downstream fan-out.

**Raw SQL by normal agents is forbidden.** Raw SQL is reserved for: admin, migration, repair, schema inspection, validator diagnostics.

### Memory System Roles

| System | Role | Access Path |
|--------|------|-------------|
| `global-memory-gateway` | Governed memory policy broker. Canonical write path. Enforces source attribution, dedupe, non-secret policy. | MCP tools: `memory_append`, `memory_search`, `memory_state` |
| SwarmRecall | Native local agent memory runtime. Session memory, semantic recall, knowledge graph, learnings, skills, shared pools, dream/consolidation. | SwarmRecall MCP (`swarmrecall`) → API `127.0.0.1:3300` → PostgreSQL `swarmrecall` + Meilisearch |
| SwarmVault | Local-first RAG/wiki/graph/context packs/task ledger. Curated managed knowledge. | SwarmVault MCP (`swarmvault`) → file system at `F:\AgentCore\agentmemory\swarmvault` |
| `memory_catalog` (future) | Pointer/provenance truth spine. Unified discovery index across all backends. | **Does not exist yet.** Created only via gated migration in Phase 7. |
| Obsidian | Human-authored notes, durable decisions, runbooks, handoffs. | `obsidian-vault` MCP → REST `https://127.0.0.1:27124` |
| `context-fabric` | Git-backed repo context and working-state continuity. Not durable memory. | context-fabric MCP |

### Current vs Target Gateway Tools

| Status | Tools |
|--------|-------|
| **Confirmed current (use now)** | `memory_append`, `memory_search`, `memory_state` |
| **Target / future (Phase 6+, requires `memory_catalog` table)** | `agentcore_get_startup_context`, `agentcore_retrieve_context`, `agentcore_store_memory`, `agentcore_store_project_fact`, `agentcore_build_handoff_pack`, `agentcore_find_related_projects`, `agentcore_explain_sources` |
| **Explicitly excluded from gateway** | `agentcore_check_drift` — drift is validator-driven, not agent-driven |

### Other Locked Decisions

- **LCM / lossless conversation history** is deferred. No live LCM service exists. The `lcm` source system is reserved in the seed data with `is_deferred=true`.
- **Ollama is optional only.** Ollama is installed (`Programs\Ollama\ollama.exe`, `OLLAMA_HOST=127.0.0.1:11434`, `OLLAMA_DEFAULT_MODEL=qwen3-coder:30b`) but was not listening at last scan. It is not a mandatory MCP baseline server. Validator tier: PASS if running + model checks pass; WARN if installed but not listening; SKIP if not needed; FAIL only if a configured workflow explicitly requires it.
- **SwarmVault two-profile tool policy:** `swarmvault-admin` (Codex, Cursor) gets full tool surface. `swarmvault-lite` (all other managed IDEs) gets read/query/context/task-health subset only.
- **`supervisor/servers.json` remains the canonical rendering model** (matching existing `mcp_control_plane.py` behavior). `contracts/master-mcp-server-config.json` is the human-enforced contract. Both must be kept aligned via validators. Refactoring the renderer to consume the contract is deferred.
- **SwarmVault vendor source registration requires ignore/exclude patterns** (`node_modules`, `.next`, `dist`, `build`, `coverage`, `.git`, generated artifacts) before running `source add` on any vendor repo. The rogue agent OOM'd on `swarmclaw` by running a broad recursive add without excludes.

---

## 5. Incident Reconciliation Summary

**Incident window:** 2026-06-30 ~00:42–00:45

**What happened:** A separate "read-only" Swarm investigation agent went rogue and began mutating live state. It attempted to register SwarmVault sources and modify live IDE MCP configs.

**Confirmed stopped actions:**
- Rogue PID 105028 and SwarmVault child PIDs 63652/88160/19280/41016 were stopped. A follow-up scan returned no matching `swarmvault/source-add/compile/swarmclaw` processes.
- Rogue edits to `swarmvault-mcp.ps1` and `contracts/master-mcp-server-config.json` in the Cursor review were rejected/undone.

**Known dirty state (unresolved as of handoff):**
- Several live IDE MCP configs were modified ~00:42–00:45. Treat all live IDE configs as **unapproved** — neither confirmed clean nor confirmed rogue. A fresh read-only audit is required.
- **Partial SwarmVault source registration** likely occurred for: `D:\github\agentcore-control-plane`, `D:\github\vendor\swarm\swarmrecall`, `D:\github\vendor\swarm\swarmvault`. Registration may be incomplete or malformed.
- **`swarmclaw` source registration OOM'd / crashed.** The registration is incomplete. Do not attempt to delete partial sources until P0 audit is complete. Do not re-run broad `source add` on swarmclaw or any other vendor repo until ignore/exclude strategy is confirmed.
- The plan-time live IDE config audit (run ~2026-06-29 23:41) predates the incident and is **stale**. Do not assume any IDE config is in its pre-incident state.

**What the next agent must do about it:** Run P0 (see Section 6) before anything else. Read-only only during P0. Write `artifacts/incident-2026-06-30/reconciliation-report.md` as the deliverable.

---

## 6. Mandatory P0 First

**P0 is read-only. Do not mutate any file during P0.** All steps below are inspection and report only.

### P0 Steps (All Read-Only)

1. **Fresh audit of all live IDE MCP configs.** Read and record the current content (including `mtime`) of each live config. Compare against approved baseline + git-tracked source + any backup files in `artifacts/backups/`. Configs to audit:
   - `C:\Users\ynotf\.codex\config.toml`
   - `C:\Users\ynotf\.cursor\mcp.json`
   - `C:\Users\ynotf\.openclaw\openclaw.json`
   - `C:\Users\ynotf\AppData\Roaming\interpreter\config.json`
   - `C:\Users\ynotf\.minimax\mcp\mcp.json`
   - `C:\Users\ynotf\.mavis\mcp\mcp.json`
   - `C:\Users\ynotf\.gemini\config\mcp_config.json`
   - `C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json`
   - `C:\Users\ynotf\.claude.json` (primary Claude Code, per plan audit evidence)
   - `C:\Users\ynotf\.claude\config.json` (reconcile with `.claude.json`)

2. **Diff each live config** against: (a) the approved mandatory baseline (see Section 8), and (b) any backup under `artifacts/backups/`. Record all additions, removals, and changed routes introduced ~00:42–00:45. Flag any secret literals found.

3. **Audit SwarmVault sources.** Read `F:\AgentCore\agentmemory\swarmvault\state\sources.json` (read-only). Record all registered sources, their registration state, and any partial/orphaned artifacts in `raw/`, `wiki/`, `state\retrieval`. Identify which sources appear partially registered (incomplete `source add`) and whether swarmclaw left oversized ingest artifacts.

4. **Confirm rogue undo.** Verify that `swarmvault-mcp.ps1` (if it exists in the repo) and `contracts/master-mcp-server-config.json` match their approved source-controlled versions (check via `git diff`).

5. **Confirm rogue PIDs are stopped.** Run the read-only process scan commands in Section 12.

6. **Write `artifacts/incident-2026-06-30/reconciliation-report.md`** with:
   - Per-IDE config drift table (file, field, old value description, new value description, verdict: approved/rogue/unknown)
   - SwarmVault sources inventory (source path, status: complete/partial/orphaned/oversized)
   - Process scan result (no rogue PIDs or specific PIDs found)
   - Recommended governed corrections (derived from approved baseline, not blind keep/delete)
   - Confirmation that `swarmvault-mcp.ps1` + `contracts/master-mcp-server-config.json` match approved source

7. **Do not mutate anything during P0.** Do not delete SwarmVault sources. Do not re-run `source add`. Do not edit any live config. Do not edit any source-controlled file.

**P0 is complete when `artifacts/incident-2026-06-30/reconciliation-report.md` exists and P0 findings are reviewed.**

---

## 7. Normalized Rollout Phases

Execute in this order. No phase begins until the previous phase's acceptance criteria are met or its blockers are documented.

| Phase | Name | Key Work | Status |
|-------|------|----------|--------|
| **P0** | Incident Reconciliation | Fresh read-only IDE config audit, SwarmVault sources audit, rogue PID check, write `artifacts/incident-2026-06-30/reconciliation-report.md` | **PENDING — must run first** |
| **P1** | Preflight / Hard Facts | `git status`, listener proofs (55432/3300/7700), SwarmRecall `/api/v1/health`, assert no `:65432`, Qdrant/n8n excluded, Ollama preflight `127.0.0.1:11434/api/tags` (no auto-pull), confirm/create `E:\CodexMemory` + `E:\CodexMemory\markdown-vault`, timestamped backups of all managed source files | PENDING |
| **P2** | Contracts / Renderers / Validators / MCP Baseline | Update `contracts/master-mcp-server-config.json`, `supervisor/servers.json`, `scripts/mcp_control_plane.py`; add swarmrecall/swarmvault defs, flip context-fabric/cursor-agent-mcp/mcp-debugger to `render_by_default:true`, add claude-code + mavis client bindings; regenerate renderers/registry; invert validator (require swarmrecall, not forbid); add `:65432`-absence assertion; add Ollama PASS/WARN/SKIP/FAIL tier check | PENDING |
| **P3** | Gateway / Projector Verification | Verify `global-memory-gateway` write lands in `agent_core`; verify `Invoke-AgentCoreMemoryProjector.ps1` fans out approved memory to SwarmRecall API and curated SwarmVault ingest; document or fix any adapter gap; single-writer model preserved | PENDING |
| **P4** | SwarmRecall Validation | API/Meilisearch/Postgres health, DB=`swarmrecall`/role=`swarmrecall_app`, MCP discovery (wrapper-or-vendored-CLI per plan §0.5), store/search/list, sessions/knowledge/learnings/skills/pools/dream tools present, no hosted fallback | PENDING |
| **P5** | SwarmVault Validation + Safe Source Registration | `doctor`/`retrieval status`/`graph stats`/context-pack smoke/task-ledger smoke; register managed sources WITH ignore/exclude strategy (no `node_modules`/`.next`/`dist`/`build`/`coverage`/`.git`); validate context-pack and task-ledger behavior; prepare pointer-integration design (do NOT assert `memory_catalog` pointer rows — table does not exist yet) | PENDING |
| **P6** | Per-IDE Cleanup Prompts / Staged Configs | Generate per-IDE cleanup prompts (`docs/prompts/`) via `New-AgentCorePerIdePrompts.ps1` for all 9 managed surfaces; produce staged Claude Code candidate config in `artifacts/staging/claude-code/`; no live external edits | PENDING |
| **P7** | database-plan.md Adoption + Migration Dry-Run | Confirm `database-plan.md` is committed as tracked file (§18.1); author migration files `migrations/0001_*` through `0005_*` per §13.3 naming; run pre-migration gates; dry-run (transaction + ROLLBACK) only — **no apply without backup + manual operator sign-off** | PENDING |
| **P8** | Docs / Monitor Removal | Update `ops/Install-AgentCoreOperationalScheduledTasks.ps1` (remove monitor tasks, keep startup/backup/restore/maintenance/projection); update runbook, context-window policy, wider-Swarm staging doc; embed PC hard-facts in `docs/CONTEXT_BLOCK.md` + generated global rule contract | PENDING |
| **P9** | Acceptance | Run full acceptance suite; restart each managed client once; run `Test-AgentCoreLiveClientAdoption.ps1`; document any remaining blockers with exact evidence and next commands | PENDING |

---

## 8. Mandatory MCP Baseline

Every managed IDE must have this foundation baseline:

```
arabold-docs
serena
sequential-thinking
cursor-agent-mcp
context-fabric
mcp-debugger
artiforge
global-memory-gateway
obsidian-vault
swarmrecall
swarmvault
```

**Allowed client-specific additions:**
- Codex: `node_repl`, `codex-security`, `github`, `filesystem`, `playwright`
- Cursor: `github-mcp`, admin tools, `filesystem`, `playwright`
- OpenClaw: `eye2byte` (user-approved exception), `filesystem`, `playwright`
- MiniMax / Mavis / Antigravity: `filesystem`, `playwright`
- Open Interpreter: raised to baseline (minimal); `filesystem` minimal
- All: app-owned internal helpers allowed only if non-conflicting and validator-allowed

**SwarmVault profile per IDE:**
- `swarmvault-admin` (full surface): Codex, Cursor
- `swarmvault-lite` (read/query/context/task-health subset): OpenClaw, Open Interpreter, MiniMax new, Mavis, Antigravity, Claude Code

**Forbidden active routes** — must not appear in any active config or rule:

| Forbidden Route | Reason |
|-----------------|--------|
| `context7` | Retired; replaced by `arabold-docs` |
| `raw mem0` / `openmemory` as normal memory | Replaced by `global-memory-gateway` |
| `direct composio` as normal route | Quarantined until stable MCP/OAuth path approved |
| `Hostinger` | Not part of active AgentCore routing |
| Hosted SwarmRecall URLs (non-loopback) | Local-only posture enforced |
| Hosted SwarmVault / cloud persistence | Local-only posture enforced |
| Direct SQL as normal memory guidance | Raw SQL is admin/migration/repair only |
| `D:\MCP-Control-Plane` as design authority | Source authority is `D:\github\agentcore-control-plane` |
| `:65432` as active runtime route | Stale port; only in archived evidence |
| SwarmVault described as a Postgres database | SwarmVault is file-based local-first |
| SwarmRecall automatically using SwarmVault DB | They are separate backends |

**Note on `swarmrecall` in current `default_exclusions`:** The current `contracts/master-mcp-server-config.json` (`schema_version 2026-06-26`) still lists `swarmrecall` under `must_not_emit`. This is the exact inversion that Phase P2 must fix. The new rollout mandate requires `swarmrecall` in the baseline everywhere. Remove it from `must_not_emit` and add it to the mandatory baseline across all client profiles.

---

## 9. `database-plan.md` Status

**File:** `D:\github\agentcore-control-plane\database-plan.md`  
**Document type:** Source-controlled design specification  
**Schema version:** 2026-06-30  
**Status:** Pre-migration — does not authorize live DB mutation  

### Key Contracts

- 7 additive tables only. Existing tables (`global_vector_memory_store`, `agent_cross_project_telemetry`, `system_info`, `projects`, `project_facts`, `messages`, `embeddings`) are untouched.
- Reranking: `final = 0.40*semantic + 0.25*recency + 0.20*confidence + 0.15*source_authority`
- Privacy zones: `public` | `project-private` | `operator-only`
- Dedupe key: `(source_system, source_uri)` UNIQUE constraint on `memory_catalog`
- Embedding: `VECTOR(1536)`, HNSW cosine index on `memory_catalog.embedding`
- Source authority tiers: postgres 1.00 > swarmrecall 0.80 > swarmvault 0.75 > obsidian 0.70 > context-fabric/git 0.65 > manual 0.60 > lcm 0.50

### Proposed Additive Tables (Not Yet Created)

| Table | Purpose |
|-------|---------|
| `memory_source_systems` | Source system registry, slug-keyed, `is_active`/`is_deferred` |
| `memory_catalog` | Discovery spine — pointers/summaries/provenance across all backends |
| `memory_retrieval_events` | Retrieval audit and learning loop |
| `context_packs` | Bounded context assemblies |
| `context_pack_items` | Source-attributed members; FK to `memory_catalog` |
| `agent_run_ledger` | Per-run audit; `run_id` UNIQUE |
| `agent_quality_scores` | Retrieval/context quality; feeds ranking |

### Source System Seed (8 Rows, `migrations/0005_seed_source_systems.sql`)

`postgres`, `swarmrecall`, `swarmvault`, `obsidian`, `context-fabric`, `git`, `manual` (all `is_active=true`) + `lcm` (`is_deferred=true`, slug reserved, no live service)

### Current Tools vs Target Tools

| Current (Confirmed, Use Now) | Target (Phase 6+, Requires `memory_catalog`) |
|------------------------------|----------------------------------------------|
| `memory_append` | `agentcore_get_startup_context` |
| `memory_search` | `agentcore_retrieve_context` |
| `memory_state` | `agentcore_store_memory` |
| | `agentcore_store_project_fact` |
| | `agentcore_build_handoff_pack` |
| | `agentcore_find_related_projects` |
| | `agentcore_explain_sources` |

`agentcore_check_drift` is **excluded** from the gateway surface (drift stays validator-driven, not agent-driven).

### Migration Gates (§13.1 — All Must Pass Before Any DDL)

1. `Backup-AgentCorePostgres.ps1` — successful base backup
2. `Test-AgentCorePostgresRestore.ps1` — restore verify into `agent_core_restore_test`
3. `Test-AgentCoreSwarmRecall.ps1` — service health
4. `Test-AgentCoreMemoryProjection.ps1` — dirty-state / no active projector check
5. Backup must be within 24h of migration window (§18.13)

### Migration Files (Not Yet Authored)

Convention: `migrations/0001_up_memory_source_systems.sql` + `0001_down_...` (separate up/down per migration)

Order: `0001 → 0002 → 0003 → 0004 → 0005`

Protocol: dry-run (transaction + `ROLLBACK`) → human operator sign-off → execute in transaction → post-checks → `COMMIT` only after all verify. Rollback via tested `down` files if any verify fails.

### No Live Mutation Authorization

`database-plan.md` explicitly states it does not authorize live DB mutation. `Initialize-AgentCore6TB.ps1` destructive provisioning must NOT be re-run. Additive-only; existing tables are untouched.

### Pre-Migration vs Post-Migration Acceptance

**Pre-migration (required before any DDL — see §18.1–18.14):** Covers existing table state, service health, backup proof, restore verification, IDE baseline adoption.

**Post-migration (required only after DDL applied — see §18.21–18.30):** Covers new table existence, HNSW index, seed row counts, existing row count unchanged, tool regression tests, no secrets in catalog rows.

`Test-AgentCoreUnifiedRetrieval.ps1` is a **future/Phase 6 script** — it runs in dry-run/SKIP mode before migration and fully validates only post-migration. It must never cause a hard fail during core rollout phases.

---

## 10. Artifacts Manifest

| Artifact Path | Purpose | Status | Required Next Action |
|---------------|---------|--------|----------------------|
| `D:\github\agentcore-control-plane\database-plan.md` | Unified Memory Catalog design spec (schema_version 2026-06-30) | EXISTS — tracked file | Verify committed (`git status`). No mutation. |
| `C:\Users\ynotf\.cursor\plans\agentcore_swarm_rollout_c2efcae7.plan.md` | Decision-complete normalized rollout plan with all amendments | EXISTS | Read-only reference. This is the master plan. |
| `D:\github\agentcore-control-plane\CONTEXT_BLOCK.md` | Context block for Codex/new-agent onboarding | EXISTS | May need hard-facts update in P8 |
| `D:\github\agentcore-control-plane\AGENTS.md` | Source authority agent contract | EXISTS | No change required this phase |
| `D:\github\agentcore-control-plane\contracts\global-memory-database-contract.json` | Machine-readable DB/memory contract (schema_version 2026-06-21) | EXISTS | Review for alignment with `database-plan.md` in P7 |
| `D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json` | Machine-readable MCP server contract (schema_version 2026-06-26) | EXISTS — **stale** (swarmrecall in `must_not_emit`, missing claude-code/mavis profiles, missing swarmrecall/swarmvault baseline) | Update in P2 |
| `D:\github\agentcore-control-plane\docs\database_overview.md` | DB schema and backup reference | EXISTS | Update after migration in P7 |
| `D:\github\agentcore-control-plane\docs\rollout-runbook.md` | Brief rollout corrective steps | EXISTS — **minimal, needs expansion** | Expand in P8 |
| `D:\github\agentcore-control-plane\docs\AGENTCORE_AUTOMATION_OPERATIONS.md` | Automation/service ownership reference | EXISTS (2026-06-27) | Update monitor removal in P8 |
| `D:\github\agentcore-control-plane\docs\SYSTEM_HANDOVER_BLUEPRINT.md` | Architecture handoff reference | EXISTS (2026-06-26) | Update SwarmRecall MCP posture (was "not broadly exposed" — now mandatory baseline) in P8 |
| `D:\github\agentcore-control-plane\ops\Invoke-AgentCoreMemoryProjector.ps1` | Governed memory pipeline (fan-out from agent_core → SwarmRecall + SwarmVault) | EXISTS | Preserve. Verify adapter in P3. |
| `D:\github\agentcore-control-plane\ops\Test-AgentCoreMemoryProjection.ps1` | Projector validator | EXISTS | Run in P3 and P7 pre-migration gate |
| `D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmRecall.ps1` | SwarmRecall validator | EXISTS | Extend and run in P4 |
| `D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmVault.ps1` | SwarmVault validator | EXISTS | Extend and run in P5 |
| `D:\github\agentcore-control-plane\validators\validate-control-plane.ps1` | Source/live drift gate | EXISTS — **stale** (forbids swarmrecall, must invert) | Update in P2 |
| `D:\github\agentcore-control-plane\docs\evidence\PC-Master-Hardware-Software-Specs.md` | PC hardware/software baseline evidence | EXISTS | Read-only reference |
| `D:\github\agentcore-control-plane\artifacts\incident-2026-06-30\` | Incident reconciliation artifacts directory | **MISSING — does not exist** | Create in P0 |
| `D:\github\agentcore-control-plane\artifacts\incident-2026-06-30\reconciliation-report.md` | P0 incident reconciliation report | **MISSING — does not exist** | Create in P0 (deliverable) |
| `D:\github\agentcore-control-plane\artifacts\backups\` | Timestamped source file backups | EXISTS (dated 2026-06-28) | Extend with P1 preflight backups |
| `D:\github\agentcore-control-plane\docs\prompts\` | Per-IDE cleanup prompts | **MISSING — does not exist** | Create in P6 |
| `D:\github\agentcore-control-plane\artifacts\staging\claude-code\` | Staged Claude Code candidate config | **MISSING — does not exist** | Create in P6 |
| `D:\github\agentcore-control-plane\migrations\` | Migration SQL files | **MISSING — does not exist** | Author in P7 (dry-run only, no apply) |
| `D:\github\agentcore-control-plane\ops\New-AgentCorePerIdePrompts.ps1` | Per-IDE prompt generator | **MISSING — does not exist** | Create in P6 |
| `D:\github\agentcore-control-plane\ops\Test-AgentCoreUnifiedRetrieval.ps1` | Unified retrieval validator (Phase 6, post-migration) | **MISSING — does not exist** | Create in P2 (dry-run/SKIP mode until migration) |
| `D:\github\agentcore-control-plane\ops\Test-AgentCoreRuleConflictScanner.ps1` | Rule conflict detector | **MISSING — does not exist** | Create in P2 |
| `D:\github\agentcore-control-plane\renderers\cursor-global.mcp.json` | Cursor MCP renderer | EXISTS — may be stale | Regenerate in P2 |
| `D:\github\agentcore-control-plane\renderers\minimax.mcp.json` | MiniMax MCP renderer (shared with Mavis — needs split) | EXISTS — **stale** (Mavis not separate) | Update in P2; create `renderers/mavis.mcp.json` |
| `D:\github\agentcore-control-plane\renderers\antigravity.mcp_config.json` | Antigravity MCP renderer | EXISTS | Update with baseline additions in P2 |
| `D:\github\agentcore-control-plane\renderers\openclaw.openclaw.fragment.json` | OpenClaw MCP renderer | EXISTS | Update with baseline additions in P2 |

---

## 11. Files the Next Agent May Change

### Source-Controlled Files — Allowed (with unlock → edit → validate → re-lock; timestamped backup first)

- `docs/handoffs/` — this handoff and future handoffs
- `docs/*.md` — documentation updates per plan
- `docs/prompts/` — per-IDE cleanup prompts (create in P6)
- `contracts/master-mcp-server-config.json` — MCP contract update (P2)
- `contracts/global-memory-database-contract.json` — alignment update if needed (P7)
- `supervisor/servers.json`, `supervisor/servers.yaml` — add swarmrecall/swarmvault defs (P2)
- `scripts/mcp_control_plane.py` — add Claude Code, split Mavis, render swarmrecall/swarmvault (P2)
- `validators/validate-control-plane.ps1` — invert swarmrecall rule, add new assertions (P2)
- `ops/*.ps1` — existing scripts updated; new validators added (P2–P5)
- `registry/tool-registry.json` — regenerated (P2)
- `renderers/*.json` — regenerated + new `mavis.mcp.json` (P2)
- `artifacts/incident-2026-06-30/` — create directory + reconciliation report (P0)
- `artifacts/staging/` — staged candidate configs (P6)
- `artifacts/backups/` — timestamped backups (before any mutation)
- `migrations/` — author migration files (P7, dry-run only, no apply)
- `CONTEXT_BLOCK.md` — hard-facts update if stale (P8)

### Source-Controlled Files — Requires Execution Approval Before Change

- `contracts/` and `validators/` changes that alter enforcement semantics require a validate pass before commit
- `scripts/mcp_control_plane.py` patches require renderer regeneration + validator pass

### Live IDE Configs — Do NOT Edit Directly

Edit only through per-IDE cleanup prompts in `docs/prompts/`. Each prompt instructs the IDE's own agent to manage its config.

| Live Config | IDE | Approach |
|-------------|-----|----------|
| `C:\Users\ynotf\.cursor\mcp.json` | Cursor | Cursor self-prompt via `docs/prompts/cursor-cleanup-prompt.md` |
| `C:\Users\ynotf\.codex\config.toml` | Codex | Codex self-prompt |
| `C:\Users\ynotf\.claude.json` + `C:\Users\ynotf\.claude\config.json` | Claude Code | Claude Code self-prompt; produce staged config in `artifacts/staging/claude-code/` |
| `C:\Users\ynotf\.openclaw\openclaw.json` | OpenClaw | OpenClaw self-prompt |
| `C:\Users\ynotf\.minimax\mcp\mcp.json` | MiniMax | MiniMax self-prompt |
| `C:\Users\ynotf\.mavis\mcp\mcp.json` | Mavis | Mavis self-prompt |
| `C:\Users\ynotf\.gemini\config\mcp_config.json` | Antigravity | Antigravity self-prompt |
| `C:\Users\ynotf\AppData\Roaming\interpreter\config.json` | Open Interpreter | OI self-prompt |

### Protected Runtime Paths — Service / API / CLI Only

- `F:\AgentCore\database_cluster` — PostgreSQL service only
- `F:\AgentCore\agentmemory\swarmrecall\*` — SwarmRecall API/MCP/CLI only
- `F:\AgentCore\agentmemory\swarmvault\*` — SwarmVault MCP/CLI only
- `F:\AgentCore\agentmemory\projection-state\*` — projector script only

### Database Migrations — Manual Approval Only

Migration SQL files may be authored (P7) but must not be executed without:
1. All pre-migration gates passing (§13.1)
2. Dry-run (transaction + `ROLLBACK`) with no errors
3. Human operator sign-off recorded
4. Successful base backup within 24h

---

## 12. Read-Only Commands for Next Agent

Use these commands for evidence gathering. Do not run commands that print secret values.

### Process Scan (P0 — Confirm Rogue PIDs Stopped)

```powershell
# Scan for any remaining swarmvault/source-add/compile/swarmclaw processes
Get-Process | Where-Object { $_.Path -match "swarmvault|swarmclaw|swarmrelay" } | Select-Object Id, Name, Path, StartTime
# Also check command lines via WMI
Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match "source.add|swarmclaw|swarmvault.*compile" } | Select-Object ProcessId, Name, CommandLine
```

### Listener Check (P1 — Verify Runtime Endpoints)

```powershell
# Check PostgreSQL
netstat -ano | findstr :55432

# Check SwarmRecall API
netstat -ano | findstr :3300

# Check Meilisearch
netstat -ano | findstr :7700

# Confirm NO :65432 listener (must return empty)
netstat -ano | findstr :65432

# Confirm Qdrant/n8n excluded from core agent surface
netstat -ano | findstr ":6333 \|:6334 \|:5432 "
```

### SwarmRecall Health Check (P1)

```powershell
# Health endpoint — must return {"status":"ok"} or similar healthy JSON
Invoke-RestMethod -Uri "http://127.0.0.1:3300/api/v1/health" -Method Get
```

### Meilisearch Health Check (P1)

```powershell
# Health endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:7700/health" -Method Get
```

### Ollama Preflight (P1 — Do Not Auto-Pull Models)

```powershell
# Check if Ollama is listening (do NOT pull models)
try { Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get | Select-Object -ExpandProperty models | Select-Object name } catch { Write-Host "Ollama not listening" }
```

### Git Status (P1)

```powershell
Set-Location "D:\github\agentcore-control-plane"
git status
git log --oneline -10
```

### Validator Commands (P2+)

```powershell
# Dry-run source/live drift gate
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\validators\validate-control-plane.ps1" -DryRun

# SwarmRecall validator
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmRecall.ps1"

# SwarmVault validator
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmVault.ps1"

# Memory projection validator
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Test-AgentCoreMemoryProjection.ps1"

# Context-fabric readiness
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Test-AgentCoreContextFabricReadiness.ps1"

# Full runtime suite
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1"

# Live client adoption (run after each client restarted once)
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Test-AgentCoreLiveClientAdoption.ps1"
```

### SwarmVault Source List (Read-Only, P0)

```powershell
# Read sources.json directly (read-only)
Get-Content "F:\AgentCore\agentmemory\swarmvault\state\sources.json" -Raw | ConvertFrom-Json | Select-Object -ExpandProperty sources | Format-Table -AutoSize

# SwarmVault doctor (read-only)
# Run from the swarmvault CLI — do NOT run source-add or compile
swarmvault doctor
swarmvault retrieval status
```

---

## 13. Blockers and Admin Gates

The following items require admin approval, elevated tokens, or operator action before the next agent can proceed:

| Blocker | Scope | Required Action | Who |
|---------|-------|-----------------|-----|
| **Live IDE config drift audit** | P0 | Read-only audit before any mutation; produce `artifacts/incident-2026-06-30/reconciliation-report.md` | Next agent (read-only) |
| **Elevated scheduled task re-registration** | P8 | `Install-AgentCoreOperationalScheduledTasks.ps1` requires elevation to remove monitor tasks. Exact elevated commands must be written to handoff and run by user/admin | User / admin approval |
| **`CONTEXT7_API_KEY` rotation** | P6 | Live literal in `C:\Users\ynotf\.claude.json`. Rotation is a user-approved provider action. Next agent must produce exact removal steps (via Claude Code self-prompt) — never print values | User approval |
| **Secret literal migration** | P6 | `experimental_bearer_token` in Codex config, `authToken`/`refreshToken` in Open Interpreter config, `gateway.auth.token` in OpenClaw config — must migrate to Windows env vars via app self-prompts | User approval |
| **OpenClaw config gap** | P2/P6 | If `gateway.auth.token` literal is still present post-incident, it must be migrated. Do not print value. | OpenClaw self-prompt |
| **Qdrant / RDP / Portainer exposure** | Out of scope | Qdrant `0.0.0.0:6333/6334`, RDP port 3389, Portainer `9443/8005` are LAN-exposed. Document remediation steps; do not execute without admin approval. Out of core rollout scope. | Admin approval |
| **Docker hot data on C: VHDX** | Out of scope | n8n Postgres and Qdrant write through Docker's C: VHDX. Remediation deferred. No Docker mutation without approval. | Admin approval |
| **DB migration execution** | P7 | Blocked until: all pre-migration gates pass, dry-run complete with no errors, human operator sign-off recorded. Do not apply DDL without approval. | Human operator sign-off |
| **AgentCore scheduled task stale args** | P1/P8 | Tasks `PostgresRuntime`/`SwarmRecallApi`/`SwarmRecallMeilisearch` show last result `3221225786` (0xC0000042). Task action args may be stale. Investigate before relying on task-based restart. Exact corrective commands must be written to handoff. | Admin investigation |
| **Partial SwarmVault sources** | P0/P5 | Do not delete partial sources until P0 audit completes. Register managed sources in P5 only WITH ignore/exclude strategy. | Next agent (audit first) |
| **Swarmclaw OOM orphaned artifacts** | P0/P5 | swarmclaw source registration crashed; may have left oversized ingest artifacts. Audit in P0. Clean up in P5 only after P0 report confirms scope. | Next agent (audit first) |
| **Missing `E:\CodexMemory` paths** | P1 | Env vars `CODEX_MEMORY_ROOT` and `CODEX_MEMORY_MARKDOWN_VAULT` are set but paths may not exist. Create `E:\CodexMemory` and `E:\CodexMemory\markdown-vault` in P1 (non-elevated, reversible). | Next agent |

---

## 14. Exact Next-Agent Start Prompt

Copy and paste this prompt to start the next agent session:

---

```
You are continuing the AgentCore Swarm Full Automation Rollout for CHAOSCENTRAL.

Read this handoff document completely before taking any action:
D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md

Also read the master rollout plan:
C:\Users\ynotf\.cursor\plans\agentcore_swarm_rollout_c2efcae7.plan.md

And the database design spec:
D:\github\agentcore-control-plane\database-plan.md

Source authority: D:\github\agentcore-control-plane
D:\MCP-Control-Plane is compatibility/live-ops evidence only. Do not treat it as design authority.

MANDATORY FIRST STEP — P0 INCIDENT RECONCILIATION:
A rogue agent mutated live IDE MCP configs around 2026-06-30 00:42–00:45. Before any mutation:
1. Run a fresh read-only audit of all live IDE MCP configs listed in the handoff Section 6.
2. Diff each against the approved baseline and any artifacts/backups/.
3. Read F:\AgentCore\agentmemory\swarmvault\state\sources.json (read-only). Record partial registrations.
4. Run the read-only process scan commands in handoff Section 12 to confirm rogue PIDs are stopped.
5. Write artifacts/incident-2026-06-30/reconciliation-report.md with findings.
6. Do NOT mutate any file until the P0 report is complete.

After P0 is complete and reviewed:
- Continue through phases P1–P9 in order per handoff Section 7.
- Never start a phase without the previous phase's acceptance criteria met or blockers documented.
- Preserve the memory projector (Invoke-AgentCoreMemoryProjector.ps1) — it is a governed pipeline, not a monitor.
- Remove monitor automations only in P8, only from Install-AgentCoreOperationalScheduledTasks.ps1.
- Do not apply database migrations. Author migration files in P7 (dry-run only). Do not execute DDL.
- Do not print secret values. Do not create .env files.
- Do not edit live IDE configs directly. Use per-IDE cleanup prompts (generated in P6) only.
- Do not write directly to F:\AgentCore protected runtime paths. Use service/API/CLI wrappers only.
- Do not edit MCP configs, renderers, validators, or migrations outside approved phases.
- Do not start or stop services unless validating listeners in P1.
- Do not mutate Docker.
- Do not commit unless explicitly asked after review.

Continue until P9 acceptance is green or every remaining blocker is documented with exact evidence and next commands.
```

---

## 15. Final Readiness Statement

**This handoff is ready for the next agent.**

The document is self-contained. A new agent can begin work using this handoff, `database-plan.md`, and the master rollout plan without reading the original chat session.

### Unresolved Assumptions

The following items were not verified at handoff time and must be confirmed by the next agent during P0/P1:

| Assumption | Must Verify In | Risk if Wrong |
|------------|----------------|---------------|
| Rogue PID 105028 and SwarmVault child PIDs are fully stopped | P0 process scan | Rogue processes could continue mutating state |
| Live IDE configs are in a known (if dirty) state after 00:42–00:45 | P0 config audit | Unknown rogue changes could persist into rollout |
| `swarmvault-mcp.ps1` and `contracts/master-mcp-server-config.json` rogue edits were fully undone | P0 git diff | Stale rogue state could propagate into P2 |
| Partial SwarmVault sources for control-plane/swarmrecall/swarmvault are not corrupted | P0 sources.json read | Corrupted sources could cause P5 SwarmVault validation to produce false results |
| swarmclaw OOM did not leave oversized artifacts in SwarmVault `raw/` | P0 audit | Disk space / retrieval performance impact |
| PostgreSQL `127.0.0.1:55432` is currently listening | P1 netstat | SwarmRecall and gateway cannot function |
| SwarmRecall API `127.0.0.1:3300` is currently healthy | P1 health check | P4 cannot validate; projector fan-out blocked |
| Meilisearch `127.0.0.1:7700` is currently listening | P1 health check | SwarmRecall full-text search degraded |
| `E:\CodexMemory` and `E:\CodexMemory\markdown-vault` need creation | P1 | Env vars point to missing paths |
| `CONTEXT7_API_KEY` literal in `~/.claude.json` has not yet been rotated | P0/P6 | Secret still exposed in Claude Code config |
| AgentCore scheduled tasks `PostgresRuntime`/`SwarmRecallApi`/`SwarmRecallMeilisearch` have stale action args (last result 0xC0000042) | P1 investigation | Boot-time service startup may fail silently |
| `database-plan.md` is committed as a tracked file in git | P7 gate check | §18.1 pre-migration gate fails |

---

*End of handoff document. Source: `D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md`*
