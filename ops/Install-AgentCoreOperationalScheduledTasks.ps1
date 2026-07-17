param(
  [string]$TaskPath = "\AgentCore\",
  [string]$ConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json",
  [string]$TaskBackupRoot = "E:\AgentCoreArchive\backups_cold\scheduled-tasks",
  [switch]$StartPostgresTask,
  [switch]$StartProjectionTask,
  [switch]$UseHighestRunLevel
)

$ErrorActionPreference = "Stop"

$repoOps = Split-Path -Parent $PSCommandPath
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = Join-Path $TaskBackupRoot $stamp
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

function Export-AgentCoreTaskBackup {
  param([string]$TaskName)
  try {
    $xml = Export-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
    $path = Join-Path $backupRoot "$TaskName.xml"
    $xml | Set-Content -LiteralPath $path -Encoding utf8
  } catch {
    # Task may not exist yet.
  }
}

function New-DailyRepeatingTrigger {
  param(
    [datetime]$At,
    [TimeSpan]$Interval
  )
  New-ScheduledTaskTrigger -Once -At $At -RepetitionInterval $Interval -RepetitionDuration ([TimeSpan]::FromDays(1))
}

function Register-AgentCoreTask {
  param(
    [string]$TaskName,
    [string]$ScriptName,
    [Microsoft.Management.Infrastructure.CimInstance[]]$Triggers,
    [string[]]$ScriptArguments = @(),
    [string]$WorkingDirectory = $repoOps
  )

  Export-AgentCoreTaskBackup -TaskName $TaskName

  $scriptPath = Join-Path $repoOps $ScriptName
  if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Required task script not found: $scriptPath"
  }

  $argumentParts = @("-NoProfile", "-ExecutionPolicy Bypass", "-File `"$scriptPath`"") + $ScriptArguments
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ($argumentParts -join " ") -WorkingDirectory $WorkingDirectory
  $settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable
  $runLevel = if ($UseHighestRunLevel) { "Highest" } else { "Limited" }
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel $runLevel
  $task = New-ScheduledTask -Action $action -Trigger $Triggers -Settings $settings -Principal $principal
  Register-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -InputObject $task -Force | Out-Null
}

# --- Monitor removal (rollout P8, per CONTEXT_BLOCK.md sec 9) -----------------------------------
# REMOVED from scheduled registration in this pass (now MANUAL validators only, run on demand):
#   - DailyDriftCheck (Test-AgentCoreDrift.ps1)          -> drift-scan monitor; run manually when needed
#   - ContextFabricReadiness (Test-AgentCoreContextFabricReadiness.ps1) -> every-2h readiness poll; run manually
# Also do NOT register any of: context-window-optimizer, pgvector/RAG/memory-projection/mcp-drift/
#   live-client-adoption/plugin-extension monitors, spec-sync, or any background re-audit loop.
# RETAINED (startup ownership + backup/restore/maintenance + governed projection pipeline):
#   PostgresRuntime, SwarmRecallMeilisearch, SwarmRecallApi, NightlyBackup, NightlyRestoreTest,
#   WeeklyMaintenance, MemoryProjection.
# ADDED (central durability and placement audit — layered frequency per §6 hardening spec):
#   DurabilityHealthCheck   — Health mode,   every 6 hours (lightweight, idempotent).
#   DurabilityResourceAudit — Resource mode, daily at 02:00 (complete resource/location audit).
#   DurabilityDeepAudit     — Deep mode,     weekly Sunday at 05:30 (deep recovery/retention/WAL).
#   These replace DailyDriftCheck for continuity/placement concerns.
#   No overlap with NightlyBackup (03:00), NightlyRestoreTest (03:30), WeeklyMaintenance (04:30).
# NOTE: Invoke-AgentCoreMemoryProjector.ps1 (MemoryProjection) is a GOVERNED MEMORY PIPELINE, not a
#   monitor. It is preserved. Removing the monitors from LIVE Task Scheduler requires an elevated run
#   of this script (or Unregister-ScheduledTask) and is an operator/admin action (hard gate).
# -----------------------------------------------------------------------------------------------
$nightlyBackup = New-ScheduledTaskTrigger -Daily -At 3:00am
$nightlyRestore = New-ScheduledTaskTrigger -Daily -At 3:30am
$weeklyMaintenance = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 4:30am
$postgresStartup = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$postgresStartup.Delay = "PT30S"
$swarmRecallMeilisearchStartup = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$swarmRecallMeilisearchStartup.Delay = "PT45S"
$swarmRecallApiStartup = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$swarmRecallApiStartup.Delay = "PT75S"
$projectionPipeline = New-DailyRepeatingTrigger -At ([datetime]"00:15") -Interval (New-TimeSpan -Hours 2)

# Durability audit triggers — layered frequency, no overlap with backup/restore/maintenance.
# 6h health: runs at 01:00 and repeats every 6h (lightweight health/continuity probe).
$durabilityHealth = New-DailyRepeatingTrigger -At ([datetime]"01:00") -Interval (New-TimeSpan -Hours 6)
# Daily resource: 02:00 (after midnight projection pipeline, before nightly backup).
$durabilityResource = New-ScheduledTaskTrigger -Daily -At 2:00am
# Weekly deep: Sunday 05:30 (after WeeklyMaintenance 04:30, before daily resource 02:00 next day).
$durabilityDeep = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 5:30am

Register-AgentCoreTask -TaskName "PostgresRuntime" -ScriptName "Start-AgentCorePostgres.ps1" -Triggers @($postgresStartup) -ScriptArguments @("-StartIfStopped")
Register-AgentCoreTask -TaskName "SwarmRecallMeilisearch" -ScriptName "Start-AgentCoreSwarmRecallComponent.ps1" -Triggers @($swarmRecallMeilisearchStartup) -ScriptArguments @("-Component Meilisearch", "-ConfigPath `"$ConfigPath`"")
Register-AgentCoreTask -TaskName "SwarmRecallApi" -ScriptName "Start-AgentCoreSwarmRecallComponent.ps1" -Triggers @($swarmRecallApiStartup) -ScriptArguments @("-Component Api", "-ConfigPath `"$ConfigPath`"")
Register-AgentCoreTask -TaskName "NightlyBackup" -ScriptName "Backup-AgentCorePostgres.ps1" -Triggers @($nightlyBackup)
Register-AgentCoreTask -TaskName "NightlyRestoreTest" -ScriptName "Test-AgentCorePostgresRestore.ps1" -Triggers @($nightlyRestore)
Register-AgentCoreTask -TaskName "WeeklyMaintenance" -ScriptName "Invoke-AgentCoreMaintenance.ps1" -Triggers @($weeklyMaintenance)
Register-AgentCoreTask -TaskName "MemoryProjection" -ScriptName "Invoke-AgentCoreMemoryProjector.ps1" -Triggers @($projectionPipeline)

# Central durability and placement audit tasks (§6 layered frequency).
Register-AgentCoreTask -TaskName "DurabilityHealthCheck" `
  -ScriptName "Test-AgentCoreDurabilityAndPlacement.ps1" `
  -Triggers @($durabilityHealth) `
  -ScriptArguments @("-Mode Health")

Register-AgentCoreTask -TaskName "DurabilityResourceAudit" `
  -ScriptName "Test-AgentCoreDurabilityAndPlacement.ps1" `
  -Triggers @($durabilityResource) `
  -ScriptArguments @("-Mode Resource")

Register-AgentCoreTask -TaskName "DurabilityDeepAudit" `
  -ScriptName "Test-AgentCoreDurabilityAndPlacement.ps1" `
  -Triggers @($durabilityDeep) `
  -ScriptArguments @("-Mode Deep")

if ($StartPostgresTask) {
  Start-ScheduledTask -TaskPath $TaskPath -TaskName "PostgresRuntime"
}

if ($StartProjectionTask) {
  Start-ScheduledTask -TaskPath $TaskPath -TaskName "MemoryProjection"
}

[pscustomobject]@{
  ok = $true
  backup_root = $backupRoot
  tasks = @(
    "PostgresRuntime", "SwarmRecallMeilisearch", "SwarmRecallApi",
    "NightlyBackup", "NightlyRestoreTest", "WeeklyMaintenance", "MemoryProjection",
    "DurabilityHealthCheck", "DurabilityResourceAudit", "DurabilityDeepAudit"
  )
  durability_audit_tasks = @(
    @{ name="DurabilityHealthCheck";   mode="Health";   schedule="every 6h from 01:00"; script="Test-AgentCoreDurabilityAndPlacement.ps1" },
    @{ name="DurabilityResourceAudit"; mode="Resource"; schedule="daily at 02:00";       script="Test-AgentCoreDurabilityAndPlacement.ps1" },
    @{ name="DurabilityDeepAudit";     mode="Deep";     schedule="weekly Sunday 05:30";  script="Test-AgentCoreDurabilityAndPlacement.ps1" }
  )
  removed_monitors = @("DailyDriftCheck", "ContextFabricReadiness")
  removed_monitors_note = "Removed from scheduled registration in rollout P8; run as manual validators on demand. Unregister live tasks via elevated Unregister-ScheduledTask (operator action)."
  runtime_tasks = @("PostgresRuntime", "SwarmRecallMeilisearch", "SwarmRecallApi")
  completed_at = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Depth 6
