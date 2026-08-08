<#
.SYNOPSIS
  Debounced one-minute health watchdog for the AgentCore Bifrost gateway.

.DESCRIPTION
  The watchdog owns recovery decisions only. The gateway task remains the sole
  owner of bifrost-http.exe. A maintenance marker suppresses recovery while an
  operator intentionally stops or starts the gateway; its bounded TTL prevents
  a failed preflight from suppressing recovery indefinitely.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$GatewayUrl = 'http://127.0.0.1:8080',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [int]$StartupGraceSeconds = 120,
  [int]$MaintenanceMarkerTtlSeconds = 900,
  [int]$FailureThreshold = 3,
  [switch]$TestMode,
  [ValidateSet('Healthy', 'Unhealthy')]
  [string]$TestHealthResult = 'Healthy',
  [ValidateSet('None', 'BeforeStopMarker', 'BeforeRestartMarker', 'StopFailure', 'StartFailure')]
  [string]$TestRecycleOutcome = 'None',
  [string]$GatewayStartedAtUtc = '',
  [string]$NowUtc = ''
)

$ErrorActionPreference = 'Stop'
$stateDir = Join-Path $RuntimeRoot 'state'
$logDir = Join-Path $RuntimeRoot 'logs'
$statePath = Join-Path $stateDir 'bifrost-watchdog.json'
$maintenanceMarker = Join-Path $stateDir 'bifrost-maintenance.marker'

function Get-Now {
  if (-not [string]::IsNullOrWhiteSpace($NowUtc)) {
    return [datetime]::Parse($NowUtc).ToUniversalTime()
  }
  return (Get-Date).ToUniversalTime()
}

function Write-WatchdogLog([string]$Message) {
  $line = '[{0}] {1}' -f (Get-Now).ToString('o'), $Message
  Write-Host $line
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  Add-Content -LiteralPath (Join-Path $logDir 'bifrost-watchdog.log') -Value $line -Encoding utf8
}

function Get-WatchdogState {
  if (-not (Test-Path -LiteralPath $statePath)) {
    return [ordered]@{ consecutive_failures = 0; recycle_attempted = $false; last_recycle_outcome = 'none' }
  }
  try {
    $saved = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    return [ordered]@{
      consecutive_failures = [int]$saved.consecutive_failures
      recycle_attempted = [bool]$saved.recycle_attempted
      last_recycle_outcome = [string]$saved.last_recycle_outcome
    }
  } catch {
    Write-WatchdogLog 'WATCHDOG_STATE_RESET invalid_state'
    return [ordered]@{ consecutive_failures = 0; recycle_attempted = $false; last_recycle_outcome = 'none' }
  }
}

function Save-WatchdogState([System.Collections.IDictionary]$State) {
  New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
  $temporary = Join-Path $stateDir '.bifrost-watchdog.json.tmp'
  $State | ConvertTo-Json -Compress | Set-Content -LiteralPath $temporary -Encoding utf8
  Move-Item -LiteralPath $temporary -Destination $statePath -Force
}

function Get-GatewayStartedAt {
  if (-not [string]::IsNullOrWhiteSpace($GatewayStartedAtUtc)) {
    try { return [datetime]::Parse($GatewayStartedAtUtc).ToUniversalTime() } catch { return $null }
  }
  try {
    return (Get-ScheduledTaskInfo -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop).LastRunTime.ToUniversalTime()
  } catch {
    return $null
  }
}

