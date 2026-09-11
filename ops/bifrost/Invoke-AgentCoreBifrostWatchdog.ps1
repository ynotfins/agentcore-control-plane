<#
.SYNOPSIS
  Debounced one-minute health watchdog for the AgentCore Bifrost gateway.

.DESCRIPTION
  The watchdog owns recovery decisions only. The gateway task remains the sole
  owner of bifrost-http.exe. Maintenance markers may briefly suppress recovery
  during Stop/Start handoff, but TTLs are intentionally short so an orphaned
  marker cannot leave agentcore-gateway down. Only an explicit operator_hold
  marker may suppress recovery for the longer hold TTL.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$GatewayUrl = 'http://127.0.0.1:8080',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [int]$StartupGraceSeconds = 120,
  [int]$MaintenanceMarkerTtlSeconds = 900,
  [ValidateRange(30, 900)]
  [int]$StopRequestedMarkerTtlSeconds = 120,
  [ValidateRange(30, 900)]
  [int]$StartRequestedMarkerTtlSeconds = 180,
  [int]$FailureThreshold = 2,
  [ValidateRange(1, 3600)]
  [int]$RecycleRetryBackoffSeconds = 60,
  [switch]$TestMode,
  [ValidateSet('Healthy', 'Unhealthy')]
  [string]$TestHealthResult = 'Healthy',
  [ValidateSet('None', 'BeforeStopMarker', 'BeforeRestartMarker', 'StopFailure', 'StartFailure')]
  [string]$TestRecycleOutcome = 'None',
  [ValidateSet('Running', 'Ready', 'Disabled', 'Unknown')]
  [string]$TestGatewayTaskState = 'Running',
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

function Get-NowEpochSeconds {
  $now = Get-Now
  return ([DateTimeOffset]$now).ToUnixTimeSeconds()
}

function Write-WatchdogLog([string]$Message) {
  $line = '[{0}] {1}' -f (Get-Now).ToString('o'), $Message
  Write-Host $line
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  Add-Content -LiteralPath (Join-Path $logDir 'bifrost-watchdog.log') -Value $line -Encoding utf8
}

