#Requires -Version 5.1
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$TaskName,
  [string]$TaskPath = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AgentCoreSilentAutomation.Common.ps1')
$policy = Get-AgentCoreSilentPolicyContract
$entry = Find-AgentCoreSilentContractTask -TaskName $TaskName -TaskPath $TaskPath -Policy $policy
if (-not $entry) { throw "Task not listed in contract: $TaskName" }
if (-not [bool]$entry.repair.disable_allowed) { throw "disable_allowed=false for $TaskName" }
$resolvedPath = if ([string]::IsNullOrWhiteSpace($TaskPath)) { [string]$entry.task_path } else { $TaskPath }
if ([string]::IsNullOrWhiteSpace($resolvedPath)) { $resolvedPath = '\' }
Disable-ScheduledTask -TaskName $TaskName -TaskPath $resolvedPath | Out-Null
Write-AgentCoreSilentAutomationAudit -Message ("DISABLE task=$TaskName path=$resolvedPath") -Policy $policy
Write-Host "OK DISABLED $TaskName"