function Test-GatewayHealth {
  if ($TestMode) { return $TestHealthResult -eq 'Healthy' }
  try {
    $response = Invoke-WebRequest -Uri "$GatewayUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

function Test-MaintenanceMarker([string]$Phase) {
  if ($TestMode) {
    return ($TestRecycleOutcome -eq "${Phase}Marker")
  }
  return Test-Path -LiteralPath $maintenanceMarker
}

function Invoke-ControlledRecycle([int]$FailureCount) {
  if (Test-MaintenanceMarker -Phase 'BeforeStop') {
    Write-WatchdogLog 'WATCHDOG_RECYCLE_SKIPPED maintenance_marker_before_stop'
    return [pscustomobject]@{ success = $true; outcome = 'maintenance_marker_before_stop' }
  }
  if ($TestMode -and $TestRecycleOutcome -eq 'StopFailure') {
    Write-WatchdogLog "WATCHDOG_RECYCLE_STOP_FAILED count=$FailureCount"
    return [pscustomobject]@{ success = $false; outcome = 'stop_failed' }
  }
  if ($TestMode) {
    if ($TestRecycleOutcome -eq 'BeforeRestartMarker') {
      Write-WatchdogLog 'WATCHDOG_RECYCLE_SKIPPED maintenance_marker_before_restart'
      return [pscustomobject]@{ success = $true; outcome = 'maintenance_marker_before_restart' }
    }
    if ($TestRecycleOutcome -eq 'StartFailure') {
      Write-WatchdogLog "WATCHDOG_RECYCLE_START_FAILED count=$FailureCount"
      return [pscustomobject]@{ success = $false; outcome = 'start_failed' }
    }
    Write-WatchdogLog "WATCHDOG_TEST_RECYCLE count=$FailureCount"
    return [pscustomobject]@{ success = $true; outcome = 'started' }
  }
  try {
    Stop-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  } catch {
    Write-WatchdogLog "WATCHDOG_RECYCLE_STOP_FAILED count=$FailureCount"
    return [pscustomobject]@{ success = $false; outcome = 'stop_failed' }
  }
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task -or $task.State -ne 'Running') { break }
    Start-Sleep -Seconds 1
  }
  if (Test-MaintenanceMarker -Phase 'BeforeRestart') {
    Write-WatchdogLog 'WATCHDOG_RECYCLE_SKIPPED maintenance_marker_before_restart'
    return [pscustomobject]@{ success = $true; outcome = 'maintenance_marker_before_restart' }
  }
  if ($TestMode -and $TestRecycleOutcome -eq 'StartFailure') {
    Write-WatchdogLog "WATCHDOG_RECYCLE_START_FAILED count=$FailureCount"
    return [pscustomobject]@{ success = $false; outcome = 'start_failed' }
  }
  try {
    Start-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
    Write-WatchdogLog "WATCHDOG_RECYCLE_STARTED count=$FailureCount"
    return [pscustomobject]@{ success = $true; outcome = 'started' }
  } catch {
    Write-WatchdogLog "WATCHDOG_RECYCLE_START_FAILED count=$FailureCount"
    return [pscustomobject]@{ success = $false; outcome = 'start_failed' }
  }
}

if (Test-Path -LiteralPath $maintenanceMarker) {
  $ageSeconds = [math]::Floor(((Get-Now) - (Get-Item -LiteralPath $maintenanceMarker).LastWriteTimeUtc).TotalSeconds)
  if ($ageSeconds -lt $MaintenanceMarkerTtlSeconds) {
    Write-WatchdogLog "WATCHDOG_SKIP maintenance_marker age_seconds=$ageSeconds"
    exit 0
  }
  Remove-Item -LiteralPath $maintenanceMarker -Force
  Write-WatchdogLog "WATCHDOG_STALE_MARKER_REMOVED age_seconds=$ageSeconds"
}

$startedAt = Get-GatewayStartedAt
if ($startedAt -and (((Get-Now) - $startedAt).TotalSeconds -lt $StartupGraceSeconds)) {
  Write-WatchdogLog 'WATCHDOG_SKIP startup_grace'
  exit 0
}

$state = Get-WatchdogState
if (Test-GatewayHealth) {
  $state.consecutive_failures = 0
  $state.recycle_attempted = $false
  $state.last_recycle_outcome = 'healthy'
  Save-WatchdogState $state
  Write-WatchdogLog 'WATCHDOG_HEALTHY'
  exit 0
}

$state.consecutive_failures = [int]$state.consecutive_failures + 1
Save-WatchdogState $state
if ($state.consecutive_failures -lt $FailureThreshold) {
  Write-WatchdogLog "WATCHDOG_FAILURE count=$($state.consecutive_failures)"
  exit 0
}
if ($state.recycle_attempted) {
  Write-WatchdogLog "WATCHDOG_RECYCLE_SUPPRESSED count=$($state.consecutive_failures) outcome=$($state.last_recycle_outcome)"
  exit 0
}

$state.recycle_attempted = $true
Save-WatchdogState $state
$result = Invoke-ControlledRecycle -FailureCount $state.consecutive_failures
$state.last_recycle_outcome = $result.outcome
Save-WatchdogState $state
if (-not $result.success) { exit 1 }
