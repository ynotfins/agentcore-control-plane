param(
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [string]$PgRoot = "F:\PostgreSQL18",
  [string]$PgData = "F:\PostgreSQL18\data",
  [string]$PgService = "AgentCore-PostgreSQL18",
  [string]$TaskPath = "\AgentCore\",
  [string]$EvidenceDir = "audits\M5",
  [int]$TaskTimeoutMinutes = 180
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

function Test-IsAdmin {
  return ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-NativeChecked {
  param(
    [string]$Command,
    [string[]]$Arguments,
    [string]$FailureMessage,
    [switch]$AllowFailure
  )
  $output = & $Command @Arguments 2>&1
  $code = $LASTEXITCODE
  $text = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
  if ($code -ne 0 -and -not $AllowFailure) {
    throw "$FailureMessage (exit $code): $text"
  }
  return [pscustomobject]@{ exit_code = $code; output = $text }
}

function Invoke-Step {
  param([string]$Name, [scriptblock]$Script)
  $started = Get-Date
  try {
    $result = & $Script
    $script:checks += [pscustomobject]@{
      name = $Name
      ok = $true
      started_at = $started.ToUniversalTime().ToString("o")
      completed_at = (Get-Date).ToUniversalTime().ToString("o")
      result = $result
    }
    return $result
  } catch {
    $script:checks += [pscustomobject]@{
      name = $Name
      ok = $false
      started_at = $started.ToUniversalTime().ToString("o")
      completed_at = (Get-Date).ToUniversalTime().ToString("o")
      error = $_.Exception.Message
    }
    throw
  }
}

function Get-Pg18OwnerSnapshot {
  $service = Get-CimInstance Win32_Service -Filter "Name='$PgService'"
  $ports = @(netstat -ano -p tcp | Select-String '127\.0\.0\.1:55433' | ForEach-Object { [string]$_ })
  $processes = @()
  foreach ($line in $ports) {
    $parts = ($line -replace "\s+", " ").Trim().Split(" ")
    $pidText = $parts[-1]
    if ($pidText -match '^\d+$') {
      $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pidText" -ErrorAction SilentlyContinue
      if ($proc) {
        $processes += [pscustomobject]@{
          process_id = [int]$pidText
          executable = $proc.ExecutablePath
          command_line = $proc.CommandLine
        }
      }
    }
  }
  return [pscustomobject]@{
    service = $service | Select-Object Name,State,StartMode,StartName,PathName,ProcessId
    ports = $ports
    processes = $processes
  }
}

function Wait-TaskComplete {
  param([string]$TaskName)
  $deadline = (Get-Date).AddMinutes($TaskTimeoutMinutes)
  do {
    Start-Sleep -Seconds 5
    $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName
    if ($task.State -ne "Running") {
      return Get-ScheduledTaskInfo -TaskPath $TaskPath -TaskName $TaskName
    }
  } while ((Get-Date) -lt $deadline)
  throw "Task timed out after $TaskTimeoutMinutes minutes: $TaskName"
}

function Set-AgentCoreTask {
  param(
    [string]$TaskName,
    [string]$ScriptName,
    [Microsoft.Management.Infrastructure.CimInstance[]]$Triggers
  )
  $backupRoot = Join-Path "E:\AgentCoreArchive\backups_cold\scheduled-tasks" ((Get-Date -Format "yyyyMMdd-HHmmss") + "-m0-m5-closeout")
  New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
  try {
    Export-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName | Set-Content -LiteralPath (Join-Path $backupRoot "$TaskName.xml") -Encoding utf8
  } catch {
    throw "Expected existing task missing or unreadable: $TaskName"
  }

  $scriptPath = Join-Path (Join-Path $RepoRoot "ops") $ScriptName
  if (-not (Test-Path -LiteralPath $scriptPath)) { throw "Task script missing: $scriptPath" }

  $action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory (Join-Path $RepoRoot "ops")
  $settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes $TaskTimeoutMinutes) `
    -RestartCount 0
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

  Register-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -Action $action -Trigger $Triggers -Settings $settings -Principal $principal -Force | Out-Null
  return [pscustomobject]@{ task = $TaskName; backup_root = $backupRoot; script = $scriptPath }
}

function Get-TaskSnapshot {
  param([string]$TaskName)
  $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName
  $info = Get-ScheduledTaskInfo -TaskPath $TaskPath -TaskName $TaskName
  return [pscustomobject]@{
    task = $TaskName
    state = $task.State.ToString()
    executable = $task.Actions[0].Execute
    arguments = $task.Actions[0].Arguments
    working_directory = $task.Actions[0].WorkingDirectory
    account = $task.Principal.UserId
    run_level = $task.Principal.RunLevel.ToString()
    logon_type = $task.Principal.LogonType.ToString()
    timeout = $task.Settings.ExecutionTimeLimit
    last_run_time = $info.LastRunTime
    last_task_result = $info.LastTaskResult
    next_run_time = $info.NextRunTime
    environment_handling = "Scripts read Windows environment variables at runtime; no .env files or task-embedded secrets."
  }
}

function Invoke-ScriptFile {
  param([string]$Path)
  $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Path 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0) { throw "Script failed ($code): $Path`n$($output -join "`n")" }
  return (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

if (-not (Test-IsAdmin)) {
  throw "Elevation unavailable: this script must run as Administrator."
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$repoEvidence = Join-Path $RepoRoot $EvidenceDir
New-Item -ItemType Directory -Path $repoEvidence -Force | Out-Null
$runRoot = Join-Path $repoEvidence "elevated-closeout-$stamp"
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null

$script:checks = @()
$pgBin = Join-Path $PgRoot "bin"
$pgCtl = Join-Path $pgBin "pg_ctl.exe"
$pgReady = Join-Path $pgBin "pg_isready.exe"
if (-not (Test-Path -LiteralPath $pgCtl)) { throw "pg_ctl missing: $pgCtl" }
if (-not (Test-Path -LiteralPath $pgReady)) { throw "pg_isready missing: $pgReady" }

$report = [ordered]@{
  ok = $false
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  elevated_user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
  repo_root = $RepoRoot
  run_root = $runRoot
  pre = [ordered]@{}
  post = [ordered]@{}
  checks = $null
}

$report.pre.pg18 = Get-Pg18OwnerSnapshot
$report.pre.pg16_read_only = if (Test-Path -LiteralPath "F:\AgentCore\postgres_runtime_engine\pgsql\bin\pg_isready.exe") {
  Invoke-NativeChecked -Command "F:\AgentCore\postgres_runtime_engine\pgsql\bin\pg_isready.exe" -Arguments @("-h", "127.0.0.1", "-p", "55432", "-d", "agent_core") -FailureMessage "PG16 read-only health failed" -AllowFailure
} else {
  [pscustomobject]@{ exit_code = 127; output = "PG16 pg_isready missing" }
}
$report.pre.tasks = @("NightlyBackup", "NightlyRestoreTest", "WeeklyMaintenance") | ForEach-Object { Get-TaskSnapshot -TaskName $_ }

Invoke-Step -Name "PG18 stop through current owner for clean handoff" -Script {
  $before = Get-Pg18OwnerSnapshot
  if ($before.ports.Count -gt 0) {
    Invoke-NativeChecked -Command $pgCtl -Arguments @("-D", $PgData, "stop", "-m", "fast", "-w") -FailureMessage "pg_ctl stop of existing PG18 process failed"
  } else {
    [pscustomobject]@{ exit_code = 0; output = "PG18 was not listening before service start" }
  }
}

Invoke-Step -Name "PG18 start through Windows service owner" -Script {
  Set-Service -Name $PgService -StartupType Automatic
  Start-Service -Name $PgService
  Start-Sleep -Seconds 5
  Invoke-NativeChecked -Command $pgReady -Arguments @("-h", "127.0.0.1", "-p", "55433", "-d", "agent_core") -FailureMessage "PG18 readiness after service start failed"
}

Invoke-Step -Name "PG18 restart through Windows service owner" -Script {
  Restart-Service -Name $PgService -Force
  Start-Sleep -Seconds 8
  Invoke-NativeChecked -Command $pgReady -Arguments @("-h", "127.0.0.1", "-p", "55433", "-d", "agent_core") -FailureMessage "PG18 readiness after service restart failed"
}

$dailyBackup = New-ScheduledTaskTrigger -Daily -At "03:00"
$dailyRestore = New-ScheduledTaskTrigger -Daily -At "03:30"
$weeklyMaintenance = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "04:30"

Invoke-Step -Name "Retarget NightlyBackup task" -Script { Set-AgentCoreTask -TaskName "NightlyBackup" -ScriptName "Backup-AgentCorePostgres.ps1" -Triggers @($dailyBackup) }
Invoke-Step -Name "Retarget NightlyRestoreTest task" -Script { Set-AgentCoreTask -TaskName "NightlyRestoreTest" -ScriptName "Test-AgentCorePostgresRestore.ps1" -Triggers @($dailyRestore) }
Invoke-Step -Name "Retarget WeeklyMaintenance task" -Script { Set-AgentCoreTask -TaskName "WeeklyMaintenance" -ScriptName "Invoke-AgentCoreMaintenance.ps1" -Triggers @($weeklyMaintenance) }

$taskResults = @()
foreach ($taskName in @("NightlyBackup", "NightlyRestoreTest", "WeeklyMaintenance")) {
  $taskResults += Invoke-Step -Name "Manual Task Scheduler run: $taskName" -Script {
    Start-ScheduledTask -TaskPath $TaskPath -TaskName $taskName
    $info = Wait-TaskComplete -TaskName $taskName
    if ($info.LastTaskResult -ne 0) { throw "$taskName failed with result $($info.LastTaskResult)" }
    Get-TaskSnapshot -TaskName $taskName
  }
}

$report.post.tasks = @("NightlyBackup", "NightlyRestoreTest", "WeeklyMaintenance") | ForEach-Object { Get-TaskSnapshot -TaskName $_ }
$report.post.pg18 = Get-Pg18OwnerSnapshot
$report.post.pg16_read_only = if (Test-Path -LiteralPath "F:\AgentCore\postgres_runtime_engine\pgsql\bin\pg_isready.exe") {
  Invoke-NativeChecked -Command "F:\AgentCore\postgres_runtime_engine\pgsql\bin\pg_isready.exe" -Arguments @("-h", "127.0.0.1", "-p", "55432", "-d", "agent_core") -FailureMessage "PG16 read-only health failed" -AllowFailure
} else {
  [pscustomobject]@{ exit_code = 127; output = "PG16 pg_isready missing" }
}

$scripts = [ordered]@{
  m2 = Join-Path $RepoRoot "scripts\memory_platform\Test-M2CanonicalIdentity.ps1"
  m3 = Join-Path $RepoRoot "scripts\memory_platform\Test-M3LosslessContext.ps1"
  m4 = Join-Path $RepoRoot "scripts\memory_platform\Test-M4Gateway.ps1"
  m5 = Join-Path $RepoRoot "scripts\memory_platform\Test-M5HybridRetrieval.ps1"
  restore = Join-Path $RepoRoot "ops\Test-AgentCorePostgresRestore.ps1"
  pitr = Join-Path $RepoRoot "ops\Test-AgentCorePg18Pitr.ps1"
}
foreach ($key in $scripts.Keys) {
  $path = $scripts[$key]
  Invoke-Step -Name "Regression $key" -Script {
    $output = Invoke-ScriptFile -Path $path
    $logPath = Join-Path $runRoot "$key.log"
    $output | Set-Content -LiteralPath $logPath -Encoding utf8
    [pscustomobject]@{ log = $logPath; tail = (($output -split "`n") | Select-Object -Last 12) -join "`n" }
  } | Out-Null
}

Invoke-Step -Name "Repository validators and secret scan" -Script {
  $commands = @(
    @{ exe = "python"; args = @((Join-Path $RepoRoot "scripts\bifrost\validate_contracts.py")) },
    @{ exe = "python"; args = @((Join-Path $RepoRoot "scripts\bifrost\test_contracts.py")) },
    @{ exe = "powershell.exe"; args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $RepoRoot "validators\validate-control-plane.ps1"), "-DryRun") }
  )
  $combined = @()
  foreach ($cmd in $commands) {
    $out = & $cmd.exe @($cmd.args) 2>&1
    $combined += $out
    if ($LASTEXITCODE -ne 0) { throw "Validator failed: $($cmd.exe) $($cmd.args -join ' ')" }
  }
  $logPath = Join-Path $runRoot "repository-validators.log"
  ($combined | ForEach-Object { [string]$_ }) | Set-Content -LiteralPath $logPath -Encoding utf8
  [pscustomobject]@{ log = $logPath }
} | Out-Null

$report.post.latest_backup = Get-ChildItem -LiteralPath "E:\AgentCoreArchive\agentcore-memory\backups\pg18" -Directory |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 -ExpandProperty FullName
$report.post.latest_backup_g = if ($report.post.latest_backup) {
  $leaf = Split-Path -Leaf $report.post.latest_backup
  "G:\AgentCoreArchive\agentcore-memory\backups\pg18\$leaf"
} else { $null }
$report.post.wal_archive = "E:\AgentCoreArchive\agentcore-memory\wal\pg18"
$report.post.wal_dr_copy = "G:\AgentCoreArchive\agentcore-memory\wal\pg18"

$report.ok = -not (@($script:checks | Where-Object { -not $_.ok }))
$report.checks = $script:checks
$reportPath = Join-Path $repoEvidence "elevated-closeout-$stamp.json"
$report | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $reportPath -Encoding utf8
$report | ConvertTo-Json -Depth 16
if (-not $report.ok) { exit 1 }
