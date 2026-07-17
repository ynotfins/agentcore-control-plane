# M5 Exit Evidence — Hybrid Retrieval and Curated Cognee Memory

**Status:** PASSED  
**Completed on:** 2026-07-16 UTC  
**Gateway:** `agentcore-gateway` at `http://127.0.0.1:8080/mcp`  
**Upstream identity:** `agentcore-memory` (unchanged)  
**Server implementation:** `scripts/agentcore_memory/server.py` version `0.5.0`  
**Acceptance summary:** `audits/M5/m5-acceptance-summary.json` (run `20260716003954`)  
**Migration applied:** `migrations/m5/001_up_hybrid_retrieval_cognee.sql`  
**Rollback migration:** `migrations/m5/001_down_hybrid_retrieval_cognee.sql`

## Cognee

| Fact | Value |
| --- | --- |
| Package/version | `cognee 1.3.0` |
| Installation path | `H:\AgentRuntime\agentcore-memory\cognee\.venv311\Lib\site-packages\cognee\__init__.py` |
| Runtime root | `H:\AgentRuntime\agentcore-memory\cognee\` |
| Database | `cognee_core` on existing PostgreSQL 18 (`127.0.0.1:55433`) |
| Configuration | Windows process/User environment variables only; no `.env` file |
| Adapter path | `scripts/agentcore_memory/knowledge_memory.py` (`KnowledgeMemoryPort`) |

Cognee API/package details were checked through Arabold URL fetches for the official Cognee
installation and relational database docs. The installed package exposes `run_migrations`; that
was used against `cognee_core` after the docs-described top-level `run_startup_migrations` name
was not exported by Cognee 1.3.0.

## Retrieval Strategy

- PostgreSQL remains canonical.
- `docs_search` and `retrieve_context` retain their MCP names and add optional query/filter/vector arguments.
- Hybrid retrieval combines PostgreSQL metadata/trust/project filters, full-text search, `pg_trgm`, exact pgvector, and curated Cognee promotion rows.
- Official documents/source excerpts live on `E:\AgentCoreArchive\agentcore-memory\official-docs\`.
- Search metadata, full-text/trigram indexes, embeddings, and retrieval rows live in PostgreSQL 18 on F:.
- The M5 fixture corpus did not justify HNSW; exact pgvector remains the correctness baseline. IVFFlat, pgvectorscale, and DiskANN remain deferred.

## Acceptance Results

| # | Check | Result |
| ---: | --- | --- |
| 1 | Versioned reversible M5 migration | PASS |
| 2 | Live M5 migration applied | PASS |
| 3 | Exact MCP surface preserved | PASS |
| 4 | Bounded retrieval fixtures seeded | PASS |
| 5 | Full-text retrieval returns expected fixture | PASS |
| 6 | `pg_trgm` retrieves controlled misspelling/partial identifier | PASS |
| 7 | Exact pgvector search produces correctness baseline | PASS |
| 8 | HNSW benchmark gate recorded | PASS (`decision=deferred`, `hnsw_index_present=false`) |
| 9 | Retrieval respects project and trust boundaries | PASS |
| 10 | Raw transcripts rejected by promotion gate | PASS |
| 11 | Quarantined evidence rejected by promotion gate | PASS |
| 12 | Validated fact promoted with complete provenance | PASS |
| 13 | Cognee retrieval returns promoted fact and source references | PASS |
| 14 | E: official document found through F: index | PASS |
| 15 | Cognee outage degrades to PostgreSQL-only retrieval | PASS |
| 16 | No Mem0 package, process, database, or config introduced | PASS |
| 17 | Bifrost restart and safe Cursor call succeed | PASS |

## Benchmark Result

M5 recorded `m5.hnsw.decision` with:

- `corpus_rows=16`
- `decision=deferred`
- `hnsw_index_present=false`

The bounded M5 corpus does not justify ANN operational cost. Exact pgvector was used as the
correctness baseline; HNSW remains the first ANN strategy only when measured corpus/query evidence
justifies it.

## Degraded Mode

The acceptance harness used `H:\AgentRuntime\agentcore-memory\cognee\COGNEE_DISABLED.flag` to
simulate Cognee outage. During that outage:

- `memory_status` reported Cognee degradation.
- `docs_search` returned PostgreSQL-only results.
- exact expansion continued.
- STATE/projection rows remained queryable (`projections=28` in final M5 acceptance).
- Bifrost and `agentcore-memory` identities remained unchanged.

## Regression Evidence

- M2 regression: `scripts/memory_platform/Test-M2CanonicalIdentity.ps1` PASS.
- M3 regression: `scripts/memory_platform/Test-M3LosslessContext.ps1` PASS.
- M4 regression: `scripts/memory_platform/Test-M4Gateway.ps1` PASS (updated to accept post-M5 Cognee availability and reapply its own M4 migration after M3).
- Contract validators: `scripts/bifrost/validate_contracts.py` PASS; `scripts/bifrost/test_contracts.py` PASS (107 checks).

## Rollback Procedure

1. Disable Cognee by creating `H:\AgentRuntime\agentcore-memory\cognee\COGNEE_DISABLED.flag`.
2. Apply `migrations/m5/001_down_hybrid_retrieval_cognee.sql` to `agent_core`.
3. Restore `scripts/agentcore_memory/server.py` and `contracts/bifrost-upstream-mcp-registry.json` from the pre-M5 commit if full rollback is required.
4. Run `python scripts\bifrost\render_bifrost_config.py`.
5. Restart Bifrost via `ops\bifrost\Stop-AgentCoreBifrostGateway.ps1` and `ops\bifrost\Start-AgentCoreBifrostGateway.ps1`.
6. IDE configs remain unchanged throughout rollback.

## CHAOSCENTRAL Documentation

Synchronized:

- `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`
- `D:\ChaosCentral-Current-Build\docs\software\PC_INSTALLED_SOFTWARE.md`
- `D:\ChaosCentral-Current-Build\CURRENT_STATE.md`
- `D:\ChaosCentral-Current-Build\AGENTCORE_MEMORY_OPERATING_MANUAL.md`
- New runtime snapshot: `D:\ChaosCentral-Current-Build\docs\runtime\PC_RUNTIME_SNAPSHOT_20260716-003753.md`
- New machine-readable runtime evidence: `D:\ChaosCentral-Current-Build\evidence\runtime\PC_RUNTIME_SNAPSHOT_20260716-003753.json`

Validation: `D:\ChaosCentral-Current-Build\scripts\Test-PCDocumentation.ps1` PASS (`30/30`).

## Out of Scope Confirmed

- No Mem0 install.
- No new vector database.
- No IVFFlat, pgvectorscale, or DiskANN.
- No LangGraph M6 checkpoint/workflow implementation.
- No runtime JIT tool leases.
- No IDE MCP config edits.
- No Swarm dependency added to the non-Swarm AgentCore baseline.

## M0-M5 Hardening Delta — 2026-07-16

Follow-up hardening evidence:

- `audits/M5/M0-M5-HARDENING-EVIDENCE.md`
- `audits/M5/FEATURE-RECONCILIATION-MATRIX.md`
- `docs/memory-platform/BACKUP_RESTORE_WAL_PITR.md`

Additional results:

- PG18 logical/base/source/config backup created on E: and mirrored to G: with SHA-256 verification.
- Isolated logical restore of `agent_core` and `cognee_core` passed.
- WAL archiving enabled for PG18 with active WAL on F:, archive on E:, DR copy on G:.
- PITR marker recovery passed in an isolated restore cluster.
- Residual PG16 references were classified; current non-Swarm AgentCore drift was corrected where this shell had permission.
- Elevated closeout repaired Windows service ownership and live maintenance task retargeting:
  - `AgentCore-PostgreSQL18` owns PG18 again and starts automatically.
  - `NightlyBackup`, `NightlyRestoreTest`, and `WeeklyMaintenance` now call source-controlled PG18 scripts under `D:\github\agentcore-control-plane\ops`.
  - Manual Task Scheduler runs for all three returned `0`.
  - Elevated M2/M3/M4/M5 regressions passed.
  - Final scheduled-task backup/restore and PITR passed against backup `20260716-015835`.
  - Swarm-owned PG16 configuration was not changed.
