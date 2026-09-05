#Requires -Version 7.0
<#
.SYNOPSIS
  Upgrade the live AgentCore Bifrost binary with rollback evidence.

.DESCRIPTION
  Backs up the live binary, config, SQLite config store, and OAuth client state;
  stops only AgentCore-owned Bifrost processes; copies a shadow-validated
  candidate binary into place; rotates oversized gateway text logs; restarts via
  the existing AgentCore scheduled-task starter; verifies version and health;
  then attempts to enable the quiet watchdog task.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$SourceExe = "$env:LOCALAPPDATA\bifrost\v2.0.0\bin\bifrost-http.exe-0",
  [string]$ExpectedVersion = 'v2.0.0',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$WatchdogTaskName = 'AgentCore-Bifrost-Watchdog',
  [string]$TaskPath = '\AgentCore\',
  [switch]$SkipWatchdogEnable
)

$ErrorActionPreference = 'Stop'
$liveExe = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
$backupRoot = Join-Path $RuntimeRoot ("backups\upgrade-$ExpectedVersion-{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

function Copy-IfPresent([string]$Source, [string]$Destination) {
  if (Test-Path -LiteralPath $Source) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
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

function Test-AgentCoreOwnedProcess([int]$ProcessId) {
  try {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
  } catch {
    return $false
  }
  if ($null -eq $process) { return $false }
  $actualExe = [string]$process.ExecutablePath
  $commandLine = [string]$process.CommandLine
  if ((-not [string]::IsNullOrWhiteSpace($actualExe)) -and
      [string]::Equals($actualExe, $liveExe, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $true
  }
  if ((-not [string]::IsNullOrWhiteSpace($commandLine)) -and
      ($commandLine.IndexOf($RuntimeRoot, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)) {
    return $true
  }
  return $false
}

function Stop-LiveGateway {
  try {
    Stop-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  } catch {
    Write-Warning "Scheduled task stop failed or was unnecessary: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 2

  $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  foreach ($listener in $listeners) {
    if (-not $listener.OwningProcess) { continue }
    if (-not (Test-AgentCoreOwnedProcess $listener.OwningProcess)) {
      throw "Refusing upgrade: non-AgentCore process PID=$($listener.OwningProcess) owns port $Port."
    }
  }

  Get-Process -Name bifrost-http -ErrorAction SilentlyContinue | ForEach-Object {
    if (Test-AgentCoreOwnedProcess $_.Id) {
      Stop-Process -Id $_.Id -Force -ErrorAction Stop
    }
  }
  Start-Sleep -Seconds 2
}

function Test-LiveGateway {
  $versionString = $null
  $healthStatus = $null
  for ($i = 0; $i -lt 60; $i++) {
    try {
      $versionString = Get-BifrostVersionString (Invoke-RestMethod -Uri "http://${HostAddress}:${Port}/api/version" -TimeoutSec 2 -ErrorAction Stop)
    } catch {
      $versionString = $null
    }
    try {
      $healthStatus = (Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop).StatusCode
    } catch {
      $healthStatus = $null
    }
    if ($versionString -and ($healthStatus -eq 200)) { break }
    Start-Sleep -Seconds 1
  }
  return [ordered]@{ version = $versionString; health_status = $healthStatus }
}

if (-not (Test-Path -LiteralPath $SourceExe)) { throw "Candidate binary missing: $SourceExe" }
if (-not (Test-Path -LiteralPath $liveExe)) { throw "Live binary missing: $liveExe" }

New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
Copy-IfPresent $liveExe (Join-Path $backupRoot 'bin\bifrost-http.exe')
Copy-IfPresent (Join-Path $RuntimeRoot 'config.json') (Join-Path $backupRoot 'config.json')
Copy-IfPresent (Join-Path $RuntimeRoot 'config\config.json') (Join-Path $backupRoot 'config\config.json')
Copy-IfPresent (Join-Path $RuntimeRoot 'data\config.db') (Join-Path $backupRoot 'data\config.db')
Copy-IfPresent (Join-Path $RuntimeRoot 'data\config.db-wal') (Join-Path $backupRoot 'data\config.db-wal')
Copy-IfPresent (Join-Path $RuntimeRoot 'data\config.db-shm') (Join-Path $backupRoot 'data\config.db-shm')
Copy-IfPresent (Join-Path $RuntimeRoot 'state\oauth-clients.json') (Join-Path $backupRoot 'state\oauth-clients.json')

$beforeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $liveExe).Hash
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SourceExe).Hash

Stop-LiveGateway
Copy-Item -LiteralPath $SourceExe -Destination $liveExe -Force
$afterHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $liveExe).Hash

$rotationScript = Join-Path $PSScriptRoot 'Rotate-BifrostLogs.ps1'
if (Test-Path -LiteralPath $rotationScript) {
  & $rotationScript -LogDir (Join-Path $RuntimeRoot 'logs') -MaxBytes 50MB -KeepCount 0 | Out-Null
}

$startScript = Join-Path $PSScriptRoot 'Start-AgentCoreBifrostGateway.ps1'
& $startScript -RuntimeRoot $RuntimeRoot -TaskName $TaskName -TaskPath $TaskPath -HostAddress $HostAddress -Port $Port
$startExitCode = $LASTEXITCODE
if (($null -ne $startExitCode) -and ($startExitCode -ne 0)) {
  throw "Start script failed with exit $startExitCode"
}

$live = Test-LiveGateway
$watchdog = [ordered]@{ requested = (-not $SkipWatchdogEnable); enabled = $null; error = $null }
if (-not $SkipWatchdogEnable) {
  try {
    Enable-ScheduledTask -TaskPath $TaskPath -TaskName $WatchdogTaskName -ErrorAction Stop | Out-Null
    $watchdog.enabled = $true
  } catch {
    $watchdog.enabled = $false
    $watchdog.error = $_.Exception.Message
  }
}

$tasks = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName, $WatchdogTaskName -ErrorAction SilentlyContinue |
  Select-Object TaskName, State, @{n='Enabled';e={$_.Settings.Enabled}}

$ok = ($afterHash -eq $sourceHash) -and ($live.version -eq $ExpectedVersion) -and ($live.health_status -eq 200) -and ($SkipWatchdogEnable -or $watchdog.enabled)
[ordered]@{
  ok = $ok
  backup_root = $backupRoot
  before_hash = $beforeHash
  source_hash = $sourceHash
  after_hash = $afterHash
  live = $live
  watchdog = $watchdog
  tasks = $tasks
} | ConvertTo-Json -Depth 6

if (-not $ok) { exit 1 }
