# Recipe 07 — Windows Service and Scheduled Task Recovery

**Pattern:** Register, restart, and verify native Windows services without Docker/WSL.  
**Stack:** PowerShell 5.1+, Windows Task Scheduler, SC.exe.  
**Authority:** `docs/engineering/CONSTITUTION.md` §14, `BLUEPRINT.md` §4.

---

## Bifrost Gateway (Scheduled Task — current pattern)

```powershell
# Check status
Get-ScheduledTask -TaskName "AgentCore\AgentCore-Bifrost-Gateway" | Select-Object State

# Restart
Stop-ScheduledTask -TaskName "AgentCore\AgentCore-Bifrost-Gateway"
Start-ScheduledTask -TaskName "AgentCore\AgentCore-Bifrost-Gateway"

# Verify
Start-Sleep -Seconds 5
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8080/health" -TimeoutSec 5
    Write-Host "Bifrost: $($r.StatusCode)"
} catch {
    Write-Host "Bifrost not reachable: $_"
}
```

## PostgreSQL 18 Service

```powershell
# Status
Get-Service -Name "postgresql-x64-18" | Select-Object Status

# Restart
Restart-Service -Name "postgresql-x64-18" -Force

# Verify connectivity
$pass = $env:AGENT_CORE_POSTGRES_PASSWORD
& "F:\PostgreSQL18\bin\psql.exe" "host=127.0.0.1 port=55433 dbname=agent_core user=postgres password=$pass" -c "SELECT 1"
```

## Register a New Scheduled Task

```powershell
$action = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "D:\path\to\service.py" `
    -WorkingDirectory "D:\path\to"

$trigger = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit "00:00:00" `  # no time limit
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "AgentCore\MyService" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal
```

## Recovery After Restart

1. Query all AgentCore scheduled tasks:
   ```powershell
   Get-ScheduledTask -TaskPath "\AgentCore\" | Select-Object TaskName, State
   ```
2. Start any that are `Ready` but not `Running`:
   ```powershell
   Get-ScheduledTask -TaskPath "\AgentCore\" | Where-Object { $_.State -eq 'Ready' } | Start-ScheduledTask
   ```
3. Verify health endpoints and PostgreSQL connectivity.

## Rollback Pattern

- Keep previous binary/script version as `service.py.bak` or in Git.
- `git checkout <previous-sha> -- path/to/service.py` to restore.
- Restart the task after rollback.

## Rules

- No Docker or WSL for core AgentCore services.
- H: contains the live Bifrost runtime — never format or relocate without backup.
- F: contains PostgreSQL 18 data — never point a different instance at F:\PostgreSQL18\data.
- Secrets: Windows User-scope env vars. Services must read them at startup.
