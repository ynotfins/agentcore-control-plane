# MEMORY_STACK_AUDIT — CHAOSCENTRAL

**Generated:** 2026-07-03
**Scope:** Inventory, posture, and audit of every memory and context backend installed on CHAOSCENTRAL. Maps each component to its role in the architecture options.
**Source contracts:**
- `D:\github\agentcore-control-plane\docs\memory_system.md`
- `D:\github\agentcore-control-plane\docs\SYSTEM_HANDOVER_BLUEPRINT.md`
- `D:\github\agentcore-control-plane\database-plan.md` (§3.3, §4)
- `D:\github\agentcore-control-plane\contracts\global-memory-database-contract.json`
- `D:\github\agentcore-control-plane\supervisor\servers.json`

---

## 1. Memory Plane Taxonomy

Per `database-plan.md` §4, AgentCore models memory as a set of orthogonal **planes**. The audit below classifies every installed backend against this taxonomy.

| Plane | Role | Where it lives | Audited state |
|-------|------|-----------------|---------------|
| **Working context** | In-process session state | (no persistence) | n/a |
| **Canonical structured memory** | Source of truth for cross-project facts | PostgreSQL `agent_core` on `127.0.0.1:55432` | **Cold** at audit; schema applied |
| **Vector catalog** | Embeddings + similarity search | `agent_core.global_vector_memory_store` (pgvector 1536-d HNSW cosine) | Schema applied; cold |
| **Semantic recall** | Episode retrieval (full-text + semantic) | SwarmRecall (`swarmrecall` DB + Meilisearch `127.0.0.1:7700`) | Meilisearch running; API cold |
| **Local RAG / knowledge** | Wiki + graph + context packs + task ledger | SwarmVault file system at `F:\AgentCore\agentmemory\swarmvault` | File state present; native CLI build present |
| **Human notes** | Long-form decisions, runbooks, handoffs | Obsidian at `D:\Obsidian\Dungeon Vault\` (REST `https://127.0.0.1:27124`) | Vault present; REST cold |
| **Unified memory catalog** | Future cross-backend index | (target — `agent_core` new tables) | **Not yet migrated** |
| **LCM/lossless history** | Future lossless source-system type | (deferred) | **Deferred** |

Each plane is governed by a write policy in `database-plan.md` §4. Normal agents may write only through `global-memory-gateway` (now retired — see §2) or, in the new baseline, **through the SwarmRecall MCP**. Direct filesystem writes to SwarmVault or Obsidian by normal agents are forbidden.

---

## 2. Critical Posture Change — `global-memory-gateway` Retired

The most recent source commit on `agentcore-control-plane` is *"Native-first memory: retire global-memory-gateway from baseline"* (2026-07-01). The contract (`master-mcp-server-config.json` v2026-06-26, `normal_memory_rule`) states explicitly:

> *"normal durable memory now routes through native SwarmRecall (global-memory-gateway retired from the baseline)."*

Therefore:

- **Normal-agent writes** to durable memory: SwarmRecall MCP → `swarmrecall` DB + Meilisearch.
- **Direct Postgres for normal agents**: still forbidden (unchanged from pre-retirement posture).
- **`global-memory-gateway`**: present in older docs, retired from the live contract, still referenced by some IDEs that have not yet run their cleanup prompts.

Architecture for the future must assume **SwarmRecall is the canonical durable plane for normal agents**. Any plan that proposes bringing `global-memory-gateway` back as the central broker contradicts the current source authority and is rejected at the architecture-comparison step.

---

## 3. PostgreSQL Cluster

### 3.1 Identity

