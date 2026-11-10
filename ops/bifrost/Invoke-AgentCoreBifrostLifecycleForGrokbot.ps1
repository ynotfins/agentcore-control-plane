#Requires -Version 7.0
<#
.SYNOPSIS
  Narrow Bifrost gateway lifecycle helper for Grok Bot standing backup (operator decision 1B).
.DESCRIPTION
  Wraps existing Start / Stop / Status / Test ops scripts. Logs to F:\AgentCore\runtime\bifrost\logs\grokbot-lifecycle.log (no secrets).
#>
param(
  [Parameter(Mandatory)]
  [ValidateSet('Start', 'Stop', 'Status', 'Test')]
  [string]$Action
)

$ErrorActionPreference = 'Stop'

$RepoRoot = 'D:\github\agentcore-control-plane'
$OpsDir = Join-Path $RepoRoot 'ops\bifrost'
$LogPath = 'F:\AgentCore\runtime\bifrost\logs\grokbot-lifecycle.log'

function Write-GrokbotLifecycleLog {
  param([string]$Message, [int]$ExitCode = 0)
  $line = '[{0}] action={1} exit={2} {3}' -f (Get-Date).ToString('o'), $Action, $ExitCode, $Message
  $logDir = Split-Path $LogPath -Parent
  if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
  Add-Content -LiteralPath $LogPath -Value $line -Encoding utf8
  Write-Host $line
}

function Invoke-WrappedScript {
  param([string]$ScriptName)
  $scriptPath = Join-Path $OpsDir $ScriptName
  if (-not (Test-Path -LiteralPath $scriptPath)) { throw "Missing wrapper target: $scriptPath" }
  Write-GrokbotLifecycleLog -Message ("invoke $ScriptName")
  & $scriptPath
  if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { return $LASTEXITCODE }
  if (-not $?) { return 1 }
  return 0
}

$exitCode = 0
try {
  Write-GrokbotLifecycleLog -Message 'begin'
  switch ($Action) {
    'Start' { $exitCode = Invoke-WrappedScript 'Start-AgentCoreBifrostGateway.ps1' }
    'Stop' { $exitCode = Invoke-WrappedScript 'Stop-AgentCoreBifrostGateway.ps1' }
    'Status' { $exitCode = Invoke-WrappedScript 'Get-BifrostStatus.ps1' }
    'Test' { $exitCode = Invoke-WrappedScript 'Test-AgentCoreBifrostGateway.ps1' }
  }
  Write-GrokbotLifecycleLog -Message 'end' -ExitCode $exitCode
  exit $exitCode
} catch {
  Write-GrokbotLifecycleLog -Message ("ERROR $($_.Exception.Message)") -ExitCode 1
  exit 1
}
