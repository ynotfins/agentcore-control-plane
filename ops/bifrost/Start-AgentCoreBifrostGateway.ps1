<#
.SYNOPSIS
  Start the AgentCore Bifrost MCP Gateway process (or scheduled task).
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [switch]$Direct
)

$ErrorActionPreference = 'Stop'
$exePath = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'

if (-not (Test-Path -LiteralPath $exePath)) {
  throw "Missing binary: $exePath"
}

$existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalAddress -in @('127.0.0.1', '::1', '0.0.0.0') }
if ($existing) {
  Write-Host "[Start] Already listening on ${HostAddress}:${Port}"
  return
}

if (-not $Direct) {
  try {
    Start-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
    Start-Sleep -Seconds 2
    Write-Host "[Start] Started scheduled task $TaskPath$TaskName"
    return
  } catch {
    Write-Warning "Scheduled task start failed; falling back to direct launch: $($_.Exception.Message)"
  }
}

$argument = "-app-dir `"$RuntimeRoot`" -host $HostAddress -port $Port -log-level info -log-style json"
Start-Process -FilePath $exePath -ArgumentList $argument -WorkingDirectory $RuntimeRoot -WindowStyle Hidden | Out-Null
Write-Host "[Start] Launched bifrost-http.exe directly"
