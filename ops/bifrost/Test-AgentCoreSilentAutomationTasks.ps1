#Requires -Version 5.1
<#
.SYNOPSIS
  Fail if Enabled AgentCore / NFA / OmniRoute shell tasks can flash a visible console.

.DESCRIPTION
  Enforces the non-intrusive automation mandate. Exit 0 = pass; exit 1 = regression.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path (Split-Path $PSScriptRoot -Parent) 'AgentCoreSilentAutomation.Common.ps1')

$policy = Get-AgentCoreSilentPolicyContract
$failures = @()
$checked = 0

Get-ScheduledTask | Where-Object { Test-AgentCoreTaskNameMatchesSilentPolicy -TaskName $_.TaskName -Policy $policy } | ForEach-Object {
  if (-not $_.Settings.Enabled) { return }
  $checked++
  $ok = Test-AgentCoreTaskIsSilent -ScheduledTask $_ -Policy $policy
  if (-not $ok) {
    $action = $_.Actions | Select-Object -First 1
    $failures += [pscustomobject]@{
      Task = $_.TaskName
      TaskPath = $_.TaskPath
      HiddenSetting = [bool]$_.Settings.Hidden
      Execute = [string]$action.Execute
      Arguments = [string]$action.Arguments
    }
  }
}

Write-Host "Checked enabled matching tasks with shell actions: $checked"
if ($failures.Count -gt 0) {
  Write-Host 'FAIL: visible-console regressions detected:' -ForegroundColor Red
  $failures | Format-List | Out-String | Write-Host
  exit 1
}

Write-Host 'PASS: enabled matching shell tasks use conhost --headless with Hidden settings.' -ForegroundColor Green
exit 0
