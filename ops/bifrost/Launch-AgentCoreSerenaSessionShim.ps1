<#
.SYNOPSIS
  Run the Serena HTTP session shim as the foreground process for the Windows startup owner.

.DESCRIPTION
  Long-running owner process. The scheduled task owns this PowerShell process, which owns
  the Python shim (scripts/bifrost/serena_session_shim.py) on loopback :18090.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\serena-shim',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 18090,
  [string]$PythonExe = '',
  [string]$ShimScript = '',
  [long]$MaxLogBytes = 25MB,
  [int]$InitialRestartBackoffSeconds = 2,
  [int]$MaxRestartBackoffSeconds = 30,
  [int]$MinRunSecondsForBackoffReset = 30,
  [int]$MaintenanceMarkerTtlSeconds = 900
)

$ErrorActionPreference = 'Stop'

function Write-AgentCoreLog([string]$Message) {
  Write-Host ("[{0}] {1}" -f (Get-Date).ToString('o'), $Message)
}

function ConvertTo-AgentCoreCanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
  try { return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/') } catch { return '' }
}

function Resolve-SerenaShimPython([string]$Root, [string]$Override) {
  if (-not [string]::IsNullOrWhiteSpace($Override) -and (Test-Path -LiteralPath $Override -PathType Leaf)) {
    return (ConvertTo-AgentCoreCanonicalPath $Override)
  }
  $venvPython = Join-Path $Root 'scripts\.venv\Scripts\python.exe'
  if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
    return (ConvertTo-AgentCoreCanonicalPath $venvPython)
  }
  throw "Serena shim Python not found under $Root\scripts\.venv\Scripts\python.exe"
}

function Resolve-SerenaShimScript([string]$Root, [string]$Override) {
  if (-not [string]::IsNullOrWhiteSpace($Override) -and (Test-Path -LiteralPath $Override -PathType Leaf)) {
    return (ConvertTo-AgentCoreCanonicalPath $Override)
  }
  $scriptPath = Join-Path $Root 'scripts\bifrost\serena_session_shim.py'
  if (Test-Path -LiteralPath $scriptPath -PathType Leaf) {
    return (ConvertTo-AgentCoreCanonicalPath $scriptPath)
  }
  throw "Serena shim script missing: $scriptPath"
}

function Get-MaintenanceMarkerInfo {
  if (-not (Test-Path -LiteralPath $maintenanceMarker)) {
    return [pscustomobject]@{ Present = $false; Value = ''; AgeSeconds = $null; Active = $false }
  }
  $item = Get-Item -LiteralPath $maintenanceMarker -ErrorAction Stop
  $ageSeconds = [math]::Floor(((Get-Date).ToUniversalTime() - $item.LastWriteTimeUtc).TotalSeconds)
  $value = ''
  try { $value = ((Get-Content -LiteralPath $maintenanceMarker -Raw -ErrorAction Stop) ?? '').Trim() } catch { $value = '' }
  $active = ($ageSeconds -le $MaintenanceMarkerTtlSeconds)
  return [pscustomobject]@{ Present = $true; Value = $value; AgeSeconds = $ageSeconds; Active = $active }
}

function Test-StopMaintenanceMarker {
  $marker = Get-MaintenanceMarkerInfo
  if (-not $marker.Present) { return $false }
  if (-not $marker.Active) {
    Write-AgentCoreLog "Maintenance marker stale; ignoring for launcher age_seconds=$($marker.AgeSeconds)"
    return $false
  }
  # start_requested must NOT suppress launch (Start sets it before the task runs).
  return -not [string]::Equals([string]$marker.Value, 'start_requested', [System.StringComparison]::OrdinalIgnoreCase)
}

function Rotate-AgentCoreLogIfNeeded([string]$LogPath, [long]$MaxBytes) {
  if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf)) { return }
  $item = Get-Item -LiteralPath $LogPath
  if ($item.Length -lt $MaxBytes) { return }
  $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
  $archive = Join-Path $item.DirectoryName ($item.BaseName + ".$stamp.log")
  Move-Item -LiteralPath $LogPath -Destination $archive -Force
}

$RepoRoot = ConvertTo-AgentCoreCanonicalPath $RepoRoot
$RuntimeRoot = ConvertTo-AgentCoreCanonicalPath $RuntimeRoot
$pythonPath = Resolve-SerenaShimPython -Root $RepoRoot -Override $PythonExe
$shimPath = Resolve-SerenaShimScript -Root $RepoRoot -Override $ShimScript
$logsDir = Join-Path $RuntimeRoot 'logs'
$stateDir = Join-Path $RuntimeRoot 'state'
$stdoutLog = Join-Path $logsDir 'serena-shim.stdout.log'
$stderrLog = Join-Path $logsDir 'serena-shim.stderr.log'
$maintenanceMarker = Join-Path $stateDir 'serena-shim-maintenance.marker'

New-Item -ItemType Directory -Force -Path $logsDir, $stateDir | Out-Null
Write-AgentCoreLog "Serena shim launcher starting python=$pythonPath shim=$shimPath host=$HostAddress port=$Port"

$backoff = $InitialRestartBackoffSeconds
while ($true) {
  if (Test-StopMaintenanceMarker) {
    Write-AgentCoreLog 'LAUNCH_SUPPRESSED maintenance_marker'
    Start-Sleep -Seconds 5
    continue
  }

  Rotate-AgentCoreLogIfNeeded -LogPath $stdoutLog -MaxBytes $MaxLogBytes
  Rotate-AgentCoreLogIfNeeded -LogPath $stderrLog -MaxBytes $MaxLogBytes

  $startedAt = Get-Date
  $argList = @(
    '-u',
    $shimPath,
    '--host', $HostAddress,
    '--port', ([string]$Port)
  )
  $process = Start-Process -FilePath $pythonPath -ArgumentList $argList `
    -WorkingDirectory $RuntimeRoot -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
  Write-AgentCoreLog "Started Serena shim PID=$($process.Id)"
  Wait-Process -Id $process.Id
  $exitCode = $process.ExitCode
  $ranSeconds = ((Get-Date) - $startedAt).TotalSeconds
  Write-AgentCoreLog "Serena shim exited code=$exitCode ran_seconds=$([int]$ranSeconds)"

  if (Test-StopMaintenanceMarker) {
    Write-AgentCoreLog "SUPERVISOR_EXIT maintenance_marker code=$exitCode"
    Start-Sleep -Seconds 5
    continue
  }

  if ($ranSeconds -ge $MinRunSecondsForBackoffReset) {
    $backoff = $InitialRestartBackoffSeconds
  }
  Start-Sleep -Seconds $backoff
  $backoff = [Math]::Min($backoff * 2, $MaxRestartBackoffSeconds)
}
