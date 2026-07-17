# System Handover Blueprint

Generated: 2026-06-25
Updated: 2026-07-14

> **Bifrost override:** This handover predates the Bifrost MCP Gateway cutover.
> For non-Swarm IDE setup, follow `PROJECT_ANCHOR.md`,
> `MASTER_CONFIG_AND_PROMPT.md`, and `docs/bifrost/UNIFIED_GATEWAY_SETUP.md`.
> The current IDE route is `agentcore-gateway` → `agentcore-memory`; older
> `global-memory-gateway` statements below are retained as historical memory
> architecture context.

This document is the canonical architecture handoff for the current AgentCore local runtime, storage, and governed memory environment. It is intended for global-controller ingestion and should be treated as an operational dependency map, not as a speculative future-state design.

## Source And Live Roots

- Canonical Git source repo: `D:\github\agentcore-control-plane`
- Current live deployed ops root: `D:\MCP-Control-Plane`
- Active runtime root: `F:\AgentCore`
- Source hardening in the Git repo does not by itself migrate scheduled tasks, WAL archive scripts, or live client configs away from `D:\MCP-Control-Plane`.

## Unified Memory Architecture

- Governed non-Swarm IDE path: `agentcore-gateway` → `agentcore-memory`
- Canonical governed database: PostgreSQL `agent_core` on `127.0.0.1:55432`
- Shared local memory runtime: `SwarmRecall` local API + local database + local Meilisearch
- Shared local retrieval substrate: `SwarmVault`
- Downstream sync model: control-plane-managed projection from governed Postgres memory into `SwarmRecall` and `SwarmVault`
- Default IDE posture: do not expose direct `SwarmRecall` MCP broadly in v1; keep it as a backend runtime/admin surface

## Modular Control-Plane Ownership

- `scripts\mcp_control_plane.py` generates repo-owned MCP surfaces and inventory.
- `contracts\master-mcp-server-config.json` is the machine-readable MCP contract for IDE setup.
- `contracts\global-memory-database-contract.json` is the machine-readable database and memory contract.
- `renderers\*.json` are executable per-client MCP fragments.
- `validators\validate-control-plane.ps1` is the repo/source/live drift gate.
- `ops\*.ps1` own runtime startup, projection, validation, backup, restore, and live adoption checks.
- `supervisor\*`, `registry\*`, and `inventory\*` are generated operating inventories.
- `docs\*.md` are human handoff/runbook surfaces.

Approved client exception:

- `eye2byte` is a user-approved OpenClaw-only MCP server.
- It belongs in `renderers\openclaw.openclaw.fragment.json` and `contracts\master-mcp-server-config.json`.
- It must not be copied into Codex, Cursor, MiniMax, Mavis, or Open Interpreter.

Retired route:

- The retired website-hosting connector is not part of active AgentCore MCP routing and should not be restored into default configs.
- Historical logs, backups, or archived rollback artifacts may still contain retired connector names; those are not active routing authority.

## 1. PostgreSQL And pgvector Status

### Runtime Identity

- Engine: `PostgreSQL 16.6`
- Extension: `pgvector 0.8.2`
- Host: `127.0.0.1`
- Port: `55432`
- Database: `agent_core`

### Authentication And Network Posture

- `listen_addresses = 'localhost'`
- `ssl = on`
- `ssl_min_protocol_version = 'TLSv1.2'`
- `password_encryption = 'scram-sha-256'`
- `pg_hba.conf` allows only localhost SSL connections for approved roles.
- Non-SSL localhost connections are rejected.
- All non-local IP ranges are rejected.
- Operational helper scripts force `PGSSLMODE=require`.

### Roles And Access Classes

- `agent_admin`
  - purpose: migrations, schema maintenance, backup/restore validation
  - direct SQL: yes
  - privilege level: superuser
- `agent_ingest`
  - purpose: gateway and approved ingest writes
  - direct SQL: yes, constrained by grants
  - privilege level: `SELECT` and `INSERT` on approved memory tables
- `agent_read`
  - purpose: read-only inspection and validation
  - direct SQL: yes, read-only
  - privilege level: `SELECT` only
- `postgres`
  - purpose: break-glass local maintenance
  - direct SQL: yes
  - privilege level: superuser

### Isolation And Enforcement Gap

