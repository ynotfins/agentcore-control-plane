# AgentCore M8 Performance Baseline

**Authority:** BLUEPRINT.md M8  
**Hardware:** CHAOSCENTRAL — Intel Core i9-14900KF, 128 GB DDR5, RTX 4070 SUPER 12 GB  
**Storage:** F: Samsung 990 PRO NVMe (7 GB/s read), H: Crucial P5+ NVMe (3.5 GB/s read)  
**OS:** Windows 11 Pro (build 26200+)  
**PostgreSQL:** 18 on F:, endpoint 127.0.0.1:55433  
**Date:** 2026-07-16

---

## Measurement Method Key

| Method | Description |
|--------|-------------|
| `pg_local_write` | `EXPLAIN ANALYZE` on local PostgreSQL 18 with F: NVMe |
| `pg_fts` | Full-text search via `tsvector` index on F: |
| `pg_fts_vector` | Combined FTS + vector similarity (pg_vector or pgvector) |
| `http_local` | HTTP round-trip to 127.0.0.1 (Bifrost or memory service) |
| `disk_local` | Local filesystem read/write on H: or E: |
| `process_timing` | `time` or Python `time.perf_counter()` around the operation |
| `estimated` | Hardware-based estimate; measure in production during M9 if applicable |

---

## Memory Service Operations

### `append_event`

Writes a single memory event row to `agentcore.memory_events`.

| Metric | Target | Acceptable (p99) | Method |
|--------|--------|-----------------|--------|
| Latency p50 | < 5 ms | < 20 ms | `pg_local_write` |
| Throughput | > 5000 writes/min at p50 | — | `process_timing` batch |

**Baseline rationale:** F: Samsung 990 PRO delivers ~1M IOPS. Single-row INSERT to an indexed
table on local NVMe should complete well under 5 ms including psycopg roundtrip overhead.

---

### `startup_context`

Assembles bounded startup context from memory_events + summaries + facts.

| Metric | Target | Acceptable (p99) | Method |
|--------|--------|-----------------|--------|
| Latency p50 | < 200 ms | < 500 ms | `pg_fts` + `process_timing` |
| Context size | ≤ 8000 tokens assembled | — | estimated |

**Baseline rationale:** Bounded query across 3 tables with FTS index on F:. 200 ms budget
covers 2–3 indexed queries plus Python serialization on i9-14900KF.

---

### `retrieve_context`

Full-text + optional vector similarity search across memory_events and summaries.

| Metric | Target | Acceptable (p99) | Method |
|--------|--------|-----------------|--------|
| Latency p50 | < 50 ms | < 200 ms | `pg_fts_vector` |
| Result set | top-K (K ≤ 20) | — | estimated |

**Baseline rationale:** FTS on F: with HNSW index. Single query, well-indexed.

---

### `docs_search`

Full-text search across knowledge index (arabold-docs indexed content).

| Metric | Target | Acceptable (p99) | Method |
|--------|--------|-----------------|--------|
| Latency p50 | < 100 ms | < 300 ms | `pg_fts` |
| Index size | ≤ 5 GB in PostgreSQL | — | estimated |

**Baseline rationale:** Dedicated tsvector index on docs table on F:.

---

### `expand_source`

Fetches an artifact from H: runtime or E: cold archive.

| Metric | Target | Acceptable (p99) | Method |
|--------|--------|-----------------|--------|
| Latency p50 (H:) | < 10 ms | < 50 ms | `disk_local` (H: NVMe) |
| Latency p50 (E:) | < 50 ms | < 200 ms | `disk_local` (E: spinning) |

**Baseline rationale:** H: Crucial P5+ NVMe gives ~3.5 GB/s. Small artifact reads should
be < 10 ms. E: archive may be spinning or slow SSD — 50 ms p50 is conservative.

---

## Workflow and Compaction Operations

### `compaction_throughput`

Events processed per minute during memory compaction pipeline.

| Metric | Target | Acceptable | Method |
|--------|--------|-----------|--------|
| Events/minute | > 1000 | > 500 | `process_timing` over a batch run |

---

### `projection_generation`

Generate a STATE.md or similar projection for a single project.

| Metric | Target | Acceptable (p99) | Method |
|--------|--------|-----------------|--------|
| Latency | < 2 s | < 10 s | `process_timing` |

---

## PostgreSQL Operations

### `pg_checkpoint_save`

PostgreSQL checkpoint write (shared_buffers flush to F: NVMe).

| Metric | Target | Acceptable (p99) | Method |
|--------|--------|-----------------|--------|
| Latency p50 | < 10 ms | < 50 ms | `pg_local_write` + `EXPLAIN ANALYZE` |

---

### `backup_logical`

Full logical backup via `pg_dump` of `agent_core`.

| Metric | Target | Acceptable | Method |
|--------|--------|-----------|--------|
| Duration | < 5 minutes | < 15 minutes | `process_timing` |
| Typical DB size | ≤ 10 GB logical | — | estimated |

**Script:** `ops/Backup-AgentCorePostgres.ps1`

---

### `restore_test`

Restore from most recent backup and verify integrity.

| Metric | Target | Acceptable | Method |
|--------|--------|-----------|--------|
| Duration | < 10 minutes | < 30 minutes | `process_timing` |

**Script:** `ops/Test-AgentCorePostgresRestore.ps1`

---

### `pitr_recovery`

Point-In-Time Recovery to a specific target timestamp using WAL archive.

| Metric | Target | Acceptable | Method |
|--------|--------|-----------|--------|
| Duration to recovery point | < 15 minutes | < 45 minutes | `process_timing` |

**Script:** `ops/Test-AgentCorePg18Pitr.ps1`

---

## Resource Limits

These are hard limits enforced by configuration or policy. PostgreSQL settings are
authoritative in `F:\PostgreSQL18\data\postgresql.conf`.

| Component | Limit | Setting |
|-----------|-------|---------|
| PostgreSQL max_connections | 100 | `max_connections = 100` in postgresql.conf |
| PostgreSQL shared_buffers | 8 GB | `shared_buffers = 8GB` |
| PostgreSQL effective_cache_size | 32 GB | `effective_cache_size = 32GB` |
| PostgreSQL work_mem | 64 MB | `work_mem = 64MB` |
| Bifrost max concurrent MCP connections | 50 | Bifrost gateway config |
| Memory service max RSS | 4 GB | Operator monitoring target |
| Worker (LangGraph node) max RSS | 2 GB | Operator monitoring target |
| DA builder sessions | 1 per project at a time | `deepagents_worker.py` design |
| GPU (RTX 4070 SUPER 12 GB) | Reserved for model inference | Not used by PostgreSQL or Bifrost |

---

## Notes

1. All latency targets assume a warm PostgreSQL buffer cache (F: NVMe backed).
   Cold-cache p99 values may be 2–5× higher on first access after restart.
2. These targets are **baselines** established from hardware specs and architecture.
   They should be measured empirically during normal operation and updated if the
   hardware or data volume changes materially.
3. GPU is explicitly excluded from database and Bifrost workloads to preserve
   model inference headroom.
4. E: archive read latency depends on whether E: is a spinning disk or SSD.
   The 200 ms p99 target assumes spinning disk worst case.