| Item | Value |
|------|-------|
| Engine | PostgreSQL 16.6 |
| Vector extension | pgvector 0.8.2 |
| Engine path | `F:\AgentCore\postgres_runtime_engine\pgsql\bin\` |
| Cluster data dir | `F:\AgentCore\database_cluster\` |
| Host / Port | `127.0.0.1` : `55432` |
| `listen_addresses` | `localhost` |
| `ssl` | on, min TLSv1.2 |
| `password_encryption` | scram-sha-256 |
| Startup task | `\AgentCore\PostgresRuntime` |

### 3.2 Databases

| Database | Purpose | Tables |
|----------|---------|--------|
| `agent_core` | Governed memory spine | `system_info`, `projects`, `project_facts`, `messages`, `embeddings`, `global_vector_memory_store` (HNSW cosine, 1536-d), `agent_cross_project_telemetry` |
| `swarmrecall` | SwarmRecall runtime | (managed by SwarmRecall migrations) |

The two databases **must remain separate**. `database-plan.md` §2 explicitly forbids merging them.

### 3.3 Roles

| Role | Privileges | Used by |
|------|-----------|---------|
| `agent_read` | SELECT only | Validators, projector reads |
| `agent_ingest` | SELECT + INSERT on approved tables | Gateway (now retired), approved ingest runners |
| `agent_admin` | Superuser | Migrations, backup/restore, maintenance |
| `postgres` | Superuser (break-glass) | Local break-glass only |

`pg_hba.conf` allows **only `hostssl localhost`** for approved roles. Non-SSL localhost and non-local IPs are rejected. This is enforced and documented.

### 3.4 Auth Posture (live exception)

Per `SYSTEM_HANDOVER_BLUEPRINT.md` §2, the live `pg_hba.conf` was extended on 2026-06-25 to allow scoped `hostssl` localhost authentication for `swarmrecall` DB / `swarmrecall_app` role. The rollback copy is preserved at `E:\AgentCoreBackups\agentcore-control-plane\20260625-225901\live-postgres-auth\20260625-231022\pg_hba.conf`.

Correction (2026-07-15): `pg_hba.conf` owns authentication rules only. SQL ownership, `GRANT`/`REVOKE`, row-level security policies, and `SECURITY DEFINER` functions own authorization.

### 3.5 State at Audit

- Listener on `127.0.0.1:55432`: **not active at the audit moment** (the cold-start task is responsible).
- Cluster data dir: intact, files present.
- WAL archive target: `E:\AgentCoreArchive\backups_cold\pgvector\wal\`.
- Base backup target: `E:\AgentCoreArchive\backups_cold\pgvector\base\`.
- Backup scripts in `ops\`: `Backup-AgentCorePostgres.ps1`, `Start-AgentCorePostgres.ps1`, `Restore-AgentCorePostgres.ps1`.

### 3.6 Isolation Gap

Row-level security is **not** the isolation boundary. Isolation today rests on gateway policy + role grants + application behavior. RLS is in the hardening backlog, not in this handoff. The audit notes this as a known gap, not a blocker.

---

## 4. SwarmRecall

| Item | Value |
|------|-------|
| Source | `D:\github\vendor\swarm\swarmrecall` |
| Runtime root | `F:\AgentCore\agentmemory\swarmrecall` |
| API endpoint | `http://127.0.0.1:3300` |
| Local API-key env | `AGENT_CORE_SWARMRECALL_API_KEY` |
| Local Meilisearch URL | `http://127.0.0.1:7700` |
| Local Meilisearch master-key env | `AGENT_CORE_SWARMRECALL_MEILI_MASTER_KEY` |
| Native Meilisearch binary | `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe` |
| Database | `swarmrecall` on `127.0.0.1:55432` |
| Role | `swarmrecall_app` |
| Scheduled tasks | `\AgentCore\SwarmRecallMeilisearch`, `\AgentCore\SwarmRecallApi` |

### 4.1 State at Audit

- Meilisearch process: **running** (1 instance, no `--master-key` in args).
- SwarmRecall API: **not running** at audit moment (Task Scheduler not triggered or service start failed).

### 4.2 Local-Only Posture Verification (per blueprint)

- API bound to `127.0.0.1:3300` only.
- No Upstash configured.
- No Firebase dashboard auth.
- API-key registration works locally.
- CLI local call succeeds.
- MCP stdio probe succeeds.
- Meilisearch launched with `--no-analytics`.
- No `.env` files in runtime root.
- Exactly one Meilisearch listener present.

### 4.3 Risk: "Broad MCP Rollout"

`global-memory-database-contract.json` `projection_layer.swarmrecall.broad_mcp_rollout` is `false`. The current contract does **not** authorize SwarmRecall MCP to be widely emitted to IDEs. Only the governed wrapper `Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp` may launch the MCP. Architecture must respect this constraint — a "make every IDE talk to SwarmRecall directly" plan is not authorized by the contract.

---

## 5. SwarmVault

