# Backup / WAL E: Drive Blocker — Evidence Report

**Generated:** 2026-07-01 (session: AgentCore continuation)  
**Source authority:** `D:\github\agentcore-control-plane`  
**Status:** BLOCKER — NightlyBackup failing; WAL archiving failing silently. Operator action required.

---

## Summary

The E: archive USB drive is **unmounted**. Both the nightly Postgres base backup and WAL continuous
archiving are targeting E:\ paths. Both are currently failing. The next scheduled backup run is
**2026-07-01 03:00:00 AM local** — less than 3 hours from report generation.

Additional issue: all four non-startup scheduled tasks point to the **old D:\MCP-Control-Plane ops
path** instead of the canonical source-controlled path at D:\github\agentcore-control-plane\ops\.

---

## Findings

### 1. E: Drive Status

```
E: mounted: FALSE (Test-Path "E:\" returned False)
G: mounted: TRUE  (available backup target)
```

**Role of each drive per PROJECT_ANCHOR.md §2:**
- `E:` — Archive / cold storage / backups / exports / emergency spool only (no primary SQL)
- `G:` — Backup target only

G: is the correct fallback when E: is unavailable.

### 2. NightlyBackup Scheduled Task

```
TaskName:       \AgentCore\NightlyBackup
State:          Ready
Last run:       2026-06-30 03:00:01 AM
Next run:       2026-07-01 03:00:00 AM
LastTaskResult: 1  (FAIL)
MissedRuns:     0

Action script:  D:\MCP-Control-Plane\ops\Backup-AgentCorePostgres.ps1
Action args:    (none — no -BackupRoot passed)
```

**Root causes (stacked):**
1. Script path is old (`D:\MCP-Control-Plane`) — not the canonical source-controlled version.
2. The D:\MCP-Control-Plane version has `[string]$BackupRoot,` with no default and no value passed
   by the task, causing the script to attempt `New-Item -Path ""` which fails.
3. Even if the source-controlled version were used, E:\ is unmounted.

**Source-controlled fix applied:** `ops/Backup-AgentCorePostgres.ps1` now auto-detects E: and falls
back to `G:\AgentCoreArchive\backups_cold\pgvector\base` when E: is unmounted.

**Operator action required (elevated shell):**

```powershell
# Update NightlyBackup to use source-controlled script with explicit G: fallback arg
$action = New-ScheduledTaskAction `
  -Execute 'powershell.exe' `
  -Argument '-NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Backup-AgentCorePostgres.ps1"'
Set-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyBackup' -Action $action
```

> Once E: is reconnected, no further change is needed — the script auto-prefers E: when mounted.
> Alternatively: reconnect E: USB before 03:00 AM tonight for the canonical backup path.

### 3. WAL Archiving (postgresql.conf)

```
archive_mode = on
archive_timeout = '15min'
archive_command = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File
  "D:/MCP-Control-Plane/ops/Archive-AgentCoreWal.ps1" "%p" "%f"'
```

**Issues:**
1. Script path is old (`D:\MCP-Control-Plane`) — not canonical.
2. The D:\MCP-Control-Plane version passes `$SourcePath` and `$WalFileName` positionally but uses
   an unset `$ArchiveRoot` → writes to `""` → FAIL → WAL files accumulate in `pg_wal/archive_status/ready/`.

**Risk:** Unarchived WAL files accumulate in `F:\AgentCore\database_cluster\pg_wal`. On a busy system
this can fill the F: runtime drive. Monitor `F:\AgentCore\database_cluster\pg_wal\archive_status\ready\`
for accumulation.

**Source-controlled fix applied:** `ops/Archive-AgentCoreWal.ps1` now auto-detects E: and falls back
to `G:\AgentCoreArchive\backups_cold\pgvector\wal`.

**Operator action required (postgresql.conf update + service reload):**

```powershell
# Step 1: Unlock postgresql.conf (read-only protection may apply — check attrib)
# Step 2: Replace the archive_command line:
#   Old: 'powershell.exe ... "D:/MCP-Control-Plane/ops/Archive-AgentCoreWal.ps1" "%p" "%f"'
#   New: 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:/github/agentcore-control-plane/ops/Archive-AgentCoreWal.ps1" "%p" "%f"'
# Step 3: Reload Postgres config (no restart required for archive_command change):
#   psql -h 127.0.0.1 -p 55432 -U agent_admin -c "SELECT pg_reload_conf();"
```

> Note: Do NOT change archive_mode or archive_timeout — only the archive_command path.
> After reload, check pg_wal/archive_status/ready/ to confirm WAL files start being archived.

### 4. Other Stale Scheduled Task Paths

These tasks also point to D:\MCP-Control-Plane but are lower-urgency (no imminent failure):

| Task | Current Path | Canonical Path |
|------|-------------|----------------|
| NightlyRestoreTest | `D:\MCP-Control-Plane\ops\Test-AgentCorePostgresRestore.ps1` | `D:\github\agentcore-control-plane\ops\Test-AgentCorePostgresRestore.ps1` |
| WeeklyMaintenance | `D:\MCP-Control-Plane\ops\Invoke-AgentCoreMaintenance.ps1` | `D:\github\agentcore-control-plane\ops\Invoke-AgentCoreMaintenance.ps1` |
| DailyDriftCheck | `D:\MCP-Control-Plane\ops\Test-AgentCoreDrift.ps1` | **Remove** (removed from Install-AgentCoreOperationalScheduledTasks.ps1 in 2026-06-30 rollout) |

**Operator action (all three, elevated shell):**

```powershell
# Update NightlyRestoreTest
$a = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument '-NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Test-AgentCorePostgresRestore.ps1"'
Set-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyRestoreTest' -Action $a

# Update WeeklyMaintenance
$a = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument '-NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Invoke-AgentCoreMaintenance.ps1"'
Set-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'WeeklyMaintenance' -Action $a

# Remove DailyDriftCheck (was removed from source-controlled task installer; still active in Task Scheduler)
Unregister-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'DailyDriftCheck' -Confirm:$false
```

---

## Immediate Risk

**CRITICAL — NightlyBackup will fail AGAIN tonight at 03:00 AM.**

If E: cannot be reconnected before 03:00 AM:
- Reconnect E: USB before 03:00 AM (canonical path, no config change needed), OR
- Run the elevated task update command (section 2) to switch the task to the fixed source-controlled script

The fixed source-controlled script auto-falls to G: when E: is unmounted, so once the task
points to the correct script it will succeed regardless of E: state.

---

## Source-Controlled Changes Applied This Session

| File | Change |
|------|--------|
| `ops/Backup-AgentCorePostgres.ps1` | Added E:/G: auto-detect fallback when E: unmounted |
| `ops/Archive-AgentCoreWal.ps1` | Added E:/G: auto-detect fallback when E: unmounted |

These changes are safe to commit and push. They do not alter script behavior when E: is mounted.

---

## Verification Commands (after operator remediation)

```powershell
# Verify NightlyBackup task action updated
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'NightlyBackup' |
  Select-Object -ExpandProperty Actions | Format-List

# Verify WAL archive_command updated in postgresql.conf
Select-String -Path 'F:\AgentCore\database_cluster\postgresql.conf' -Pattern 'archive_command'

# Check WAL accumulation (should be 0 or low after archiving resumes)
(Get-ChildItem "F:\AgentCore\database_cluster\pg_wal\archive_status\ready" -ErrorAction SilentlyContinue).Count

# Run manual backup smoke (non-elevated, using source-controlled script)
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Backup-AgentCorePostgres.ps1"
```
