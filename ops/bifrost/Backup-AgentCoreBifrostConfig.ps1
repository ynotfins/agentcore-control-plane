<#
.SYNOPSIS
  Backup Bifrost runtime config (sanitized check; no secret echo).
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$BackupRoot = 'H:\AgentRuntime\bifrost\backups'
)

$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dest = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null

foreach ($name in @('config.json', 'config\config.json')) {
  $src = Join-Path $RuntimeRoot $name
  if (Test-Path -LiteralPath $src) {
    $target = Join-Path $dest ($name -replace '\\', '_')
    Copy-Item -LiteralPath $src -Destination $target -Force
    Write-Host "[Backup] Copied $src -> $target"
  }
}

# Also snapshot renderer sanitized copy if present
$repoSanitized = 'D:\github\agentcore-control-plane\renderers\bifrost\config.sanitized.json'
if (Test-Path -LiteralPath $repoSanitized) {
  Copy-Item -LiteralPath $repoSanitized -Destination (Join-Path $dest 'config.sanitized.json') -Force
}

Write-Host "[Backup] Complete: $dest"
Write-Output $dest
