# AgentCore PG18 Backup, Restore, WAL, and PITR Runbook

`BLUEPRINT.md` remains authority. This runbook records the current PG18 operational path for M0-M5 hardening.

## Canonical Paths

- PG18 service/data: `AgentCore-PostgreSQL18`, `F:\PostgreSQL18\data`, `127.0.0.1:55433`.
- Primary backup: `E:\AgentCoreArchive\agentcore-memory\backups\pg18`.
- Secondary backup copy: `G:\AgentCoreArchive\agentcore-memory\backups\pg18`.
- WAL archive: `E:\AgentCoreArchive\agentcore-memory\wal\pg18`.
- WAL DR copy: `G:\AgentCoreArchive\agentcore-memory\wal\pg18`.
- Restore test roots: `I:\AgentCoreRestoreTests\pg18*` (disposable).

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

Do not move active `pg_wal` off F:. Do not write WAL archive to I:. Do not touch Swarm-owned PG16 configuration.
