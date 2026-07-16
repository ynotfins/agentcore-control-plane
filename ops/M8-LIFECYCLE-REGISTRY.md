# AgentCore M8 Windows Lifecycle Registry

**Authority:** BLUEPRINT.md M8  
**Date:** 2026-07-16  
**Scope:** All required Windows-managed components for AgentCore CHAOSCENTRAL deployment

---

## Component Registry

### PostgreSQL 18

| Property | Value |
|----------|-------|
| **Component** | PostgreSQL 18 database server |
| **Mechanism** | Windows Scheduled Task (wraps service management) |
| **Task path** | `\AgentCore\PostgresRuntime` |
| **Data path** | `F:\PostgreSQL18\data` |
| **Binary path** | `F:\PostgreSQL18\bin\pg_ctl.exe` |
| **Endpoint** | `127.0.0.1:55433` |
| **Log location** | `F:\PostgreSQL18\data\log\` (PostgreSQL log_directory) |

**Start:**
```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'PostgresRuntime'
# Or directly:
& 'F:\PostgreSQL18\bin\pg_ctl.exe' start -D 'F:\PostgreSQL18\data' -l 'F:\PostgreSQL18\data\log\pg18.log'
```

**Stop:**
```powershell
# Stop the scheduled task (stops trigger; pg_ctl stop is needed for DB shutdown)
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'PostgresRuntime'
# Graceful shutdown:
& 'F:\PostgreSQL18\bin\pg_ctl.exe' stop -D 'F:\PostgreSQL18\data' -m fast
```

**Restart:**
```powershell
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'PostgresRuntime'
& 'F:\PostgreSQL18\bin\pg_ctl.exe' stop -D 'F:\PostgreSQL18\data' -m fast
Start-Sleep -Seconds 3
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'PostgresRuntime'
```

**Status:**
```powershell
# Scheduled task state:
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'PostgresRuntime' | Select State, LastRunTime
# Database connectivity:
& 'F:\PostgreSQL18\bin\psql.exe' -h 127.0.0.1 -p 55433 -U postgres -c 'SELECT version();'
```

**Restart-on-failure policy:** Task configured with restart-on-failure (3 retries, 1-minute interval).

---

### Bifrost Gateway

| Property | Value |
|----------|-------|
| **Component** | AgentCore Bifrost MCP gateway |
| **Mechanism** | Windows Scheduled Task |
| **Task path** | `\AgentCore\AgentCore-Bifrost-Gateway` |
| **Runtime root** | `H:\AgentRuntime\bifrost` |
| **Endpoint** | `http://127.0.0.1:8080/mcp` |
| **Log location** | `H:\AgentRuntime\service-logs\bifrost-*.log` |

**Start:**
```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
```

**Stop:**
```powershell
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
```

**Restart:**
```powershell
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
```

**Status:**
```powershell
# Task state:
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway' | Select State, LastRunTime
# HTTP health check (expects 401):
$r = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/mcp' -UseBasicParsing -ErrorAction SilentlyContinue
"Status: $($r.StatusCode)"
```

**Restart-on-failure policy:** Task configured with restart-on-failure (3 retries, 30-second interval).

---

### DailyDriftCheck

| Property | Value |
|----------|-------|
| **Component** | Daily context fabric drift detection |
| **Mechanism** | Windows Scheduled Task |
| **Task path** | `\AgentCore\DailyDriftCheck` |
| **Schedule** | Daily at 06:00 local time |
| **Script** | `ops/Test-AgentCoreDrift.ps1` (or context-fabric cf_drift) |
| **Log location** | `H:\AgentRuntime\service-logs\drift-*.log` |

**Start (manual trigger):**
```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'DailyDriftCheck'
```

**Stop (running instance):**
```powershell
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'DailyDriftCheck'
```

**Status:**
```powershell
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'DailyDriftCheck' | Select State, LastRunTime, LastTaskResult
```

**Restart-on-failure policy:** Task runs daily; failures logged but do not restart automatically (idempotent check).

---

### NightlyBackup

