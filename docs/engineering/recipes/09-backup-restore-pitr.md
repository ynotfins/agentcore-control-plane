# Recipe 09 — Backup, Restore, and Point-in-Time Recovery

**Pattern:** Logical + physical backup with verified restore and WAL-based PITR.  
**Stack:** PostgreSQL 18, PowerShell.  
**Authority:** `BLUEPRINT.md` §11, `docs/memory-platform/BACKUP_RESTORE_WAL_PITR.md`.

---

## Logical Backup (pg_dump)

```powershell
$ts   = Get-Date -Format "yyyyMMddHHmmss"
$dest = "E:\DatabaseBackups\agent_core_$ts.dump"
$pass = $env:AGENT_CORE_POSTGRES_PASSWORD

& "F:\PostgreSQL18\bin\pg_dump.exe" `
    --host=127.0.0.1 --port=55433 `
    --username=agentcore_backup `
    --format=custom --compress=9 `
    --file=$dest `
    agent_core

# Verify
if (Test-Path $dest) {
    $size = (Get-Item $dest).Length
    Write-Host "Logical backup OK: $dest ($size bytes)"
} else {
    Write-Error "Logical backup FAILED"
}
```

## Physical Backup (pg_basebackup)

```powershell
$dest = "E:\AgentCoreArchive\basebackup_$ts"
& "F:\PostgreSQL18\bin\pg_basebackup.exe" `
    --host=127.0.0.1 --port=55433 `
    --username=agentcore_backup `
    --pgdata=$dest `
    --format=tar --compress=9 --checkpoint=fast `
    --progress --verbose
```

## Restore Test (isolated instance)

```powershell
$restoreDir = "I:\pg18-restore-test-$ts"
New-Item -ItemType Directory -Path $restoreDir

# Extract base backup
tar -xzf "$dest\base.tar.gz" -C $restoreDir

# Minimal postgresql.conf override for isolated port
"port = 55499" >> "$restoreDir\postgresql.conf"

# Start isolated instance
& "F:\PostgreSQL18\bin\pg_ctl.exe" -D $restoreDir start -l "$restoreDir\restore_test.log"
Start-Sleep -Seconds 10

# Verify
& "F:\PostgreSQL18\bin\psql.exe" "host=127.0.0.1 port=55499 dbname=agent_core user=postgres password=$pass" `
    -c "SELECT COUNT(*) FROM agentcore.schema_migrations"

# Stop and clean up
& "F:\PostgreSQL18\bin\pg_ctl.exe" -D $restoreDir stop
Remove-Item -Recurse -Force $restoreDir
```

## WAL Archive Configuration (postgresql.conf)

```ini
wal_level = replica
archive_mode = on
archive_command = 'copy "%p" "E:\\AgentCoreArchive\\wal_archive\\%f"'
restore_command = 'copy "E:\\AgentCoreArchive\\wal_archive\\%f" "%p"'
```

## Point-in-Time Recovery

```powershell
# 1. Stop primary PostgreSQL 18
Stop-Service -Name "postgresql-x64-18"

# 2. Copy base backup to recovery directory
Copy-Item -Recurse "E:\AgentCoreArchive\basebackup_<ts>" "F:\pg18-pitr-recover"

# 3. Create recovery.signal and postgresql.conf with recovery target
"recovery_target_time = '2026-07-16 02:00:00+00'" >> "F:\pg18-pitr-recover\postgresql.conf"
"restore_command = 'copy ""E:\\AgentCoreArchive\\wal_archive\\%f"" ""%p""'" >> "F:\pg18-pitr-recover\postgresql.conf"
New-Item -ItemType File -Path "F:\pg18-pitr-recover\recovery.signal"

# 4. Start recovery instance and verify
```

## Rules

- A backup is NOT accepted until a restore test succeeds.
- Never delete a backup until the next backup's restore test passes.
- Backup copies: E: (primary) and G: (second copy).
- WAL archive lives on E:. Never on I: or C:.
- Document the backup SHA-256 manifest and store it alongside the backup.
