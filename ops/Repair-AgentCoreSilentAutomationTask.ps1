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
if (-not (Get-AgentCoreSilentContractRepairBool -Entry $entry -Name 'make_silent_allowed')) { throw "make_silent_allowed=false for $TaskName" }
$resolvedPath = if ([string]::IsNullOrWhiteSpace($TaskPath)) { [string]$entry.task_path } else { $TaskPath }
if ([string]::IsNullOrWhiteSpace($resolvedPath)) { $resolvedPath = '\' }
if (Test-AgentCoreSilentPreserveFileArgs -Entry $entry) {
  Set-AgentCoreSilentConhostTask -TaskName $TaskName -TaskPath $resolvedPath -PreserveFileArgs
} else {
  $file = ([string](Get-AgentCoreJsonPropertyValue -Object $entry -Name 'file' -Default '')) -replace '/', '\'
  if (-not (Test-Path -LiteralPath $file)) { throw "Missing script file: $file" }
  Set-AgentCoreSilentConhostTask -TaskName $TaskName -TaskPath $resolvedPath -FilePath $file -ExtraArgs ([string](Get-AgentCoreJsonPropertyValue -Object $entry -Name 'extra_args' -Default ''))
}
Write-AgentCoreSilentAutomationAudit -Message ("REPAIR_SILENT task=$TaskName path=$resolvedPath") -Policy $policy
Write-Host "OK REPAIR_SILENT $TaskName"
