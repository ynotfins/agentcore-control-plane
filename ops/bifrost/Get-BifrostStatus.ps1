#Requires -Version 7.0
<#
.SYNOPSIS
  One-command Bifrost gateway status for AgentCore.

.DESCRIPTION
  Checks scheduled-task state, HTTP /health, and key tool-group presence via MCP tools/list.
  Does not print secrets. Exit 0 on healthy, 1 on failure.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$GatewayUrl = 'http://127.0.0.1:8080',
  [string]$TaskPath = '\AgentCore\',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$VirtualKeyEnvName = 'BIFROST_MCP_VIRTUAL_KEY',
  [int]$ExpectedRouterTools = 0,
  [int]$ExpectedMemoryTools = 10,
  [int]$ExpectedSkillsHubMinimum = 3
)

$ErrorActionPreference = 'Stop'
$failures = @()
$maintenanceMarker = Join-Path $RuntimeRoot 'state\bifrost-maintenance.marker'

function Write-Check([string]$Name, [bool]$Ok, [string]$Detail) {
  $mark = if ($Ok) { 'PASS' } else { 'FAIL' }
  Write-Host ("[{0}] {1}: {2}" -f $mark, $Name, $Detail)
  if (-not $Ok) { $script:failures += $Name }
}

Write-Check 'maintenance_marker' $true ("present={0}" -f (Test-Path -LiteralPath $maintenanceMarker))

# Scheduled task
try {
  $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  $info = Get-ScheduledTaskInfo -TaskPath $TaskPath -TaskName $TaskName
  Write-Check 'scheduled_task_state' ($task.State -eq 'Running') ("State=$($task.State); LastResult=$($info.LastTaskResult)")
} catch {
  Write-Check 'scheduled_task_state' $false $_.Exception.Message
}

# Health
try {
  $health = Invoke-RestMethod -Uri "$GatewayUrl/health" -TimeoutSec 5
  Write-Check 'http_health' ($health.status -eq 'ok') ("status=$($health.status)")
} catch {
  Write-Check 'http_health' $false $_.Exception.Message
}

# Tool counts via tools/list (requires the selected virtual-key env in process/User scope)
$vk = [Environment]::GetEnvironmentVariable($VirtualKeyEnvName, 'Process')
if (-not $vk) { $vk = [Environment]::GetEnvironmentVariable($VirtualKeyEnvName, 'User') }
if (-not $vk) {
  Write-Check 'tools_list' $false "$VirtualKeyEnvName missing from process/User env"
} else {
  try {
    $headers = @{
      Authorization  = "Bearer $vk"
      'Content-Type' = 'application/json'
      Accept         = 'application/json, text/event-stream'
    }
    $initBody = @{
      jsonrpc = '2.0'
      id      = 1
      method  = 'initialize'
      params  = @{
        protocolVersion = '2025-06-18'
        capabilities    = @{}
        clientInfo      = @{ name = 'agentcore-bifrost-status'; version = '1.0.0' }
      }
    } | ConvertTo-Json -Depth 6 -Compress
    $sessionHeaders = $headers.Clone()
    $initResp = Invoke-WebRequest -Uri "$GatewayUrl/mcp" -Method POST -Headers $sessionHeaders -Body $initBody -TimeoutSec 30
    $sid = $initResp.Headers['Mcp-Session-Id']
    if ($sid) { $sessionHeaders['Mcp-Session-Id'] = $sid }
    $null = Invoke-WebRequest -Uri "$GatewayUrl/mcp" -Method POST -Headers $sessionHeaders -Body (@{
        jsonrpc = '2.0'; method = 'notifications/initialized'; params = @{}
      } | ConvertTo-Json -Compress) -TimeoutSec 15
    $listBody = @{ jsonrpc = '2.0'; id = 2; method = 'tools/list'; params = @{} } | ConvertTo-Json -Compress
    $listResp = Invoke-RestMethod -Uri "$GatewayUrl/mcp" -Method POST -Headers $sessionHeaders -Body $listBody -TimeoutSec 60
    $tools = @()
    if ($listResp.result.tools) { $tools = @($listResp.result.tools) }
    $mem = @($tools | Where-Object { $_.name -like 'agentcore_memory-*' }).Count
    $router = @($tools | Where-Object { $_.name -like 'agentcore_project_router-*' }).Count
    $skills = @($tools | Where-Object { $_.name -like 'skills_hub-*' }).Count
    Write-Check 'tools_memory_expected' ($mem -eq $ExpectedMemoryTools) "agentcore_memory=$mem expected=$ExpectedMemoryTools profile_env=$VirtualKeyEnvName"
    Write-Check 'tools_router_expected' ($router -eq $ExpectedRouterTools) "agentcore_project_router=$router expected=$ExpectedRouterTools profile_env=$VirtualKeyEnvName"
    Write-Check 'tools_skills_hub_minimum' ($skills -ge $ExpectedSkillsHubMinimum) "skills_hub=$skills expected_min=$ExpectedSkillsHubMinimum profile_env=$VirtualKeyEnvName"
    Write-Host ("tool_total={0}" -f $tools.Count)
  } catch {
    Write-Check 'tools_list' $false $_.Exception.Message
  }
}

if ($failures.Count -gt 0) {
  Write-Host ("BIFROST_STATUS_FAIL count={0} items={1}" -f $failures.Count, ($failures -join ','))
  exit 1
}
Write-Host 'BIFROST_STATUS_OK'
exit 0
