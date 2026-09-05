#Requires -Version 7.0
<#
.SYNOPSIS
  Stage and smoke-test a Bifrost binary against a copied app directory.

.DESCRIPTION
  This script validates a candidate bifrost-http.exe on a shadow port without
  interrupting the live AgentCore gateway. It copies the runtime config and
  SQLite config store into F:\AgentCore\staging, starts the candidate with the
  copied app-dir, checks /api/version and /health, then stops only the process
  it started.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$SourceExe = "$env:LOCALAPPDATA\bifrost\v2.0.0\bin\bifrost-http.exe-0",
  [string]$StageRoot = '',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 18080,
  [int]$TimeoutSeconds = 45,
  [switch]$LeaveRunning
)

$ErrorActionPreference = 'Stop'

function New-Directory([string]$Path) {
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Copy-IfPresent([string]$Source, [string]$Destination) {
  if (Test-Path -LiteralPath $Source) {
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
  }
}

function Get-BifrostVersionString($Payload) {
  if ($Payload -is [string]) { return $Payload }
  if ($null -eq $Payload) { return $null }
  $property = $Payload.PSObject.Properties['version']
  if ($null -ne $property) { return [string]$property.Value }
  return $null
}

if (-not (Test-Path -LiteralPath $SourceExe)) {
  throw "Candidate Bifrost binary missing: $SourceExe"
}

if ([string]::IsNullOrWhiteSpace($StageRoot)) {
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $StageRoot = "F:\AgentCore\staging\bifrost-shadow-$stamp"
}

$appRoot = Join-Path $StageRoot 'app'
$binDir = Join-Path $appRoot 'bin'
$dataDir = Join-Path $appRoot 'data'
$stateDir = Join-Path $appRoot 'state'
$logDir = Join-Path $appRoot 'logs'
foreach ($path in @($binDir, $dataDir, $stateDir, $logDir)) {
  New-Directory $path
}

$candidateExe = Join-Path $binDir 'bifrost-http.exe'
Copy-Item -LiteralPath $SourceExe -Destination $candidateExe -Force
Copy-Item -LiteralPath (Join-Path $RuntimeRoot 'config.json') -Destination (Join-Path $appRoot 'config.json') -Force
Copy-Item -LiteralPath (Join-Path $RuntimeRoot 'data\config.db') -Destination (Join-Path $dataDir 'config.db') -Force
Copy-IfPresent (Join-Path $RuntimeRoot 'data\config.db-wal') (Join-Path $dataDir 'config.db-wal')
Copy-IfPresent (Join-Path $RuntimeRoot 'data\config.db-shm') (Join-Path $dataDir 'config.db-shm')
Copy-IfPresent (Join-Path $RuntimeRoot 'state\oauth-clients.json') (Join-Path $stateDir 'oauth-clients.json')

$stdoutLog = Join-Path $logDir 'shadow.stdout.log'
$stderrLog = Join-Path $logDir 'shadow.stderr.log'
$process = Start-Process -FilePath $candidateExe `
  -ArgumentList @('-app-dir', $appRoot, '-host', $HostAddress, '-port', [string]$Port, '-log-level', 'info', '-log-style', 'json') `
  -WorkingDirectory $appRoot `
  -RedirectStandardOutput $stdoutLog `
  -RedirectStandardError $stderrLog `
  -PassThru `
  -WindowStyle Hidden

try {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $version = $null
  $versionString = $null
  $healthStatus = $null
  while ((Get-Date) -lt $deadline) {
    if ($process.HasExited) { break }
    try {
      $version = Invoke-RestMethod -Uri "http://${HostAddress}:${Port}/api/version" -TimeoutSec 2 -ErrorAction Stop
      $versionString = Get-BifrostVersionString $version
    } catch {
      $version = $null
      $versionString = $null
    }
    try {
      $health = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
      $healthStatus = $health.StatusCode
    } catch {
      $healthStatus = $null
    }
    if ($versionString -and ($healthStatus -eq 200)) { break }
    Start-Sleep -Seconds 1
  }

  $result = [ordered]@{
    ok = ($versionString -and ($healthStatus -eq 200) -and -not $process.HasExited)
    stage_root = $StageRoot
    pid = $process.Id
    exited = $process.HasExited
    exit_code = if ($process.HasExited) { $process.ExitCode } else { $null }
    version = $versionString
    health_status = $healthStatus
    stdout_log = $stdoutLog
    stdout_length = if (Test-Path -LiteralPath $stdoutLog) { (Get-Item -LiteralPath $stdoutLog).Length } else { $null }
    stderr_tail = if (Test-Path -LiteralPath $stderrLog) { (Get-Content -LiteralPath $stderrLog -Tail 20 -ErrorAction SilentlyContinue) -join "`n" } else { '' }
  }
  $result | ConvertTo-Json -Depth 5
  if (-not $result.ok) { exit 1 }
} finally {
  if ((-not $LeaveRunning) -and (-not $process.HasExited)) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
  }
}
