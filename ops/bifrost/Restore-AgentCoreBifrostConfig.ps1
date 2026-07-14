<#
.SYNOPSIS
  Restore Bifrost config.json from a backup directory created by Backup-AgentCoreBifrostConfig.ps1.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$BackupDir,
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [switch]$SkipRenderRefresh
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $BackupDir)) {
  throw "Backup directory not found: $BackupDir"
}

$primary = Join-Path $BackupDir 'config.json'
$alt = Join-Path $BackupDir 'config_config.json'

if (-not (Test-Path -LiteralPath $primary)) {
  throw "Backup missing config.json: $BackupDir"
}

# Safety: refuse restore if backup appears to contain secret literals
$raw = Get-Content -LiteralPath $primary -Raw -Encoding UTF8
if ($raw -match 'sk-proj-|sk-ant-|ghp_') {
  throw 'Refusing restore: backup appears to contain secret literals'
}

Copy-Item -LiteralPath $primary -Destination (Join-Path $RuntimeRoot 'config.json') -Force
Write-Host "[Restore] Restored $(Join-Path $RuntimeRoot 'config.json')"

if (Test-Path -LiteralPath $alt) {
  $configDirFile = Join-Path $RuntimeRoot 'config\config.json'
  New-Item -ItemType Directory -Force -Path (Split-Path $configDirFile) | Out-Null
  Copy-Item -LiteralPath $alt -Destination $configDirFile -Force
  Write-Host "[Restore] Restored $configDirFile"
}

if (-not $SkipRenderRefresh) {
  Write-Host '[Restore] Tip: re-run render_bifrost_config.py after contract changes for GitOps alignment.'
}

Write-Host '[Restore] Complete'
