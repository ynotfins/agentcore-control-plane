# M1 Exit Evidence — Storage and PostgreSQL 18 Safety Foundation

**Status:** PASSED  
**Completed on:** 2026-07-14 / 2026-07-15  
**Completion commit:** `6ed18fa`  
**Branch:** `task/authority-reconciliation`  
**Blueprint authority:** `BLUEPRINT.md` §8, M1

## Exit Criteria

| BLUEPRINT.md M1 exit criterion | Result | Evidence |
| -- | -- | -- |
| E:, F:, H:, and I: allocation units verified | PASS | `audits/M1/allocation-units-verified.txt` |
| Any mismatched target is safely corrected with backup, hash verification, restore, and service validation | PASS | I: was the only mismatch; `audits/M1/I-format-manifest.json` records identity, emptiness, format, and post-format 64KB verification |
| Existing PostgreSQL cluster and roles inventoried | PASS | `audits/M1/pg16-inventory.txt` |
| Logical and physical backups created | PASS | `audits/M1/pg16-backup-manifest.json` |
| At least one isolated restore test passes | PASS | `audits/M1/pg16-restore-test.txt` |
| PostgreSQL 18 and compatible pgvector run on F: | PASS | `audits/M1/pg18-service-config.txt` |
| Required databases and least-privilege service roles exist | PASS | `audits/M1/pg18-service-config.txt` |
| Old PostgreSQL cluster remains preserved and recoverable | PASS | `audits/M1/rollback-proof.txt` |
| Rollback is proven | PASS | `audits/M1/rollback-proof.txt` |
| No durable database, WAL, checkpoint, queue, or lock workload is placed on I: or E: | PASS | `audits/M1/rollback-proof.txt`; I: cleaned after restore test; E:/G: contain backup copies only |

## Key Values

- I: physical identity verified before format: Disk #0, `CT1000BX500SSD1`, serial `2306E6AAD10C`, volume GUID `{ac27f734-60e4-4783-a6ec-6e9f922ad9d1}`.
- I: allocation corrected from 512 bytes to 65,536 bytes (64KB), filesystem NTFS, label `AgentCore_Staging`.
- PG16 preserved at `F:\AgentCore\database_cluster`, PostgreSQL 16.6, port 55432.
- Logical backup: `E:\AgentCoreArchive\backups_cold\pgvector\base\agent_core-20260714-232021.dump`, 731,279 bytes, SHA-256 `41EB3818F2BEFC7CE82FF02E50C92607085841900E9C6FB66D2284FD80018419`.
- Physical backup: `E:\AgentCoreArchive\pg16-base-backup-20260714-232106`, 12.8 MB, base tar SHA-256 `BD17F1FA4FC81A498AA94F8D8EB28E5B3DF7E926114B479A533D6435BC1F64EC`.
- Second backup copies were verified on G: with matching SHA-256 hashes.
- Restore test passed: restored `agent_core` into an isolated disposable cluster on I: and verified row counts match live PG16 (`projects=1`, `project_facts=215`, `global_vector_memory_store=105`, `agent_cross_project_telemetry=90`).
- PG18 installed side-by-side at `F:\PostgreSQL18`, data directory `F:\PostgreSQL18\data`, port 55433, service `AgentCore-PostgreSQL18`.
- PG18 is localhost-only (`127.0.0.1:55433`) with SSL enabled.
- pgvector 0.8.5 built from source and installed on PG18; `agent_core` has `vector 0.8.5`, `pgcrypto 1.4`, `plpgsql 1.0`.
- PG18 databases created: `agent_core`, `cognee_core`.
- PG18 roles created: `agentcore_read`, `agentcore_ingest`, `agentcore_worker`, `agentcore_admin`, `agentcore_backup`, `agentcore_cognee`.

## M2 Entry Implications

- M2 may use PG18 on port 55433 and must not alter the preserved PG16 cluster.
- M2 schema migrations must be versioned and reversible.
- M2 authorization boundaries must use SQL authorization (`GRANT`/`REVOKE`, RLS, policies, SECURITY DEFINER functions), not `pg_hba.conf`. `pg_hba.conf` controls authentication only.
- M2 must prove queue, claim, lease, and dead-letter restart recovery across a controlled PG18 restart.