- Row-level security is not the current isolation boundary for the public AgentCore tables.
- Current project/agent isolation is enforced primarily by gateway policy, approved roles, and application behavior.
- Next hardening path is still RLS and/or security-definer-function design, but those schema changes are not part of this handoff.

### Normal IDE Access Rule

- Normal IDE agents must not connect directly to PostgreSQL.
- Normal non-Swarm IDE agents must use `agentcore-gateway` → `agentcore-memory`; `global-memory-gateway` is historical memory rollout terminology in this handover.
- The governed gateway role contract is:
  - `AGENT_CORE_PGUSER=agent_ingest`
  - `AGENT_CORE_PGPASSWORD` resolves from `AGENT_CORE_AGENT_INGEST_PASSWORD`

### Deployment Model

- PostgreSQL is deployed as a native local runtime on Windows filesystems.
- It is not documented here as a Docker container.
- It is not a Windows service in the current control-plane model.
- Cold-boot/startup ownership is handled by Task Scheduler task `\AgentCore\PostgresRuntime`, which runs `D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped`.
- Normal non-Swarm agent access is mediated through `agentcore-gateway` and the stable `agentcore-memory` MCP identity.

Operational model:

1. Local PostgreSQL binaries run from the NVMe runtime tree.
2. `\AgentCore\PostgresRuntime` starts native PostgreSQL at user logon when it is not already running.
3. `agentcore-gateway` → `agentcore-memory` is the MCP access layer for normal non-Swarm IDE agents.
4. Trusted ingest/admin jobs may use direct SQL only when approved by the control plane.

### Initialized Vector And Schema State

- Vector table: `global_vector_memory_store`
- Telemetry table: `agent_cross_project_telemetry`
- Vector dimensions: `1536`
- Distance metric: `cosine`
- Vector index: `hnsw`
- Required extension: `pgcrypto`

### Normalized Schema Tables

- `system_info`
- `projects`
- `project_facts`
- `messages`
- `embeddings`

## 2. Drive Mappings And Directories

### Active 4TB NVMe Runtime Drive

- Drive letter: `F:`
- Volume label: `Agent_Vector_4TB`
- Device: `Samsung SSD 990 PRO with Heatsink 4TB`
- Filesystem: `NTFS`
- Allocation unit: `64 KB`
- Runtime root: `F:\AgentCore`

### Active PostgreSQL And pgvector Paths

- Engine directory: `F:\AgentCore\postgres_runtime_engine\pgsql`
- Data cluster: `F:\AgentCore\database_cluster`

### Active Workspace Roots

- `F:\AgentCore\agents_workspace\Cursor`
- `F:\AgentCore\agents_workspace\Autonomy`
- `F:\AgentCore\agents_workspace\Codex`
- `F:\AgentCore\agents_workspace\OpenClaw`
- `F:\AgentCore\agents_workspace\MiniMax`
- `F:\AgentCore\agents_workspace\AndroidStudio`

### Other Active Runtime Directories

- `F:\AgentCore\ingestion_staging`
- `F:\AgentCore\backups_hot`
- `F:\AgentCore\scratch`

### Standardized Local Memory Roots

- `F:\AgentCore\agentmemory\swarmvault`
- `F:\AgentCore\agentmemory\lcm`
- `F:\AgentCore\agentmemory\swarmclaw`
- `F:\AgentCore\agentmemory\swarmrelay`
- `F:\AgentCore\agentmemory\swarmrecall`

### SwarmVault Runtime Mapping

Standardized SwarmVault root:

- `F:\AgentCore\agentmemory\swarmvault`

Expected internal structure:

- `F:\AgentCore\agentmemory\swarmvault\raw`
- `F:\AgentCore\agentmemory\swarmvault\wiki`
- `F:\AgentCore\agentmemory\swarmvault\state`
- `F:\AgentCore\agentmemory\swarmvault\agent`

Verified local state:

- `F:\AgentCore\agentmemory\swarmvault\raw`
- `F:\AgentCore\agentmemory\swarmvault\wiki`
- `F:\AgentCore\agentmemory\swarmvault\state`
- `F:\AgentCore\agentmemory\swarmvault\agent`
- `F:\AgentCore\agentmemory\swarmvault\swarmvault.config.json`
- `F:\AgentCore\agentmemory\swarmvault\swarmvault.schema.md`

