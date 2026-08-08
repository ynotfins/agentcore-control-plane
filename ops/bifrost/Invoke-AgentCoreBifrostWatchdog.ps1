<#
.SYNOPSIS
  Debounced one-minute health watchdog for the AgentCore Bifrost gateway.

.DESCRIPTION
  The watchdog owns recovery decisions only. The gateway task remains the sole
  owner of bifrost-http.exe. A maintenance marker suppresses recovery while an
  operator intentionally stops or starts the gateway.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$GatewayUrl = 'http://127.0.0.1:8080',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [int]$StartupGraceSeconds = 180,
  [int]$FailureThreshold = 3,
  [switch]$TestMode,
  [ValidateSet('Healthy', 'Unhealthy')]
  [string]$TestHealthResult = 'Healthy',
  [string]$GatewayStartedAtUtc = ''
)

$ErrorActionPreference = 'Stop'
$stateDir = Join-Path $RuntimeRoot 'state'
$logDir = Join-Path $RuntimeRoot 'logs'
$statePath = Join-Path $stateDir 'bifrost-watchdog.json'
$maintenanceMarker = Join-Path $stateDir 'bifrost-maintenance.marker'

function Write-WatchdogLog([string]$Message) {
  $line = '[{0}] {1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Message
  Write-Host $line
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  Add-Content -LiteralPath (Join-Path $logDir 'bifrost-watchdog.log') -Value $line -Encoding utf8
}

function Get-WatchdogState {
  if (-not (Test-Path -LiteralPath $statePath)) {
    return [ordered]@{ consecutive_failures = 0; recycle_attempted = $false }
  }
  try {
    $saved = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    return [ordered]@{
      consecutive_failures = [int]$saved.consecutive_failures
      recycle_attempted = [bool]$saved.recycle_attempted
    }
  } catch {
    Write-WatchdogLog 'WATCHDOG_STATE_RESET invalid_state'
    return [ordered]@{ consecutive_failures = 0; recycle_attempted = $false }
  }
}

function Save-WatchdogState([hashtable]$State) {
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

function Invoke-ControlledRecycle([int]$FailureCount) {
  if ($TestMode) {
    Write-WatchdogLog "WATCHDOG_TEST_RECYCLE count=$FailureCount"
    return
  }
  try {
    Stop-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  } catch {
    Write-WatchdogLog "WATCHDOG_RECYCLE_STOP_FAILED count=$FailureCount"
    return
  }
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task -or $task.State -ne 'Running') { break }
    Start-Sleep -Seconds 1
  }
  try {
    Start-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
    Write-WatchdogLog "WATCHDOG_RECYCLE_STARTED count=$FailureCount"
  } catch {
    Write-WatchdogLog "WATCHDOG_RECYCLE_START_FAILED count=$FailureCount"
  }
}

if (Test-Path -LiteralPath $maintenanceMarker) {
  Write-WatchdogLog 'WATCHDOG_SKIP maintenance_marker'
  exit 0
}

$startedAt = Get-GatewayStartedAt
if ($startedAt -and (((Get-Date).ToUniversalTime() - $startedAt).TotalSeconds -lt $StartupGraceSeconds)) {
  Write-WatchdogLog 'WATCHDOG_SKIP startup_grace'
  exit 0
}

$state = Get-WatchdogState
if (Test-GatewayHealth) {
  $state.consecutive_failures = 0
  $state.recycle_attempted = $false
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
  Write-WatchdogLog "WATCHDOG_RECYCLE_SUPPRESSED count=$($state.consecutive_failures)"
  exit 0
}

$state.recycle_attempted = $true
Save-WatchdogState $state
Invoke-ControlledRecycle -FailureCount $state.consecutive_failures
