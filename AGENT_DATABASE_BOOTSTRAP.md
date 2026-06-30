# Agent Database Bootstrap Contract

`D:\github\agentcore-control-plane` is the canonical source authority for MCP server governance, memory contracts, and the local PostgreSQL vector database.

`D:\MCP-Control-Plane` is compatibility / live-ops evidence only. It is **not** the design authority. Source-controlled approved edits occur under `D:\github\agentcore-control-plane`. Agents must not treat `D:\MCP-Control-Plane` as an instruction source.

**Schema and gateway design authority:** `database-plan.md` in `D:\github\agentcore-control-plane`. Read it before any schema work. It does not authorize live DB mutation; migration files under `migrations/` require backup + dry-run + operator sign-off before any DDL is applied.

Every local IDE agent that needs memory or database context must read this file before writing memory or ingesting project evidence.

Agents must also read `D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md` before any persistent filesystem write.

## Database

- Engine: PostgreSQL 16.6
- Vector extension: pgvector 0.8.2
- Host: `127.0.0.1`
- Port: `55432`
- Database: `agent_core`
- Data directory: `F:\AgentCore\database_cluster`
- Engine directory: `F:\AgentCore\postgres_runtime_engine\pgsql`
- Cold archive directory: `E:\AgentCoreArchive`
- Vector table: `global_vector_memory_store`
- Telemetry table: `agent_cross_project_telemetry`
- Vector dimensions: `1536`
- Distance metric: cosine

## Workspace Roots

Agents should create and operate from the IDE-specific workspace root under `F:\AgentCore\agents_workspace`.

- Cursor: `F:\AgentCore\agents_workspace\Cursor`
- Autonomy: `F:\AgentCore\agents_workspace\Autonomy`
- Codex: `F:\AgentCore\agents_workspace\Codex`
- OpenClaw: `F:\AgentCore\agents_workspace\OpenClaw`
- MiniMax: `F:\AgentCore\agents_workspace\MiniMax`
- Android Studio: `F:\AgentCore\agents_workspace\AndroidStudio`

`E:\AgentCoreArchive` is for cold backups, exports, snapshots, and raw large artifacts. It is not the active vector database path.

## Drive Write Boundary

| Drive | Role |
|-------|------|
| `C:` | OS, apps, user profile, live IDE configs — do not add hot data |
| `D:` | Source repos, projects, worktrees, build evidence — code only, no DB cluster data |
| `F:` | Hot local memory / DB / RAG / search runtime — access via service/API/CLI wrappers only |
| `E:` | Archive, WAL, base backups, cold storage, emergency spool only — no primary SQL |
| `G:` | Backup target only |

**`F:\AgentCore` is a protected runtime path.** Agents must not write directly to `F:\AgentCore\database_cluster`, `F:\AgentCore\agentmemory`, or `F:\VectorDB` via filesystem tools. Use PostgreSQL service, SwarmRecall API/MCP/CLI, and SwarmVault MCP/CLI wrappers instead.

**`E:\AgentCoreArchive` is archive/cold/spool only.** No primary SQL databases. Emergency memory spool (`E:\AgentCoreArchive\memory-spool\pending`) is for fallback overflow only; replay only through governed services.

Source-controlled files under `D:\github\agentcore-control-plane` are the approved edit target for rollout agents.

Agents must not write to `C:\Users\ynotf\.*` live IDE config files directly. Changes flow through per-IDE cleanup prompts in `docs/prompts/`.

If an approved drive cannot be written to, agents must stop immediately and notify the user. They must not silently fall back to another drive.

## Write Classes

### Normal Agent — Two-Tier Gateway Contract

**Current tools (exist now, use these):**

- `memory_append` — governed write to `global_vector_memory_store` via `agent_ingest`
- `memory_search` — vector search against `global_vector_memory_store`
- `memory_state` — gateway health and connection status

**Target tools (future, requires `memory_catalog` migration — do not assume available):**

