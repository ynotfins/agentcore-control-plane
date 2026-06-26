# Agent Database Bootstrap Contract

`D:\github\agentcore-control-plane` is the canonical Git source repo for MCP server governance, persistent cross-project memory contracts, and the local PostgreSQL vector database.

`D:\MCP-Control-Plane` remains the current live deployed ops root used by scheduled tasks, WAL archiving hooks, and inherited operational paths until a deliberate migration is approved.

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

Default write roots:

- `F:\AgentCore`
- `E:\AgentCoreArchive`

Agents must not write to `C:`, `D:`, `G:`, `H:`, or `I:` unless explicitly instructed by the user for the current task.

If an approved drive cannot be written to, agents must stop immediately and notify the user. They must not silently fall back to another drive.

## Write Classes

### Normal Agent

Normal IDE agents must use the governed memory tool contract:

- `memory_append`
- `memory_search`
- `memory_state`

Normal agents do not need to know SQL or generate database connection code. The governed runtime is responsible for validation, metadata, embedding, database writes, and telemetry.

### Trusted Ingest

Trusted ingest jobs may write directly to PostgreSQL only when they are explicitly approved by this control plane.

Current approved temporary ingest runner:

- `D:\Autonomy\scripts\ingest_agent_core_memory.py`

Trusted ingest is for loading structured system evidence such as IDE inventories, MCP configs, drift reports, probe results, runbooks, and topology snapshots.

## Source And Live Root Split

- Canonical Git source repo: `D:\github\agentcore-control-plane`
- Current live deployed ops root: `D:\MCP-Control-Plane`
- Live migration from `D:\MCP-Control-Plane` to the Git repo path is a separate controlled rollout and is not implied by source-repo edits alone.

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
