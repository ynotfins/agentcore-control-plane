<#
.SYNOPSIS
  Start the AgentCore Bifrost MCP Gateway process (or scheduled task).
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [switch]$Direct
)

$ErrorActionPreference = 'Stop'
$exePath = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
$maintenanceMarker = Join-Path $RuntimeRoot 'state\bifrost-maintenance.marker'

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $maintenanceMarker) | Out-Null
Set-Content -LiteralPath $maintenanceMarker -Value 'start_requested' -Encoding utf8

function Wait-ForGatewayHealth {
  param([switch]$CheckScheduledTask)

  for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 2
    try {
      $health = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/health" -UseBasicParsing -TimeoutSec 3
      if ($health.StatusCode -eq 200) {
        Remove-Item -LiteralPath $maintenanceMarker -Force -ErrorAction SilentlyContinue
        Write-Host "[Start] Healthy on ${HostAddress}:${Port}"
        return
      }
    } catch {
      # keep waiting
    }
    if ($CheckScheduledTask) {
      $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
      if ($task -and $task.State -notin @('Running', 'Ready')) {
        $info = Get-ScheduledTaskInfo -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
        throw "Scheduled task entered state $($task.State); last result $($info.LastTaskResult)"
      }
    }
  }
  throw "Gateway did not make Bifrost healthy on ${HostAddress}:${Port}"
}

if (-not (Test-Path -LiteralPath $exePath)) {
  throw "Missing binary: $exePath"
}

$existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalAddress -in @('127.0.0.1', '::1', '0.0.0.0') }
if ($existing) {
  Write-Host "[Start] Already listening on ${HostAddress}:${Port}"
  Remove-Item -LiteralPath $maintenanceMarker -Force -ErrorAction SilentlyContinue
  return
}

if (-not $Direct) {
  Start-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  Write-Host "[Start] Started scheduled task $TaskPath$TaskName"
  Wait-ForGatewayHealth -CheckScheduledTask
  return
}

$launchScript = Join-Path $PSScriptRoot 'Launch-AgentCoreBifrostGateway.ps1'
Start-Process -FilePath 'pwsh.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launchScript, '-RuntimeRoot', $RuntimeRoot, '-HostAddress', $HostAddress, '-Port', [string]$Port) -WorkingDirectory $RuntimeRoot -WindowStyle Hidden | Out-Null
Write-Host "[Start] Launched Bifrost via foreground launcher directly"
Wait-ForGatewayHealth
