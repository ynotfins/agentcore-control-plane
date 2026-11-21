# Silent watchdog for agent-dispatch. Never opens a window, never steals focus.
# Registered as scheduled task AgentCore-AgentDispatch-Watchdog in the silent shape
# (conhost.exe --headless + pwsh -WindowStyle Hidden + task Hidden), per
# contracts/agentcore-silent-automation-policy.json. Authority: AUTH-2026-11-20-AGENT-DISPATCH-LIVE
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'I:\LocalApps\AgentDispatch',
  [int]$Port = 18092,
  [int]$RestartCooldownMinutes = 5
)
$ErrorActionPreference = 'Stop'
$logDir = Join-Path $RuntimeRoot 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir 'watchdog.log'
function Write-Log([string]$Message) {
  Add-Content -LiteralPath $log -Value ('{0} {1}' -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'), $Message) -Encoding utf8
}
function Test-DispatchHealthy {
  try {
    $r = Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/health" -f $Port) -TimeoutSec 8
    return ($r.status -eq 'healthy')
  } catch { return $false }
}

# Budget failsafe: clear zero-cost unpriced Paperclip usage so the company cannot
# sit budget-paused. Runs every cycle; silent, best-effort, never blocks the check.
try {
  $guard = 'D:\github\agentcore-control-plane\scripts\agent_dispatch\paperclip_guard.py'
  $py = 'D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe'
  if ((Test-Path -LiteralPath $guard) -and (Test-Path -LiteralPath $py)) {
    $out = & $py $guard 2>&1
    Write-Log ("paperclip guard: {0}" -f ($out -join ' '))
  }
} catch {
  Write-Log ("paperclip guard failed: {0}" -f $_.Exception.Message)
}

if (Test-DispatchHealthy) { Write-Log 'ok'; exit 0 }

$stampFile = Join-Path $RuntimeRoot 'watchdog.last-restart'
if (Test-Path -LiteralPath $stampFile) {
  try {
    $last = [datetime]::Parse((Get-Content -LiteralPath $stampFile -Raw).Trim())
    if (((Get-Date) - $last).TotalMinutes -lt $RestartCooldownMinutes) {
      Write-Log ("unhealthy; restart suppressed (cooldown, last {0:o})" -f $last)
      exit 0
    }
  } catch {
    Write-Log 'cooldown stamp unreadable; ignoring it'
  }
}
Write-Log 'unhealthy; restarting'
try {
  & (Join-Path $PSScriptRoot 'Start-AgentCoreAgentDispatch.ps1') -RuntimeRoot $RuntimeRoot -Port $Port *> $null
  Set-Content -LiteralPath $stampFile -Value (Get-Date).ToString('o') -Encoding utf8
  Write-Log 'restart requested'
  exit 0
} catch {
  Set-Content -LiteralPath $stampFile -Value (Get-Date).ToString('o') -Encoding utf8
  Write-Log ("restart failed (cooldown applied): {0}" -f $_.Exception.Message)
  exit 1
}