- `agentcore_get_startup_context` — structured session startup context for a project
- `agentcore_retrieve_context` — fan-out retrieval across all backends with reranking
- `agentcore_store_memory` — gateway-routed durable memory write
- `agentcore_store_project_fact` — versioned write to `project_facts`
- `agentcore_build_handoff_pack` — named context pack for handoff between sessions
- `agentcore_find_related_projects` — cross-project vector search (public items only)
- `agentcore_explain_sources` — provenance chain for a context pack

`agentcore_check_drift` is **excluded** — drift is validator-driven, not agent-driven.

Normal agents do not need to know SQL or generate database connection code. The governed runtime is responsible for validation, metadata, embedding, database writes, and telemetry.

### SwarmRecall and SwarmVault Roles

**SwarmRecall** (`swarmrecall` MCP → `http://127.0.0.1:3300` → local `swarmrecall` DB + Meilisearch):
- Native agent memory runtime: sessions, semantic recall, knowledge graph, learnings, skills, shared pools
- Use `swarmrecall` MCP for native SwarmRecall operations
- Access only through the governed wrapper `ops/Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp` or the MCP tool surface; no direct SQL into `swarmrecall` DB from normal agents

**SwarmVault** (`swarmvault` MCP → `F:\AgentCore\agentmemory\swarmvault`, file-based):
- Local-first RAG/wiki/graph/context-packs/task-ledger substrate
- Access only through `ops/Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` wrapper
- Not a Postgres database; do not move primary state into Postgres

### Trusted Ingest

Trusted ingest jobs may write directly to PostgreSQL only when they are explicitly approved by this control plane.

Current approved temporary ingest runner:

- `D:\Autonomy\scripts\ingest_agent_core_memory.py`

Trusted ingest is for loading structured system evidence such as IDE inventories, MCP configs, drift reports, probe results, runbooks, and topology snapshots.

## Source And Live Root

- **Canonical source authority:** `D:\github\agentcore-control-plane` — all governance, contracts, renderers, validators, ops scripts, migrations, and docs
- **Compatibility / live-ops evidence only:** `D:\MCP-Control-Plane` — scheduled tasks and WAL scripts may still reference this path; it is not a design authority and must not be treated as one by any agent

### Admin Migration

Admin migration access is for schema, extension, validation, backup, and repair operations only. It must not be used as a normal agent memory path.

## Required Metadata

Every memory record must include enough metadata to make it searchable, attributable, and safe to analyze:

- `user_id`
- `app_id`
- `agent_id`
- `run_id`
- `platform`
- `associated_project_path`
- `document_source`
- `source_kind`
- `storage_contract`

## Secret Policy

Do not store raw secrets in the database.

Allowed secret metadata:

- secret reference name
- provider
- scope
- present or missing status
- length
- non-reversible fingerprint prefix
- rotation status

Forbidden payloads:

- API keys
- bearer tokens
- passwords
- private keys
- refresh tokens
- session cookies
- connection strings containing credentials

## Embedding Policy

The gateway uses provider mode `auto`.

- Preferred provider: `openai_text_embedding_3_small`
- Preferred model: `text-embedding-3-small`
- Dimensions: `1536`
- Required secret: `OPENAI_API_KEY` from the process/User environment
- Offline fallback: `local_hash_v1`

`local_hash_v1` exists only so ingestion still works when `OPENAI_API_KEY` is unavailable. It is deterministic and dependency-light, but it is not the semantic-quality provider for normal memory work.

Agents must not choose their own embedding model or dimensions. The governed gateway owns embedding generation so model changes do not break the database schema or cross-agent retrieval.

## Autonomy Ingest Instructions

`D:\Autonomy` should ingest investigation data through the trusted ingest runner until the final governed service is fully rolled out.

Minimum information for an Autonomy ingest run:

- source path to ingest
- `source_kind`
- `run_id`
- `agent_id`
- `associated_project_path`

Example:

```powershell
D:\Codex_Managed\.venv\Scripts\python.exe D:\Autonomy\scripts\ingest_agent_core_memory.py `
  --source D:\Autonomy\reports `
  --source-kind drift_report `
  --agent-id autonomy-investigator `
  --run-id autonomy-ide-config-ingest `
  --project-path D:\Autonomy
```
