# AgentCore Storage Design

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

Active PostgreSQL runtime:

- Engine: `F:\AgentCore\postgres_runtime_engine\pgsql`
- Data cluster: `F:\AgentCore\database_cluster`
- Host: `127.0.0.1`
- Port: `55432`
- Database: `agent_core`
- Vector table: `global_vector_memory_store`
- Telemetry table: `agent_cross_project_telemetry`
- pgvector: `0.8.2`

Legacy rollback copy:

- `E:\database_cluster`

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
- Normal agents use `global-memory-gateway`, not direct SQL.
- Trusted ingest/admin runners may use direct SQL only when approved by `D:\MCP-Control-Plane`.
- The 128 GB NVMe is not part of the active design. Keep it as spare/scratch unless a future control-plane decision assigns it a specific role.
