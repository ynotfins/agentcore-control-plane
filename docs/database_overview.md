# AgentCore Database Overview

Generated: 2026-06-24

> **Bifrost override (2026-07-14):** Normal non-Swarm IDE agents do not connect
> directly to PostgreSQL and no longer use `global-memory-gateway` as an IDE
> baseline. The current live path is `agentcore-gateway` → `agentcore-memory`;
> this document remains database/runtime background for `agent_core`.

## Runtime

- Engine: PostgreSQL 16.6
- Extension: pgvector 0.8.2
- Host: `127.0.0.1`
- Port: `55432`
- Database: `agent_core`
- Engine directory: `F:\AgentCore\postgres_runtime_engine\pgsql`
- Data directory: `F:\AgentCore\database_cluster`
- WAL archive root: `E:\AgentCoreArchive\backups_cold\pgvector\wal`
- Base backup root: `E:\AgentCoreArchive\backups_cold\pgvector\base`
- Startup owner: Task Scheduler task `\AgentCore\PostgresRuntime`
- Startup command: `D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped`

## Security Posture

- `listen_addresses = 'localhost'`
- `ssl = on`
- `ssl_min_protocol_version = 'TLSv1.2'`
- `password_encryption = 'scram-sha-256'`
- `pg_hba.conf` allows only localhost SSL connections for approved roles.
- Non-SSL localhost connections are rejected.
- All non-local IP ranges are rejected.
- Raw secrets must not be stored in vector memory or documentation.

## Roles

| Role | Purpose | Direct SQL | Privileges |
| --- | --- | --- | --- |
| `agent_admin` | migrations, schema maintenance, backup/restore validation | yes | superuser |
| `agent_ingest` | gateway and approved ingest writes | yes, constrained by grants | `SELECT` and `INSERT` on approved memory tables |
| `agent_read` | read-only inspection and validation | yes, read-only | `SELECT` only |
| `postgres` | break-glass local maintenance | yes | superuser |

Normal IDE agents must not connect directly to PostgreSQL. They must use `agentcore-gateway` → `agentcore-memory`; any future memory catalog/router work is gated by `database-plan.md`.

Generated role passwords are stored as Windows User-scope environment variables:

- `AGENT_CORE_AGENT_ADMIN_PASSWORD`
- `AGENT_CORE_AGENT_INGEST_PASSWORD`
- `AGENT_CORE_AGENT_READ_PASSWORD`
- `AGENT_CORE_POSTGRES_PASSWORD`
- `AGENT_CORE_PGPASSWORD` only as an environment-variable alias when a process expects `PGPASSWORD`

## Environment Variable Policy

AgentCore does not use `.env` files. All secrets and runtime credentials are stored in Windows Environment Variables. Documentation may list variable names only, never values.

## Schema

```mermaid
erDiagram
    projects ||--o{ project_facts : has
    projects ||--o{ messages : owns
    projects ||--o{ embeddings : groups
    messages ||--o{ embeddings : embeds

    projects {
        uuid id PK
        text project_key UK
        text display_name
        text root_path
        jsonb metadata
        timestamptz created_at
        timestamptz updated_at
    }

    project_facts {
        uuid id PK
        uuid project_id FK
        text fact_key
        jsonb fact_value
        int version
        uuid supersedes_fact_id FK
        text source
        text created_by
        bool is_current
    }

    messages {
        uuid id PK
        uuid project_id FK
        text agent_id
        text run_id
        text role
        text content
        jsonb metadata
        timestamptz created_at
    }

    embeddings {
        uuid id PK
        uuid message_id FK
        uuid project_id FK
        vector embedding
        text provider
        jsonb metadata
        timestamptz created_at
    }
```

Existing operational tables:

- `global_vector_memory_store`: canonical current vector memory table used by `global-memory-gateway`.
- `agent_cross_project_telemetry`: gateway, ingest, and validation telemetry.

New robust schema tables:

- `system_info`: keyed local system facts.
- `projects`: project identity and roots.
- `project_facts`: versioned immutable project facts and drift records.
- `messages`: episodic events and summaries.
- `embeddings`: normalized embedding records linked to projects/messages.

## Write-Class Policy

```mermaid
flowchart TD
    normalAgent[Normal IDE Agent] --> gateway[global-memory-gateway]
    gateway --> ingestRole[agent_ingest]
    ingestRole --> postgres[(agent_core)]

    trustedIngest[Trusted Ingest Runner] --> ingestRole
    adminAgent[Admin Migration Agent] --> adminRole[agent_admin]
    adminRole --> postgres
    readAgent[Read Agent] --> readRole[agent_read]
    readRole --> postgres
```

Normal agents use the MCP gateway. Trusted ingest and admin jobs are the only approved direct SQL writers.

## Backup And Restore

Backup script:

```powershell
D:\github\agentcore-control-plane\ops\Backup-AgentCorePostgres.ps1
```

Restore validation script:

```powershell
D:\github\agentcore-control-plane\ops\Test-AgentCorePostgresRestore.ps1
```

Daily backup schedule:

- Task: `AgentCore\NightlyBackup`
- Time: `03:00`
- Target: `E:\AgentCoreArchive\backups_cold\pgvector\base`
- Codex mirror: `agentcore-nightly-backup`

Daily restore verification:

- Task: `AgentCore\NightlyRestoreTest`
- Time: `03:30`
- Behavior: restores latest dump into `agent_core_restore_test`, validates `global_vector_memory_store`, then drops the disposable database.
- Codex mirror: `agentcore-nightly-restore-test`

WAL archiving:

- `archive_mode = on`
- archive command: `D:\github\agentcore-control-plane\ops\Archive-AgentCoreWal.ps1`
- target: `E:\AgentCoreArchive\backups_cold\pgvector\wal`

Projection schedule:

- Task: `AgentCore\MemoryProjection`
- Cadence: every 2 hours
- Behavior: reads canonical memory rows from `agent_core`, projects the governed set into local SwarmRecall, and materializes only the curated governed knowledge subset into SwarmVault
- Codex mirror: `agentcore-memory-projection-monitor` validates projection health and can invoke the projector when safe

Startup ownership:

- Task: `AgentCore\PostgresRuntime`
- Trigger: current-user logon
- Behavior: starts native PostgreSQL from `F:\AgentCore\postgres_runtime_engine\pgsql` when `F:\AgentCore\database_cluster` is not already running.
- This task is required before SwarmRecall can validate as healthy after reboot, because SwarmRecall uses the same native PostgreSQL engine for its local `swarmrecall` database.

Projection rebuild:

- Script: `D:\github\agentcore-control-plane\ops\Rebuild-AgentCoreSwarmVaultProjection.ps1`
- Use when the SwarmVault corpus contains stale AgentCore projection artifacts or when the curation policy changes.
- The rebuild path backs up the current projection-derived vault files under `E:\AgentCoreArchive\backups_cold\swarmvault-projection-rebuild\`, resets only the SwarmVault projection state, and replays the current curated projection from canonical memory.

Operational ownership note:

- If the legacy Windows tasks still reference `D:\MCP-Control-Plane\ops\...`, those entrypoints delegate into the source-controlled `D:\github\agentcore-control-plane\ops\...` scripts.
- Codex cron automations mirror drift sync, backup, restore-test, and maintenance jobs, so the database operational model remains covered even before elevated Windows task re-registration is completed.

## Validation Commands

```powershell
D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped
D:\github\agentcore-control-plane\ops\Backup-AgentCorePostgres.ps1
D:\github\agentcore-control-plane\ops\Test-AgentCorePostgresRestore.ps1
```
