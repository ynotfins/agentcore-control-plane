# M0-M5 Platform Hardening Evidence

**Status:** hardening pass and elevated closeout completed
**Authority:** `BLUEPRINT.md` locked architecture; `plan-notes.txt`/original notes treated as non-authoritative research  
**Run window:** 2026-07-16 00:52-01:59 EDT
**Repository branch:** `task/authority-reconciliation`

## PG18 Canonical State

- Canonical AgentCore PostgreSQL: `127.0.0.1:55433`, `F:\PostgreSQL18\data`.
- Databases verified: `agent_core`, `cognee_core`.
- Extensions verified in `agent_core`: `pg_trgm=1.6`, `pgcrypto=1.4`, `plpgsql=1.0`, `vector=0.8.5`.
- Roles verified: `agentcore_read`, `agentcore_ingest`, `agentcore_worker`, `agentcore_admin`, `agentcore_backup`, `agentcore_cognee`.
- Windows User env drift corrected: `AGENT_CORE_PGPORT=55433`.
- PostgreSQL 16 at `127.0.0.1:55432` remains rollback/legacy evidence and Swarm-owned where applicable.

## Residual PG16 Classification

| Surface | Classification | Action |
| --- | --- | --- |
| `PROJECT_ANCHOR.md` endpoint lines | Immutable constitution residue; not edited without explicit approval | Documented as superseded by BLUEPRINT/current M1-M5 evidence for this task |
| `CLAUDE.md` PG16 current-runtime note | Current AgentCore drift | Corrected to PG18 canonical + PG16 rollback/Swarm-only |
| `ops/Backup-AgentCorePostgres.ps1`, `ops/Test-AgentCorePostgresRestore.ps1`, `ops/Invoke-AgentCoreMaintenance.ps1`, `ops/Start-AgentCorePostgres.ps1` | Current AgentCore drift | Corrected to PG18 defaults |
| `validators/validate-control-plane.ps1` listener check | Current AgentCore drift | Corrected to `55433`; validator relocked |
| `migrations/README.md` | Historical PG16 root migrations | Re-bannered as historical; current migrations are `m2`-`m5` |
| `ops/Invoke-AgentCoreMemoryProjector.ps1`, `ops/Test-AgentCoreMemoryProjection.ps1` | Swarm-owned projection tooling | Left unchanged |
| `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md`, `database-plan.md`, `AGENT_DATABASE_BOOTSTRAP.md`, old reports | Historical evidence | Left unchanged |
| Live `NightlyBackup`, `NightlyRestoreTest`, `WeeklyMaintenance` scheduled task actions | Current AgentCore drift to `D:\MCP-Control-Plane` | Repaired by elevated closeout; all three now call repo-owned PG18 scripts and returned result `0` in manual Task Scheduler runs |

## Backup Evidence

- Accepted primary backup: `E:\AgentCoreArchive\agentcore-memory\backups\pg18\20260716-015835`.
- Accepted second copy: `G:\AgentCoreArchive\agentcore-memory\backups\pg18\20260716-015835`.
- Manifest: `backup-manifest.json`.
- Hash manifest: `sha256-manifest.json`.
- G: mirror verification: 27 files checked; 0 mismatches.
- Backup contents:
  - `agent_core` custom logical dump.
  - `cognee_core` custom logical dump.
  - globals/roles dump with `--no-role-passwords`.
  - physical/base backup with streamed WAL.
  - source/config snapshot for memory service, Bifrost contracts/sanitized config, M2-M5 migrations, projection worker, and acceptance harnesses.

## Restore Evidence

Isolated logical restore test passed using `ops\Test-AgentCorePostgresRestore.ps1`.

- Restore root: `I:\AgentCoreRestoreTests\pg18\20260716-015840`.
- Restored databases: `agent_core`, `cognee_core`.
- Verified extensions: `pg_trgm=1.6`, `pgcrypto=1.4`, `plpgsql=1.0`, `vector=0.8.5`.
- Verified roles: all six AgentCore service roles.
- Verified row counts:
  - `agentcore.evidence_events`: 113
  - `agentcore.context_summaries`: 23
  - `agentcore.projection_revisions`: 40
  - `agentcore.retrieval_documents`: 103
  - `agentcore.knowledge_promotions`: null / table absent in current schema
- Verified Cognee tables: 29.

## WAL / PITR

WAL archiving was enabled now because PG18 already contains durable M2-M5 state and no architecture redesign was required.

