#Requires -Version 7.0
<#
.SYNOPSIS
  One-command AgentCore foundation health check.

.DESCRIPTION
  Verifies PostgreSQL 18 service/port, Bifrost status (delegates to Get-BifrostStatus.ps1),
  Skills-Hub start script presence, LangGraph Studio env flags, and latest pg18 restore-test artifact.
  Does not reboot the OS. Exit 0 if all critical checks pass.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$fail = 0

function Check([string]$Name, [bool]$Ok, [string]$Detail) {
  $mark = if ($Ok) { 'PASS' } else { 'FAIL' }
  Write-Host ("[{0}] {1}: {2}" -f $mark, $Name, $Detail)
  if (-not $Ok) { $script:fail++ }
}

# PG18
$svc = Get-Service -Name 'AgentCore-PostgreSQL18' -ErrorAction SilentlyContinue
$svcDetail = if ($svc) { "Status=$($svc.Status); StartType=$($svc.StartType)" } else { 'service missing' }
Check 'pg18_service' ($null -ne $svc -and $svc.Status -eq 'Running' -and $svc.StartType -eq 'Automatic') $svcDetail
$pgPort = $false
try {
  $c = New-Object System.Net.Sockets.TcpClient
  $iar = $c.BeginConnect('127.0.0.1', 55433, $null, $null)
  $pgPort = $iar.AsyncWaitHandle.WaitOne(2000, $false) -and $c.Connected
  $c.Close()
} catch { $pgPort = $false }
Check 'pg18_port_55433' $pgPort '127.0.0.1:55433'

# Bifrost
$bifrostStatus = Join-Path $repo 'ops\bifrost\Get-BifrostStatus.ps1'
if (Test-Path $bifrostStatus) {
  & $bifrostStatus
  Check 'bifrost_status_script' ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
} else {
  Check 'bifrost_status_script' $false 'Get-BifrostStatus.ps1 missing'
}

# Skills-Hub
$skillsStart = 'H:\AgentRuntime\skills-hub\start.mjs'
Check 'skills_hub_start_mjs' (Test-Path $skillsStart) $skillsStart

# LangGraph Studio env (User-scope)
$tracing = [Environment]::GetEnvironmentVariable('LANGSMITH_TRACING', 'User')
$noAnalytics = [Environment]::GetEnvironmentVariable('LANGGRAPH_CLI_NO_ANALYTICS', 'User')
Check 'langsmith_tracing_false' ($tracing -eq 'false') "LANGSMITH_TRACING='$tracing' (expect false)"
Check 'langgraph_no_analytics' ($noAnalytics -eq '1') "LANGGRAPH_CLI_NO_ANALYTICS='$noAnalytics' (expect 1)"

# Backup freshness / restore tests
$eBackups = 'E:\DatabaseBackups'
Check 'backup_root_E' (Test-Path $eBackups) $eBackups
$gBackups = 'G:\DatabaseBackups'
if (Test-Path $gBackups) {
  Check 'backup_root_G' $true $gBackups
} else {
  Write-Host '[WARN] backup_root_G: G:\DatabaseBackups missing (second copy not present)'
}
$restore = Get-ChildItem (Join-Path $repo 'audits\M5\pg18-restore-test-*.json') -ErrorAction SilentlyContinue |
  Sort-Object Name -Descending | Select-Object -First 1
Check 'pg18_restore_test_artifact' ($null -ne $restore) $(if ($restore) { $restore.Name } else { 'none' })

# Bifrost log size warning (>50MB)
$stdout = 'H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log'
if (Test-Path $stdout) {
  $len = (Get-Item $stdout).Length
  $ok = $len -lt 50MB
  Check 'bifrost_stdout_log_size' $ok ("bytes=$len threshold=52428800")
}

if ($fail -gt 0) {
  Write-Host "AGENTCORE_HEALTH_FAIL count=$fail"
  exit 1
}
Write-Host 'AGENTCORE_HEALTH_OK'
exit 0
