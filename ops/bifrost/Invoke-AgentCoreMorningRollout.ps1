<#
.SYNOPSIS
  Approval-gated morning rollout helper for Cursor global MCP cleanup and Bifrost live rollout.

.DESCRIPTION
  Default behavior is read-only: run the morning readiness checker and print the
  required approval switches. Mutating phases execute only when their explicit
  approval switches are provided by the operator in the current shell command.

  This helper does not run Sally/Swarm acceptance and does not start production
  LangGraph work. Those remain separate postflight phases.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$CursorMcpPath = 'C:\Users\ynotf\.cursor\mcp.json',
  [switch]$ApproveCursorCleanup,
  [switch]$ApproveBifrostRollout,
  [switch]$SkipInitialReadiness
)

$ErrorActionPreference = 'Stop'

function Write-Section {
  param([string]$Text)
  Write-Host ''
  Write-Host "=== $Text ==="
}

function Invoke-RepoScript {
  param(
    [string]$RelativePath,
    [hashtable]$Parameters = @{}
  )
  $script = Join-Path $RepoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
    throw "Required script missing: $script"
  }
  & $script @Parameters
  if ($LASTEXITCODE -ne 0) {
    throw "Script failed: $script exit=$LASTEXITCODE"
  }
}

function Invoke-Readiness {
  Write-Section 'Read-only morning readiness'
  $checker = Join-Path $RepoRoot 'ops\bifrost\Test-AgentCoreMorningReadiness.ps1'
  if (-not (Test-Path -LiteralPath $checker -PathType Leaf)) {
    throw "Readiness checker missing: $checker"
  }
  & $checker
  return $LASTEXITCODE
}

if (-not $SkipInitialReadiness) {
  $initialReadinessExit = Invoke-Readiness
} else {
  $initialReadinessExit = 0
}

if (-not $ApproveCursorCleanup -and -not $ApproveBifrostRollout) {
  Write-Section 'No live approvals supplied'
  Write-Host 'No live mutation was requested or performed.'
  Write-Host 'To approve Cursor cleanup, rerun with -ApproveCursorCleanup.'
  Write-Host 'To approve Bifrost live rollout, rerun from elevated PowerShell with -ApproveBifrostRollout.'
  Write-Host 'Recommended order: approve Cursor cleanup first, then Bifrost rollout.'
  if ($initialReadinessExit -ne 0) {
    exit $initialReadinessExit
  }
  exit 0
}

if ($ApproveCursorCleanup) {
  Write-Section 'Approved Cursor global MCP cleanup'
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $evidenceRoot = Join-Path $RuntimeRoot "backups\cursor-mcp-$stamp"
  Invoke-RepoScript 'ops\bifrost\Invoke-AgentCoreIdeGatewayCutover.ps1' -Parameters @{
    RepoRoot = $RepoRoot
    EvidenceRoot = $evidenceRoot
    Clients = @('cursor')
    CursorConfigPath = $CursorMcpPath
  }
  Invoke-RepoScript 'ops\bifrost\Test-AgentCoreBifrostGateway.ps1'
}

if ($ApproveBifrostRollout) {
  Write-Section 'Approved Bifrost live rollout'
  Invoke-RepoScript 'ops\bifrost\Install-AgentCoreBifrostGateway.ps1' -Parameters @{
    RuntimeRoot = $RuntimeRoot
    RepoRoot = $RepoRoot
  }
  Invoke-RepoScript 'ops\bifrost\Start-AgentCoreBifrostGateway.ps1' -Parameters @{
    RuntimeRoot = $RuntimeRoot
  }
  Invoke-RepoScript 'ops\bifrost\Get-BifrostStatus.ps1'
  Invoke-RepoScript 'ops\bifrost\Test-AgentCoreBifrostGateway.ps1'
}

$finalReadinessExit = Invoke-Readiness
if ($finalReadinessExit -ne 0) {
  exit $finalReadinessExit
}

Write-Host 'AGENTCORE_MORNING_ROLLOUT_READY'