function Get-WatchdogState {
  if (-not (Test-Path -LiteralPath $statePath)) {
    return [ordered]@{ consecutive_failures = 0; recycle_attempted = $false; last_recycle_outcome = 'none'; last_recycle_attempt_epoch = 0 }
  }
  try {
    $saved = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    $retryEpoch = 0L
    $retryEpochText = [string]$saved.last_recycle_attempt_epoch
    if (-not [string]::IsNullOrWhiteSpace($retryEpochText) -and
        -not [long]::TryParse($retryEpochText, [ref]$retryEpoch)) {
      Write-WatchdogLog 'WATCHDOG_RECYCLE_STATE_RESET invalid_retry_epoch'
      $retryEpoch = 0L
    }
    return [ordered]@{
      consecutive_failures = [int]$saved.consecutive_failures
      recycle_attempted = [bool]$saved.recycle_attempted
      last_recycle_outcome = [string]$saved.last_recycle_outcome
      last_recycle_attempt_epoch = $retryEpoch
    }
  } catch {
    Write-WatchdogLog 'WATCHDOG_STATE_RESET invalid_state'
    return [ordered]@{ consecutive_failures = 0; recycle_attempted = $false; last_recycle_outcome = 'none'; last_recycle_attempt_epoch = 0 }
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

function Get-MaintenanceMarkerValue {
  if (-not (Test-Path -LiteralPath $maintenanceMarker)) { return '' }
  try {
    return ((Get-Content -LiteralPath $maintenanceMarker -Raw -ErrorAction Stop) ?? '').Trim()
  } catch {
    return ''
  }
}

function Get-MaintenanceMarkerTtlSeconds([string]$MarkerValue) {
  if ([string]::Equals($MarkerValue, 'stop_requested', [System.StringComparison]::OrdinalIgnoreCase)) {
    return [int]$StopRequestedMarkerTtlSeconds
  }
  if ([string]::Equals($MarkerValue, 'start_requested', [System.StringComparison]::OrdinalIgnoreCase)) {
    return [int]$StartRequestedMarkerTtlSeconds
  }
  # Explicit long hold, or legacy free-text markers from older tests/ops.
  return [int]$MaintenanceMarkerTtlSeconds
}

function Test-MaintenanceMarker([string]$Phase) {
  if ($TestMode) {
    return ($TestRecycleOutcome -eq "${Phase}Marker")
  }
  if (-not (Test-Path -LiteralPath $maintenanceMarker)) { return $false }
  $value = Get-MaintenanceMarkerValue
  $ageSeconds = [math]::Floor(((Get-Now) - (Get-Item -LiteralPath $maintenanceMarker).LastWriteTimeUtc).TotalSeconds)
  $ttlSeconds = Get-MaintenanceMarkerTtlSeconds -MarkerValue $value
  return ($ageSeconds -lt $ttlSeconds)
}

function Invoke-ControlledRecycle([int]$FailureCount) {
  if (Test-MaintenanceMarker -Phase 'BeforeStop') {
    Write-WatchdogLog 'WATCHDOG_RECYCLE_SKIPPED maintenance_marker_before_stop'
    return [pscustomobject]@{ success = $true; outcome = 'maintenance_marker_before_stop' }
  }
  $task = if ($TestMode) {
    [pscustomobject]@{ State = $TestGatewayTaskState }
  } else {
    Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
  }
  $taskState = if ($task) { [string]$task.State } else { 'Unknown' }
  if ($taskState -eq 'Running') {
    if ($TestMode -and $TestRecycleOutcome -eq 'StopFailure') {
      Write-WatchdogLog "WATCHDOG_RECYCLE_STOP_FAILED count=$FailureCount"
      return [pscustomobject]@{ success = $false; outcome = 'stop_failed' }
    }
    if (-not $TestMode) {
      try {
        Stop-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
      } catch {
        Write-WatchdogLog "WATCHDOG_RECYCLE_STOP_FAILED count=$FailureCount"
        return [pscustomobject]@{ success = $false; outcome = 'stop_failed' }
      }
    }
  } else {
    Write-WatchdogLog "WATCHDOG_RECYCLE_STOP_SKIPPED task_state=$taskState"
  }
  if (-not $TestMode) {
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
      $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
      if (-not $task -or $task.State -ne 'Running') { break }
      Start-Sleep -Seconds 1
    }
  }
  if (Test-MaintenanceMarker -Phase 'BeforeRestart') {
    Write-WatchdogLog 'WATCHDOG_RECYCLE_SKIPPED maintenance_marker_before_restart'
    return [pscustomobject]@{ success = $true; outcome = 'maintenance_marker_before_restart' }
  }
  if ($TestMode -and $TestRecycleOutcome -eq 'StartFailure') {
    Write-WatchdogLog "WATCHDOG_RECYCLE_START_FAILED count=$FailureCount"
    return [pscustomobject]@{ success = $false; outcome = 'start_failed' }
  }
  if ($TestMode) {
    Write-WatchdogLog "WATCHDOG_TEST_RECYCLE count=$FailureCount"
    return [pscustomobject]@{ success = $true; outcome = 'started' }
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
  $markerValue = Get-MaintenanceMarkerValue
  $ageSeconds = [math]::Floor(((Get-Now) - (Get-Item -LiteralPath $maintenanceMarker).LastWriteTimeUtc).TotalSeconds)
  $ttlSeconds = Get-MaintenanceMarkerTtlSeconds -MarkerValue $markerValue
  if ($ageSeconds -lt $ttlSeconds) {
    Write-WatchdogLog "WATCHDOG_SKIP maintenance_marker value=$markerValue age_seconds=$ageSeconds ttl_seconds=$ttlSeconds"
    exit 0
  }
  Remove-Item -LiteralPath $maintenanceMarker -Force
  Write-WatchdogLog "WATCHDOG_STALE_MARKER_REMOVED value=$markerValue age_seconds=$ageSeconds ttl_seconds=$ttlSeconds"
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
  $state.last_recycle_attempt_epoch = 0
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
  $lastAttemptEpoch = [long]$state.last_recycle_attempt_epoch
  $nowEpoch = Get-NowEpochSeconds
  if ($lastAttemptEpoch -lt 0 -or $lastAttemptEpoch -gt $nowEpoch) {
    Write-WatchdogLog 'WATCHDOG_RECYCLE_STATE_RESET invalid_retry_epoch'
    $lastAttemptEpoch = 0
    $state.last_recycle_attempt_epoch = 0
  }
  $elapsedSeconds = if ($lastAttemptEpoch -gt 0) { $nowEpoch - $lastAttemptEpoch } else { $RecycleRetryBackoffSeconds }
  if ($elapsedSeconds -lt $RecycleRetryBackoffSeconds) {
    $remainingSeconds = [math]::Max(1, $RecycleRetryBackoffSeconds - $elapsedSeconds)
    Write-WatchdogLog "WATCHDOG_RECYCLE_BACKOFF count=$($state.consecutive_failures) outcome=$($state.last_recycle_outcome) remaining_seconds=$remainingSeconds"
    if ($state.last_recycle_outcome -in @('stop_failed', 'start_failed')) { exit 1 }
    exit 0
  }
  Write-WatchdogLog "WATCHDOG_RECYCLE_RETRY count=$($state.consecutive_failures) previous_outcome=$($state.last_recycle_outcome)"
  $state.recycle_attempted = $false
}

$state.recycle_attempted = $true
$state.last_recycle_attempt_epoch = Get-NowEpochSeconds
Save-WatchdogState $state
$result = Invoke-ControlledRecycle -FailureCount $state.consecutive_failures
$state.last_recycle_outcome = $result.outcome
if ($result.outcome -in @('maintenance_marker_before_stop', 'maintenance_marker_before_restart')) {
  $state.recycle_attempted = $false
}
Save-WatchdogState $state
if (-not $result.success) { exit 1 }
