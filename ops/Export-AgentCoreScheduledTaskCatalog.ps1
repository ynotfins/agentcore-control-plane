#Requires -Version 5.1
[CmdletBinding()]
param(
  [string]$OutFile = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AgentCoreSilentAutomation.Common.ps1')
$policy = Get-AgentCoreSilentPolicyContract
$rows = New-Object System.Collections.Generic.List[object]
foreach ($entry in @($policy.tasks)) {
  $tp = if ([string]::IsNullOrWhiteSpace($entry.task_path)) { '\' } else { [string]$entry.task_path }
  $task = Get-ScheduledTask -TaskName $entry.task_name -TaskPath $tp -ErrorAction SilentlyContinue
  $info = $null
  if ($task) { $info = Get-ScheduledTaskInfo -TaskName $entry.task_name -TaskPath $tp -ErrorAction SilentlyContinue }
  $silentOk = if ($task) { Test-AgentCoreTaskIsSilent -ScheduledTask $task -Policy $policy } else { $null }
  $silentReason = if ($task) { Get-AgentCoreTaskSilentReason -ScheduledTask $task -Policy $policy } else { 'task_missing' }
  if ($silentOk -eq $true) { $silentReason = $null }
  $action0 = if ($task) { $task.Actions | Select-Object -First 1 } else { $null }
  $rows.Add([ordered]@{
    task_name = $entry.task_name
    task_path = $tp
    purpose = Get-AgentCoreJsonPropertyValue -Object $entry -Name 'purpose'
    schedule_class = Get-AgentCoreJsonPropertyValue -Object $entry -Name 'schedule_class'
    critical = [bool](Get-AgentCoreJsonPropertyValue -Object $entry -Name 'critical' -Default $false)
    enabled = if ($task) { [bool]$task.Settings.Enabled } else { $null }
    state = if ($task) { [string]$task.State } else { 'Missing'
    }
    execute = if ($action0) { [string]$action0.Execute } else { $null }
    silent_ok = $silentOk
    silent_reason = $silentReason
    make_silent_allowed = Get-AgentCoreSilentContractRepairBool -Entry $entry -Name 'make_silent_allowed'
    disable_allowed = Get-AgentCoreSilentContractRepairBool -Entry $entry -Name 'disable_allowed'
    last_run = if ($info) { $info.LastRunTime } else { $null }
    next_run = if ($info) { $info.NextRunTime } else { $null }
    last_task_result = if ($info) { $info.LastTaskResult } else { $null }
  })
}
$payload = [ordered]@{
  exported_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  schema_version = $policy.schema_version
  tasks = $rows
}
$json = $payload | ConvertTo-Json -Depth 6
if ([string]::IsNullOrWhiteSpace($OutFile)) {
  Write-Output $json
} else {
  Set-Content -LiteralPath $OutFile -Value $json -Encoding UTF8
  Write-Host "WROTE $OutFile"
}
