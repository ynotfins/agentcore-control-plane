<#
.SYNOPSIS
  Stop the AgentCore Bifrost MCP Gateway.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

try {
  Stop-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  Write-Host "[Stop] Stopped scheduled task $TaskPath$TaskName"
} catch {
  Write-Host "[Stop] Scheduled task stop skipped: $($_.Exception.Message)"
}

Get-Process -Name 'bifrost-http' -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Host "[Stop] Stopping bifrost-http PID $($_.Id)"
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $listeners) {
  if ($conn.OwningProcess) {
    try {
      Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
      Write-Host "[Stop] Stopped PID $($conn.OwningProcess) holding port $Port"
    } catch {
      # ignore
    }
  }
}

Write-Host '[Stop] Done'