| Property | Value |
|----------|-------|
| **Component** | Nightly PostgreSQL backup |
| **Mechanism** | Windows Scheduled Task |
| **Task path** | `\AgentCore\NightlyBackup` |
| **Schedule** | Nightly at 02:00 local time |
| **Script** | `ops/Backup-AgentCorePostgres.ps1` |
| **Output** | `E:\DatabaseBackups\` (logical) + `G:\DatabaseBackups\` (DR mirror) |
| **Log location** | `H:\AgentRuntime\service-logs\backup-*.log` |

**Start (manual trigger):**
```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyBackup'
# Or directly:
powershell -ExecutionPolicy Bypass -File 'D:\github\agentcore-control-plane\ops\Backup-AgentCorePostgres.ps1'
```

**Stop:**
```powershell
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyBackup'
```

**Status:**
```powershell
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyBackup' | Select State, LastRunTime, LastTaskResult
# Check most recent backup file:
Get-ChildItem 'E:\DatabaseBackups\' -Filter '*.dump' | Sort-Object LastWriteTime -Descending | Select-Object -First 3
```

**Restart-on-failure policy:** Single retry on failure (1-hour delay). Alert operator if second attempt also fails.

---

### NightlyRestoreTest

| Property | Value |
|----------|-------|
| **Component** | Nightly restore verification test |
| **Mechanism** | Windows Scheduled Task |
| **Task path** | `\AgentCore\NightlyRestoreTest` |
| **Schedule** | Nightly at 04:00 local time (after NightlyBackup completes) |
| **Script** | `ops/Test-AgentCorePostgresRestore.ps1` |
| **Output** | `audits/M5/` restore test JSON results |
| **Log location** | `H:\AgentRuntime\service-logs\restore-test-*.log` |

**Start (manual trigger):**
```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyRestoreTest'
# Or directly:
powershell -ExecutionPolicy Bypass -File 'D:\github\agentcore-control-plane\ops\Test-AgentCorePostgresRestore.ps1'
```

**Stop:**
```powershell
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyRestoreTest'
```

**Status:**
```powershell
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyRestoreTest' | Select State, LastRunTime, LastTaskResult
# Review latest restore test result:
Get-ChildItem 'D:\github\agentcore-control-plane\audits\M5\' -Filter 'pg18-restore-test-*.json' | Sort LastWriteTime -Desc | Select -First 1
```

**Restart-on-failure policy:** Single retry (30-minute delay). Restore test failure is an alert condition.

---

### WeeklyMaintenance

| Property | Value |
|----------|-------|
| **Component** | Weekly maintenance (VACUUM, ANALYZE, WAL cleanup, log archival) |
| **Mechanism** | Windows Scheduled Task |
| **Task path** | `\AgentCore\WeeklyMaintenance` |
| **Schedule** | Sunday at 03:00 local time |
| **Script** | `ops/Invoke-AgentCoreMaintenance.ps1` |
| **Log location** | `H:\AgentRuntime\service-logs\maintenance-*.log` |

**Start (manual trigger):**
```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'WeeklyMaintenance'
# Or directly:
powershell -ExecutionPolicy Bypass -File 'D:\github\agentcore-control-plane\ops\Invoke-AgentCoreMaintenance.ps1'
```

**Stop:**
```powershell
Stop-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'WeeklyMaintenance'
```

**Status:**
```powershell
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'WeeklyMaintenance' | Select State, LastRunTime, LastTaskResult
```

**Restart-on-failure policy:** No automatic restart (maintenance tasks are idempotent; operator reviews weekly).

---

## Quick Reference: All Task Status

```powershell
# Check all AgentCore scheduled tasks at once:
Get-ScheduledTask -TaskPath '\AgentCore\' | Select TaskName, State, @{N='LastRun';E={$_.LastRunTime}}, @{N='Result';E={$_.LastTaskResult}} | Format-Table -AutoSize
```

---

## Common Recovery Procedures

### PostgreSQL not starting
1. Check `F:\PostgreSQL18\data\log\` for error messages
2. Verify data directory is writable: `Get-Acl F:\PostgreSQL18\data`
3. Check for lock file: `Test-Path F:\PostgreSQL18\data\postmaster.pid`
4. If stale lock: `Remove-Item F:\PostgreSQL18\data\postmaster.pid` (only if PG not running)
5. Restart: `Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'PostgresRuntime'`

### Bifrost not responding (no 401 on health check)
1. Check `H:\AgentRuntime\service-logs\bifrost-*.log`
2. Verify PostgreSQL is up (Bifrost depends on it)
3. Restart: `Stop-ScheduledTask ... ; Start-Sleep 2 ; Start-ScheduledTask ...`

### Backup failure
1. Check `H:\AgentRuntime\service-logs\backup-*.log` for error
2. Verify E: disk has sufficient space: `Get-PSDrive E`
3. Re-run manually: `powershell -File ops\Backup-AgentCorePostgres.ps1`
4. If persistent: run `python -m agentcore diagnose` for full diagnostic

### Restore test failure
1. Check restore test JSON in `audits/M5/`
2. Check restore log in `H:\AgentRuntime\service-logs\`
3. Verify most recent backup is intact: `Get-ChildItem E:\DatabaseBackups\ | Sort LastWriteTime -Desc | Select -First 3`
4. Re-run: `powershell -File ops\Test-AgentCorePostgresRestore.ps1`