Validated configuration facts:

- local provider type: `heuristic`
- retrieval backend: `sqlite`
- vendored CLI build path: `D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js`
- vendored MCP command shape: `node D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js mcp`

### SwarmRecall Status

SwarmRecall is now running as a local-only AgentCore runtime, but it is not yet enabled in live client MCP configs.

Verified local state:

- Source clone: `D:\github\vendor\swarm\swarmrecall`
- Runtime root: `F:\AgentCore\agentmemory\swarmrecall`
- Local config: `F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json`
- Native Meilisearch binary: `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe`
- Meilisearch data path: `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data`
- HuggingFace cache path: `F:\AgentCore\agentmemory\swarmrecall\hf-cache`
- Local API URL: `http://127.0.0.1:3300`
- Local Meilisearch URL: `http://127.0.0.1:7700`
- Local database: `swarmrecall` on native PostgreSQL at `127.0.0.1:55432`
- Local role: `swarmrecall_app`
- AgentCore scheduled tasks:
  - `\AgentCore\PostgresRuntime`
  - `\AgentCore\SwarmRecallMeilisearch`
  - `\AgentCore\SwarmRecallApi`
- Runtime owner after the 2026-06-26 takeover pass: Windows Task Scheduler, not Cursor background terminals

Validated local-only posture:

- hosted SDK default is neutralized by explicit `SWARMRECALL_API_URL=http://127.0.0.1:3300`
- no Upstash Redis is configured for the local AgentCore path
- Firebase admin credentials are absent, so dashboard auth is disabled for the local path
- API-key registration works locally without printing the key
- CLI local API call succeeds against the local API
- MCP stdio probe succeeds against the local API
- Meilisearch is running natively with `--no-analytics`
- API listener is restricted to `127.0.0.1:3300` only
- exactly one Meilisearch listener is active on `127.0.0.1:7700`
- Meilisearch is launched without `--master-key` in the process command line
- no `.env` files were created for the local runtime
- persistent Meilisearch data is on `F:`
- aggregate runtime validator passes: `D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1`

Required live exception already made:

- The active PostgreSQL `pg_hba.conf` at `F:\AgentCore\database_cluster\pg_hba.conf` was extended with scoped `hostssl` localhost rules for:
  - database `swarmrecall`
  - role `swarmrecall_app`
- This live auth edit was required to preserve the least-privilege local-only design on the existing native PostgreSQL engine.
- Rollback copy: `E:\AgentCoreBackups\agentcore-control-plane\20260625-225901\live-postgres-auth\20260625-231022\pg_hba.conf`

Current non-activation boundaries:

- no live client MCP config has been edited to point at SwarmRecall
- no hosted URL may be active in AgentCore wrappers/config
- SwarmRecall does not replace `global-memory-gateway` as the governed cross-project writer

### AgentCore Runtime Automation

The 2026-06-26 takeover pass added these repo-owned operations scripts:

- `D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1`
- `D:\github\agentcore-control-plane\ops\Start-AgentCoreSwarmRecallComponent.ps1`
- `D:\github\agentcore-control-plane\ops\Install-AgentCoreSwarmRecallScheduledTasks.ps1`
- `D:\github\agentcore-control-plane\ops\Stop-AgentCoreSwarmRecallRuntime.ps1`
- `D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1`

The PostgreSQL and SwarmRecall scheduled tasks are current-user logon tasks. They are intentionally limited-runlevel tasks because the native runtime paths do not require administrative privileges, and highest-runlevel registration failed from the non-elevated Codex inner shell.

Codex automations created for ongoing monitoring:

- `agentcore-context-window-optimizer`
- `agentcore-pgvector-database-monitor`
- `agentcore-rag-runtime-monitor`
- `agentcore-mcp-drift-monitor`

These automations are active on the initial high-frequency stabilization cadence. They are monitors and constrained repair agents; broad live IDE MCP rollout remains a separate controlled change.

## 3. Memory Pipelines

### Governed Cross-Project Memory Path

Normal IDE flow:

1. IDE agent calls:
   - `memory_append`
   - `memory_search`
   - `memory_state`
2. Request goes to `global-memory-gateway`.
3. Gateway performs:
   - secret rejection
   - metadata validation
   - embedding generation
   - PostgreSQL write/read mediation
