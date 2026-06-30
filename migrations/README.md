# AgentCore Unified Memory Catalog — Migrations

**Status:** PRE-MIGRATION. These files do NOT authorize live DB mutation.
**Design authority:** `../database-plan.md` (schema_version 2026-06-30, §6 DDL, §13 strategy).
**Target DB:** PostgreSQL `agent_core` on `127.0.0.1:55432` (NOT `swarmrecall`, NOT `:65432`).

## Hard rules
- Additive only. Existing tables (`global_vector_memory_store`, `agent_cross_project_telemetry`, `system_info`, `projects`, `project_facts`, `messages`, `embeddings`) are NEVER altered by these migrations.
- No `.env` files. Credentials are Windows environment variables only.
- Normal agents never run these. Only the `admin_migration` write class (role `agent_admin`) applies DDL, and only after explicit operator sign-off.

## Files (dependency order)
1. `0001_up_memory_source_systems.sql` / `0001_down_memory_source_systems.sql`
2. `0002_up_memory_catalog.sql` / `0002_down_memory_catalog.sql`
3. `0003_up_retrieval_events_context_packs.sql` / `0003_down_retrieval_events_context_packs.sql`
4. `0004_up_agent_run_ledger_quality_scores.sql` / `0004_down_agent_run_ledger_quality_scores.sql`
5. `0005_seed_source_systems.sql`

Apply order: `0001 -> 0002 -> 0003 -> 0004 -> 0005`. Each `down` reverses its `up`.

## Pre-migration gates (database-plan.md §13.1 — ALL must pass before any apply)
1. `ops/Backup-AgentCorePostgres.ps1` — successful base backup (within 24h, §18.13).
2. `ops/Test-AgentCorePostgresRestore.ps1` — restore verify into `agent_core_restore_test`.
3. `ops/Test-AgentCoreSwarmRecall.ps1` — service health.
4. `ops/Test-AgentCoreMemoryProjection.ps1` — dirty-state / no active projector.

## Dry-run protocol (database-plan.md §13.2 — REQUIRED before execute; no commit)
Run each `up` block inside a transaction that ends in explicit `ROLLBACK` (verifies syntax/constraints/HNSW index messages, zero errors). Example (operator, role `agent_admin`):

```
BEGIN;
\i 0001_up_memory_source_systems.sql
\i 0002_up_memory_catalog.sql
\i 0003_up_retrieval_events_context_packs.sql
\i 0004_up_agent_run_ledger_quality_scores.sql
\i 0005_seed_source_systems.sql
-- verify: \dt memory_*  \dt context_*  \dt agent_*
ROLLBACK;   -- dry-run only; never COMMIT without operator sign-off
```

Live apply (transaction + `COMMIT`) requires: all gates green, dry-run clean, and recorded human operator sign-off (§18.20). The `down` blocks must be tested in `agent_core_restore_test` before the `up` blocks are applied to production.