| Item | Value |
|------|-------|
| Source | `D:\github\vendor\swarm\swarmvault` |
| Vendored CLI build | `D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js` |
| Vendored MCP command shape | `node …\swarmvault\packages\cli\dist\index.js mcp` |
| Runtime root | `F:\AgentCore\agentmemory\swarmvault` |
| Config | `swarmvault.config.json` |
| Schema doc | `swarmvault.schema.md` |
| Internal layout | `raw\`, `wiki\`, `state\`, `agent\` |
| Provider | heuristic |
| Retrieval backend | sqlite |
| No `.env` in runtime | confirmed |

### 5.1 Current Registered Sources (per doctor)

- 5 managed sources: `swarmvault-staging`, `agentcore-control-plane`, `swarmrecall`, `swarmvault`, `swarmclaw`.
- 2465 raw sources, 7071 pages, 20545 nodes.
- Raw disk footprint ~22 MB (no balloon).
- Not registered: `swarmrelay`, `swarmfeed`, `swarmdock`.

### 5.2 State at Audit

- File system: intact, all four required dirs (`raw`, `wiki`, `state`, `agent`) present.
- Native CLI build: present.
- Doctor health: healthy (per rollout report).
- Known issue: `swarmclaw` registration may be OOM-incomplete; re-validate.
- Known issue: `query` validator timeout (heuristic query over ~7071 pages is slow); tuning required.

### 5.3 Safe Source Registration Strategy

Per `SWARMVAULT_SOURCE_REGISTRATION.md`:
- Do NOT run broad recursive `source add` on vendor repos.
- Always exclude `node_modules`, `.next`, `dist`, `build`, `coverage`, `.turbo`, `.pnpm-store`, `.cache`, `.git`, `out`, `*.log`, generated artifacts.
- Do not register secrets, `.env`, runtime DB dumps, `F:\AgentCore` raw state.
- Native-first proof: `node <cli> doctor --json`, `node <cli> retrieval status`.

---

## 6. Obsidian Vault

| Item | Value |
|------|-------|
| Vault path | `D:\Obsidian\Dungeon Vault\` |
| Local REST endpoint | `https://127.0.0.1:27124` (TLS) |
| Env vars | `OBSIDIAN_API_KEY`, `OBSIDIAN_LOCAL_REST_API`, `OBSIDIAN_BASE_URL` |
| MCP launch | `pwsh -File C:\Users\ynotf\.openclaw\start-obsidian-mcp-server.ps1` |

### 6.1 State at Audit

- Vault directory: present.
- Obsidian app: not running with REST API at audit moment (REST listener absent).
- Cleanup prompt (`docs\prompts\claude-desktop-obsidian-cleanup-prompt.md`) instructs operator to enable the Local REST API plugin before relying on the MCP.

### 6.2 Risk: Filesystem Writes

`database-plan.md` §4 forbids filesystem writes to Obsidian while Obsidian is running. Writes must go through the `obsidian-vault` MCP REST path only.

---

## 7. Lossless Claw (LCM)