4. Storage lands in PostgreSQL `agent_core`.

### Embedding Contract

- provider mode: `auto`
- preferred provider: `openai_text_embedding_3_small`
- preferred model: `text-embedding-3-small`
- vector dimensions: `1536`
- offline fallback: `local_hash_v1`

### lossless-claw And DAG-Based Summarization

Source repo:

- `D:\github\vendor\memory\lossless-claw`

Standardized runtime root:

- `F:\AgentCore\agentmemory\lcm`

Documented role:

- OpenClaw plugin that replaces sliding-window compaction with DAG-based long-term memory and recall tools.
- Uses the provider configuration already present in OpenClaw for summarization.
- Exposes memory behavior through tools such as:
  - `lcm_grep`
  - `lcm_describe`
  - `lcm_expand`

### lossless-memory4agent

Source repo:

- `D:\github\vendor\memory\lossless-memory4agent`

Standardized runtime root:

- `F:\AgentCore\agentmemory\lcm`

Documented role:

- Standalone DAG-based memory SDK.
- Stores messages in SQLite and performs hierarchical summarization/compression.

### Underlying SQLite Reality

Standardized intended AgentCore location:

- `F:\AgentCore\agentmemory\lcm`

Upstream default locations:

- `~/.openclaw/lcm.db` for `lossless-claw`
- `~/.lossless-memory/lcm.db` for `lossless-memory4agent`

Actually detected local SQLite file at the time of the verified hardening pass:

- `C:\Users\ynotf\.openclaw\agents\main\qmd\xdg-cache\qmd\index.sqlite`

Important constraint:

- The control-plane docs explicitly note that the requested AgentCore-side LCM file was not present during the hardening pass.
- Therefore, the standardized `F:\AgentCore\agentmemory\lcm` root exists as the intended runtime placement, but the verified currently detected local SQLite artifact remains on `C:`.

### Rolling Context Parameters

No concrete numeric rolling-context parameters are documented in the verified control-plane artifacts.

What is documented instead:

- `lossless-claw` is DAG-based long-term context.
- Summarization behavior is inherited from the local OpenClaw/provider configuration.
- The control plane standardizes placement and governance boundaries, but does not define token-window, chunk-depth, or summary-threshold numbers.

Dependency note:

- Rolling-context numeric values should be treated as owned by the OpenClaw/lossless-claw runtime configuration, not by the PostgreSQL control plane.

## 4. External Drive Allocation

### 6TB External Drive Role

There are two relevant path conventions in the current environment.

### A. Live / Inherited Archive Contract

- Drive letter: `E:`
- Volume label: `Agent_Core_6TB`
- Archive root: `E:\AgentCoreArchive`

Documented initialized archive layout:

- `E:\AgentCoreArchive\backups_cold`
- `E:\AgentCoreArchive\database_snapshots`
- `E:\AgentCoreArchive\raw_exports`

Database-specific archive paths:

- WAL archive root: `E:\AgentCoreArchive\backups_cold\pgvector\wal`
- Base backup root: `E:\AgentCoreArchive\backups_cold\pgvector\base`

Legacy rollback copy:

- `E:\database_cluster`

Do not treat `E:\database_cluster` as the active database cluster unless performing an explicit rollback.

### B. Newer Standardized Backup Layout

Separately, the newer storage-layout standard defines:

- `E:\AgentCoreBackups`

Verified present backup roots:

- `E:\AgentCoreBackups\postgres`
- `E:\AgentCoreBackups\agentmemory`
- `E:\AgentCoreBackups\swarmvault-exports`
- `E:\AgentCoreBackups\logs`

### Dependency-Safe Interpretation

To avoid breaking inherited dependencies:

- treat `E:\AgentCoreArchive` as the active database/archive dependency root for current PostgreSQL archive references
- treat `E:\AgentCoreBackups` as the newer standardized backup taxonomy for broader backup categories

Do not collapse the two path families without a deliberate migration because active database/archive references still point at `E:\AgentCoreArchive`.

### 6TB Drive Initialization Scope

Verified initialized on the 6TB external drive:

- archive directories
- backup directories
- snapshot/export paths
- WAL/base-backup archive targets

Not verified on the 6TB external drive:

