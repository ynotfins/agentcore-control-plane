# AgentCore PG18 Backup, Restore, WAL, and PITR Runbook

`BLUEPRINT.md` remains authority. This runbook records the current PG18 operational path for M0-M5 hardening.

## Canonical Paths

- PG18 service/data: `AgentCore-PostgreSQL18`, `F:\PostgreSQL18\data`, `127.0.0.1:55433`.
- Primary backup: `E:\AgentCoreArchive\agentcore-memory\backups\pg18`.
- Secondary backup copy: `I:\AgentCoreArchive\agentcore-memory\backups\pg18` (internal `AgentCore_Staging`; keep used percent under 75 and at least 8 GB free).
- WAL archive: `E:\AgentCoreArchive\agentcore-memory\wal\pg18`.
- WAL DR copy: `I:\AgentCoreArchive\agentcore-memory\wal\pg18` (best-effort second copy; must not fail `archive_command`).
- Second-copy policy: `contracts/secondary-backup-drive-policy.json`. Moved from removable `G:` to `I:` on 2026-11-17 (Tony-approved) because `G:` was assigned to whichever USB drive was plugged in.
- Volume-identity guard: the WAL copy, the nightly backup-set copy and the prune job act only when the volume mounted at `I:` has volume GUID `\\?\Volume{ac27f734-60e4-4783-a6ec-6e9f922ad9d1}\` (serial `A60FC108`, recorded for reference). On a missing drive, mismatched GUID, unreadable identity or exceeded headroom they skip with a warning, create no folders, and never fail `archive_command` or the primary `E:` backup.
- Restore test roots: `F:\AgentCore\staging\restore-tests\pg18*` (disposable).

## Commands

Run from `D:\github\agentcore-control-plane`.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\Backup-AgentCorePostgres.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\Test-AgentCorePostgresRestore.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\Test-AgentCorePg18Pitr.ps1
```

WAL was enabled with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\Enable-AgentCorePg18Wal.ps1
```

## Lifecycle Ownership

The live PG18 process is owned by Windows service `AgentCore-PostgreSQL18` (`Automatic`,
`NT AUTHORITY\NetworkService`). The maintenance tasks `NightlyBackup`, `NightlyRestoreTest`,
and `WeeklyMaintenance` call the source-controlled scripts in `D:\github\agentcore-control-plane\ops`
and were manually verified through Task Scheduler during elevated closeout.

`SecondaryBackupHeadroom` runs daily at 01:45 and applies `ops/Prune-AgentCoreSecondaryBackupDrive.ps1 -Apply`
to the `I:` second-copy roots only (7 daily / 4 weekly / 12 monthly backup sets; WAL kept from the oldest
retained daily backup). It never deletes `E:` WAL/backups or `F:\PostgreSQL18\data`.

Do not move active `pg_wal` off F:. The primary WAL archive stays on E:; I: holds only the guarded second copy above. Do not touch Swarm-owned PG16 configuration.
