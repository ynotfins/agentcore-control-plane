#Requires -Version 7.0
<#
.SYNOPSIS
  Rotate oversized Bifrost gateway text logs (keep N compressed/timestamped copies).

.DESCRIPTION
  Renames bifrost-gateway.stdout.log / stderr.log when over MaxBytes, keeping KeepCount archives.
  Safe to run while Bifrost is up (opens files with shared read). Prefer after Stop if rename fails.
#>
[CmdletBinding()]
param(
  [string]$LogDir = 'H:\AgentRuntime\bifrost\logs',
  [long]$MaxBytes = 20MB,
  [int]$KeepCount = 5
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $LogDir)) { throw "LogDir missing: $LogDir" }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
foreach ($name in @('bifrost-gateway.stdout.log', 'bifrost-gateway.stderr.log')) {
  $path = Join-Path $LogDir $name
  if (-not (Test-Path $path)) { continue }
  $item = Get-Item $path
  if ($item.Length -lt $MaxBytes) {
    Write-Host "skip $name size=$($item.Length)"
    continue
  }
  $dest = Join-Path $LogDir ("{0}.{1}.log" -f ($name -replace '\.log$', ''), $stamp)
  try {
    Move-Item -LiteralPath $path -Destination $dest -Force
    New-Item -ItemType File -Path $path -Force | Out-Null
    Write-Host "rotated $name -> $dest"
  } catch {
    # File locked by bifrost-http: copy then truncate in place
    Copy-Item -LiteralPath $path -Destination $dest -Force
    Clear-Content -LiteralPath $path -Force
    Write-Host "copied_and_truncated $name -> $dest (live file locked)"
  }
  Get-ChildItem $LogDir -Filter (($name -replace '\.log$', '') + '.*.log') |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $KeepCount |
    ForEach-Object { Remove-Item $_.FullName -Force; Write-Host "deleted_old $($_.Name)" }
}
Write-Host 'BIFROST_LOG_ROTATION_OK'
