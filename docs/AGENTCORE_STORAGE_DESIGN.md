# AgentCore Storage Design

> **HISTORICAL / SUPERSEDED (2026-06-24).** Pre-Bifrost / pre-PG18 storage layout notes. Implementation authority is `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` and locked drive roles in `BLUEPRINT.md`. Excluded from default ChatGPT Project Sources.

Generated: 2026-06-24

## Active Drive

`F:` is the active agent/database NVMe drive.

- Label: `Agent_Vector_4TB`
- Device: Samsung SSD 990 PRO with Heatsink 4TB
- Filesystem: NTFS
- Allocation unit: 64 KB
- Root: `F:\AgentCore`

Active layout:

```text
F:\AgentCore\
  postgres_runtime_engine\
  database_cluster\
  agents_workspace\
    Cursor\
    Autonomy\
    Codex\
    OpenClaw\
    MiniMax\
    AndroidStudio\
  ingestion_staging\
  backups_hot\
```

## Archive Drive

`E:` is the cold archive/data-lake drive.

- Label: `Agent_Core_6TB`
- Filesystem: NTFS
- Root: `E:\AgentCoreArchive`

Archive layout:

```text
E:\AgentCoreArchive\
  backups_cold\
  database_snapshots\
  raw_exports\
```

## Database

Current canonical PostgreSQL runtime (supersedes the June layout below):

- Engine root: `F:\PostgreSQL18`
- Data cluster: `F:\PostgreSQL18\data`
- Host: `127.0.0.1`
- Port: `55433`
- Database: `agent_core`
- Vector/search authority: versioned AgentCore migrations in PostgreSQL 18; do not depend on the removed PG16-era `global_vector_memory_store` name.
- pgvector: installed in PostgreSQL 18; verify the live extension version at execution time rather than treating this historical document as version authority.

Legacy rollback copy:

- PostgreSQL 16 at `127.0.0.1:55432` / `F:\AgentCore\database_cluster` is rollback evidence only.

Do not use the legacy copy as active storage unless explicitly rolling back.

## Performance Baseline

Samsung 990 Pro internal `F:`:

```text
Random 16 Read:      3301.29 MB/s
Sequential 64 Read:  6159.93 MB/s
Sequential 64 Write: 7017.93 MB/s
95th percentile:     0.088 ms
Max latency:         0.192 ms
```

Old external 128 GB bridge baseline:

```text
Random 16 Read:      280.61 MB/s
Sequential 64 Read:  389.43 MB/s
Sequential 64 Write: 385.50 MB/s
95th percentile:     0.403 ms
Max latency:         3.680 ms
```

## Policy

- Active agents and pgvector writes use `F:\AgentCore`.
- Cold backups, snapshots, exports, and raw large artifacts use `E:\AgentCoreArchive`.
- Normal agents use `agentcore-gateway` → `agentcore-memory`, not direct SQL.
- Trusted ingest/admin runners may use direct SQL only with explicit control-plane approval recorded in `D:\github\agentcore-control-plane` (never approved by `D:\MCP-Control-Plane`, which is evidence only).
- The Bifrost gateway runtime lives at `F:\AgentCore\runtime\bifrost`; AgentCore scratch/staging lives at `F:\AgentCore\staging`. `I:\LocalApps` is neutral application hot data, and `J:` is portable media (see `PROJECT_ANCHOR.md` §2).
- The 128 GB NVMe is not part of the active design. Keep it as spare/scratch unless a future control-plane decision assigns it a specific role.