- Active `pg_wal` remains under `F:\PostgreSQL18\data\pg_wal`.
- WAL archive root: `E:\AgentCoreArchive\agentcore-memory\wal\pg18`.
- Second archive copy root: `G:\AgentCoreArchive\agentcore-memory\wal\pg18`.
- Settings verified active:
  - `wal_level=replica`
  - `archive_mode=on`
  - `archive_timeout=300`
  - `max_wal_senders=5`
  - `archive_command` calls `ops\Archive-AgentCoreWal.ps1`
- Archive visibility verified with switched WAL file `00000001000000000000000E`.
- PITR test passed with `ops\Test-AgentCorePg18Pitr.ps1`.
  - Restore root: `I:\AgentCoreRestoreTests\pg18-pitr\20260716-015856`.
  - Recovered marker: `PITR_MARKER_20260716-015856`.
  - Marker count after recovery: 1.
  - Extension check included `vector=0.8.5`.
- PITR harness hardening: restore tests now set `archive_mode=off` and `recovery_target_timeline=current` so test clusters do not write timeline artifacts back into the production archive.
- Two test-generated timeline-2 archive files from an earlier failed harness run were quarantined to `E:\AgentCoreArchive\agentcore-memory\wal\pg18-test-artifacts\20260716-012021`; live PG18 remained on timeline 1.

## Runtime Reproducibility

- Source backup includes memory service implementation, `KnowledgeMemoryPort`, Bifrost registry/client contract, sanitized Bifrost config, M2-M5 migrations, and projection/test scripts.
- Context Fabric repair is now reproducible through `ops\Repair-AgentCoreContextFabricRuntime.ps1`; it patches the ignored runtime watcher max-buffer issue without vendoring `node_modules`.
- PG18 service ownership restored: Windows service `AgentCore-PostgreSQL18` is `Running`, `Automatic`, account `NT AUTHORITY\NetworkService`, path `"F:\PostgreSQL18\bin\pg_ctl.exe" runservice -N "AgentCore-PostgreSQL18" -D "F:\PostgreSQL18\data" -w`.
- Elevated closeout evidence: `audits/M5/elevated-closeout-20260716-015250.json`.

## Regression Gate

- Repository validators: PASS (`scripts/bifrost/validate_contracts.py`, `scripts/bifrost/test_contracts.py`, `validators/validate-control-plane.ps1 -DryRun`).
- Secret scan: PASS via `validate-control-plane.ps1` hard-coded secret checks.
- M2 acceptance suite: PASS (`audits/M5/elevated-closeout-20260716-015250/m2.log`).
- M3 acceptance suite: PASS (`audits/M5/elevated-closeout-20260716-015250/m3.log`).
- M4 acceptance suite: PASS (19 checks, `audits/M5/elevated-closeout-20260716-015250/m4.log`).
- M5 acceptance suite: PASS (17 checks, `audits/M5/elevated-closeout-20260716-015250/m5.log`).
- Backup restore: PASS against final scheduled-task backup `20260716-015835`.
- WAL/PITR: PASS against final scheduled-task backup `20260716-015835`.
- Bifrost restart/reconnect: PASS in M4 and M5 suites.
- Memory-service restart/reconnect: PASS in M4 suite.
- Cognee unavailable degradation: PASS in M5 suite.
- Safe Cursor retrieval through unchanged `agentcore-gateway`: PASS in M4/M5 suites.
- Task Scheduler manual runs: PASS for `NightlyBackup`, `NightlyRestoreTest`, and `WeeklyMaintenance`; each returned result code `0` and uses repo-owned scripts under `D:\github\agentcore-control-plane\ops`.

## Rollback Procedure

1. Preserve the accepted backup directories above.
2. Disable Cognee if needed by creating `H:\AgentRuntime\agentcore-memory\cognee\COGNEE_DISABLED.flag`.
3. Restore PG18 logical dumps into an isolated instance first; use `Test-AgentCorePostgresRestore.ps1` as the restore proof.
4. For point-in-time recovery, restore the base backup and replay WAL from `E:\AgentCoreArchive\agentcore-memory\wal\pg18`.
5. If full platform rollback is required, stop/uninstall PG18 only after operator approval and return to the preserved PG16 rollback cluster at `127.0.0.1:55432`; Swarm-owned PG16 databases remain isolated.

## Elevated Closeout Result

- No elevated PG18/task hardening gaps remain.
- Remaining intentional PG16 references are rollback/legacy evidence, immutable constitutional residue requiring explicit approval to edit, historical documents, or Swarm-owned tooling.
- Swarm services, tasks, databases, paths, and launchers were not modified.