| Item | Value |
|------|-------|
| Path | `C:\Users\ynotf\.openclaw\lossless-claw\` |
| Files | `config.foundation.json` (468 B), `lcm.sqlite` (4.6 MB), `files\` |
| QMD index | `C:\Users\ynotf\.openclaw\agents\main\qmd\xdg-cache\qmd\index.sqlite` |

### 7.1 Role in the Architecture

Per `memory_system.md`: *"QMD/LCM-style local memory remains separate and must not bypass the gateway for global memory writes."* LCM is local-only retrieval/context, **not** the canonical durable memory. Future `memory_catalog` may register LCM as a *source-system type* but the canonical writes still go through the (retired) gateway → SwarmRecall path.

### 7.2 State at Audit

- `lcm.sqlite` 4.6 MB — active local state.
- `config.foundation.json` present.
- `files\` directory present.

### 7.3 Risk

Lossless Claw grows unbounded unless compaction is added. The rollout does not currently schedule LCM compaction.

---

## 8. Codex Native Memory Plane

| Item | Value |
|------|-------|
| Plugin | `codex-lossless-memory-pack@personal` |
| SQLite DBs | `memories_1.sqlite` (4.3 MB), `logs_2.sqlite` (1.4 GB), `goals_1.sqlite` (24 KB), `state_5.sqlite` (1.8 MB) |
| Markdown pack | `~/.codex\memories\MEMORY.md`, `memory_summary.md`, `raw_memories.md` |
| Context window | 1,000,000 tokens |
| Hook | `Stop` → `codex-stop-audit.ps1` |

### 8.1 Risk

`logs_2.sqlite` at 1.4 GB is large. The audit did not inspect its growth pattern, but no rotation policy is documented. Future architecture should set a budget (e.g., 200 MB) and a TTL.

---

## 9. OpenClaw Per-Agent Memory

| Item | Value |
|------|-------|
| Path | `C:\Users\ynotf\.openclaw\memory\` |
| Files | `main.sqlite`, `manager.sqlite`, `sparky-chief-product-quality-officer.sqlite` (~6.5 MB), `sparky_ceo_bot.sqlite` (~6.5 MB), `qmd.foundation.json` |

These are per-agent local memory stores. They are independent of LCM and the governed memory. They duplicate a small subset of what LCM already holds, suggesting a future consolidation opportunity.

---

## 10. Pre-Wired Optional Vector Stores

`F:\VectorDB\` contains four pre-wired directories: `chroma\`, `lancedb\`, `pgvector\`, `qdrant\`. None host active runtime. They are placeholders. The live vector plane is pgvector inside PostgreSQL. The optional stores could be activated for specialized workloads (e.g., high-dimensional embeddings, time-series indexing) but are not part of the baseline architecture.

---

## 11. Unified Memory Catalog (Target — Not Yet Created)

Per `database-plan.md` §1 and `migrations\README.md`, five additive migration pairs are authored but **not applied**:

| Migration | Purpose |
|-----------|---------|
| `0001_up/down_memory_source_systems` | Register each backend as a source-system row |
| `0002_up/down_memory_catalog` | Cross-backend catalog of memory entries |
| `0003_up/down_retrieval_events_context_packs` | Retrieval event ledger + context-pack definitions |
| `0004_up/down_agent_run_ledger_quality_scores` | Per-agent run ledger + quality scoring |
| `0005_seed_source_systems` | Seed row for each existing source-system |

Apply is **blocked** until §13/§18 gates pass (native stability + projector verification). The catalog is what would let a future agent discover that "the answer is in SwarmVault, not in agent_core" automatically.

---

## 12. Backup & Restore Posture

| Backup kind | Target | Frequency | Script |
|-------------|--------|-----------|--------|
| Postgres WAL archive | `E:\AgentCoreArchive\backups_cold\pgvector\wal\` | continuous | (PG native) |
| Postgres base backup | `E:\AgentCoreArchive\backups_cold\pgvector\base\` | (scheduled) | `Backup-AgentCorePostgres.ps1` |
| Hot backup | `F:\AgentCore\backups_hot\` | (scheduled) | (PG tools) |
| Source backups | `artifacts\backups\…` | pre-mutation | manual via `Initialize-AgentCoreOperationalScheduledTasks.ps1` |

The `artifacts\backup-manifest.json` indexes all rollback copies under the `rollback` location. The pre-mutation backups from the 2026-06-30 rollout are in `artifacts\backups\20260630-042231-p2-baseline\`.

---

## 13. Memory Stack Health Matrix

| Component | Configured | Files present | Listener up | Validator green | Risk |
|-----------|------------|---------------|-------------|-----------------|------|
| PostgreSQL + pgvector | Yes | Yes | **Cold** | (cold) | Cold-start depends on Task Scheduler |
| `agent_core` schema | Yes | Yes | n/a | Yes | — |
| `swarmrecall` DB | Yes | Yes | n/a | Yes | — |
| SwarmRecall API | Yes | Yes | **Cold** | (warm-up needed) | Task `\AgentCore\SwarmRecallApi` must run |
| Meilisearch | Yes | Yes | **Up** | Yes | — |
| SwarmVault | Yes | Yes | n/a (file) | Yes (doctor) | `query` slow; swarmclaw re-validate |
| Obsidian | Yes | Yes | **Cold** | n/a | Must enable Local REST plugin |
| Lossless Claw | Yes | Yes | n/a | n/a | No compaction policy |
| Codex memories | Yes | Yes | n/a | n/a | logs DB growing unbounded |
| OpenClaw memory | Yes | Yes | n/a | n/a | Duplication with LCM |
| Pre-wired chroma/lancedb/qdrant | No | dirs only | n/a | n/a | Not in baseline |
| Unified memory catalog | Authored | Yes | n/a | (dry-run SKIP) | Migrations not applied |

---

## 14. Architectural Implications

1. **The canonical durable memory plane is SwarmRecall**, not the retired gateway. Architecture must reflect this.
2. **PostgreSQL is cold-start dependent.** Any "always-on gateway" plan that assumes PG is already running on `127.0.0.1:55432` is fragile unless paired with a deterministic cold-start contract.
3. **Obsidian is human-only at runtime.** Treat it as an external REST service that may or may not be up.
4. **SwarmVault is the canonical file-based RAG.** `query` performance tuning is a known soft blocker.
5. **Lossless Claw is a parallel plane**, not the canonical durable store. Architecture must avoid dual-write duplication.
6. **The unified memory catalog is the future target.** Today, an agent must know which backend to query; the catalog would remove that requirement. Until it ships, the architecture must explicitly document which backend to query for each request type.
7. **Backup posture is acceptable** for a single-node host, but E: is only 932 GB (not 10 TB) — long-term retention may need off-host cold storage.

The next deliverable verifies whether the assumption of a "universal OpenAI-compatible gateway at localhost:3000/v1 and /mcp" matches reality.