- git branch trees
- repo clones
- active runtime caches for agent execution
- SwarmRecall runtime pools

Operational role of the 6TB drive:

- cold archive
- database snapshots
- exports
- backup storage

It is not the active runtime execution path.

## 5. Environment Variable And Gateway Dependency Notes

AgentCore does not use `.env` files.

All secrets and runtime credentials are stored in Windows Environment Variables.

Relevant governed gateway variables:

- `AGENT_CORE_AGENT_ADMIN_PASSWORD`
- `AGENT_CORE_AGENT_INGEST_PASSWORD`
- `AGENT_CORE_AGENT_READ_PASSWORD`
- `AGENT_CORE_POSTGRES_PASSWORD`
- `AGENT_CORE_PGPASSWORD`
- `AGENT_CORE_PGUSER`
- `AGENT_CORE_SWARMRECALL_DB_PASSWORD`
- `AGENT_CORE_SWARMRECALL_MEILI_MASTER_KEY`
- `AGENT_CORE_SWARMRECALL_API_KEY`
- future `AGENT_CORE_*` variables as needed

Gateway policy:

- `AGENT_CORE_PGUSER` must resolve to `agent_ingest`
- `AGENT_CORE_PGPASSWORD` must resolve from `AGENT_CORE_AGENT_INGEST_PASSWORD`
- normal IDE agents must not direct-SQL into PostgreSQL

## 6. Controller-Safe Summary

- Active runtime root: `F:\AgentCore`
- Active PostgreSQL engine: `F:\AgentCore\postgres_runtime_engine\pgsql`
- Active PostgreSQL data: `F:\AgentCore\database_cluster`
- DB endpoint: `127.0.0.1:55432/agent_core`
- Governed MCP memory writer: `global-memory-gateway`
- Normal gateway DB role: `agent_ingest`
- Authentication posture: `SSL/TLSv1.2 + SCRAM-SHA-256 + localhost-only HBA`
- Vector store: `global_vector_memory_store`
- Vector dimensions: `1536`
- Vector index and metric: `hnsw + cosine`
- SwarmVault standardized runtime root: `F:\AgentCore\agentmemory\swarmvault`
- Expected SwarmVault inner dirs: `raw/`, `wiki/`, `state/`, `agent/`
- SwarmVault runtime is initialized and validated locally under `F:\AgentCore\agentmemory\swarmvault`
- SwarmRecall runtime root: `F:\AgentCore\agentmemory\swarmrecall`
- SwarmRecall local API: `http://127.0.0.1:3300`
- SwarmRecall local search: native Meilisearch at `http://127.0.0.1:7700`
- SwarmRecall database: separate `swarmrecall` database on native local PostgreSQL, not Docker
- SwarmRecall role: `swarmrecall_app`
- SwarmRecall local MCP probe passes, but live client config enablement has not been rolled out
- lossless-claw standardized runtime root: `F:\AgentCore\agentmemory\lcm`
- Actually detected local SQLite artifact: `C:\Users\ynotf\.openclaw\agents\main\qmd\xdg-cache\qmd\index.sqlite`
- Current archive dependency root: `E:\AgentCoreArchive`
- New standardized backup root: `E:\AgentCoreBackups`
- No verified git branch trees on the 6TB drive

## 7. Open Gaps And Do-Not-Assume Rules

- Do not route SwarmRecall to hosted defaults; require an explicit local API override.
- Do not confuse runtime ownership with live client MCP exposure; SwarmRecall is now service-owned by AgentCore scheduled tasks, but live IDE MCP configs still require a separate controlled rollout.
- Do not use hidden Docker volumes for persistent SwarmVault or SwarmRecall storage.
- Do not assume `lossless-claw` has already migrated its SQLite database onto `F:\AgentCore\agentmemory\lcm`.
- Do not collapse `E:\AgentCoreArchive` into `E:\AgentCoreBackups` without an explicit migration plan.
- Do not bypass `agentcore-gateway` / `agentcore-memory` for normal non-Swarm IDE memory health/status or future governed memory writes.
- Do not remove the OpenClaw-only `eye2byte` MCP as drift unless Tony explicitly retires it.
- Do not restore retired website-hosting MCP routes unless Tony explicitly re-enables them.
- Do not assume rolling-context numeric parameters are defined by the control plane; they are not documented here.
