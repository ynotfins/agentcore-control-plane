<#
.SYNOPSIS
  Health-test the AgentCore Bifrost MCP Gateway without printing secrets.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$CursorMcpPath = 'C:\Users\ynotf\.cursor\mcp.json'
)

$ErrorActionPreference = 'Stop'
$failed = $false

function Assert-True([bool]$Condition, [string]$Label) {
  if ($Condition) {
    Write-Host "PASS  $Label"
  } else {
    Write-Host "FAIL  $Label"
    $script:failed = $true
  }
}

function Invoke-McpJson([string]$Method, [hashtable]$Params, [int]$Id, [hashtable]$Headers) {
  $body = @{
    jsonrpc = '2.0'
    id      = $Id
    method  = $Method
    params  = $Params
  } | ConvertTo-Json -Depth 30 -Compress
  $response = Invoke-WebRequest -Uri "$BaseUrl/mcp" -Method POST -Headers $Headers -Body $body -UseBasicParsing -TimeoutSec 60
  $raw = [string]$response.Content
  $chunks = @()
  foreach ($line in ($raw -split "`n")) {
    if ($line.StartsWith('data: ')) {
      $chunks += $line.Substring(6).Trim()
    }
  }
  if ($chunks.Count -gt 0) {
    return $chunks[-1] | ConvertFrom-Json -Depth 50
  }
  return $raw | ConvertFrom-Json -Depth 50
}

$configPath = Join-Path $RuntimeRoot 'config.json'
Assert-True (Test-Path -LiteralPath $configPath) "config.json exists at $configPath"
Assert-True (Test-Path -LiteralPath (Join-Path $RuntimeRoot 'bin\bifrost-http.exe')) 'bifrost-http.exe present'

if (Test-Path -LiteralPath $configPath) {
  $raw = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8
  Assert-True ($raw -notmatch 'sk-proj-|sk-ant-|ghp_') 'config.json has no obvious secret literals'
  Assert-True ($raw -match 'env\.BIFROST_MCP_VIRTUAL_KEY') 'builder VK uses env.BIFROST_MCP_VIRTUAL_KEY'
  Assert-True ($raw -match '"mcp_disable_auto_tool_inject"\s*:\s*true') 'mcp_disable_auto_tool_inject true'
}

$validate = Join-Path $RepoRoot 'scripts\bifrost\validate_contracts.py'
if (Test-Path -LiteralPath $validate) {
  python $validate | Out-Host
  Assert-True ($LASTEXITCODE -eq 0) 'validate_contracts.py'
}

$listening = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
$netstatListening = $false
try {
  $netstatListening = $null -ne (netstat -ano | Select-String -Pattern '127\.0\.0\.1:8080\s+0\.0\.0\.0:0\s+LISTENING')
} catch {
  $netstatListening = $false
}
Assert-True (($null -ne $listening) -or $netstatListening) 'TCP 127.0.0.1:8080 listening (Get-NetTCPConnection or netstat)'

try {
  $health = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec 5
  Assert-True ($health.StatusCode -ge 200 -and $health.StatusCode -lt 500) "/health HTTP $($health.StatusCode)"
} catch {
  Write-Host "FAIL  /health request: $($_.Exception.Message)"
  $failed = $true
}

# Confirm VK env exists without printing value
$vk = [Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY', 'User')
if (-not $vk) { $vk = [Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY', 'Process') }
Assert-True (-not [string]::IsNullOrWhiteSpace($vk)) 'BIFROST_MCP_VIRTUAL_KEY is set (value not shown)'

if (-not [string]::IsNullOrWhiteSpace($vk)) {
  try {
    $headers = @{
      'x-bf-vk'      = $vk
      'Content-Type' = 'application/json'
      Accept         = 'application/json, text/event-stream'
    }
    $init = Invoke-McpJson -Method 'initialize' -Params @{
      protocolVersion = '2025-06-18'
      capabilities    = @{}
      clientInfo      = @{ name = 'agentcore-gateway-validator'; version = '1.0' }
    } -Id 1001 -Headers $headers
    Assert-True ($null -ne $init.result.serverInfo) 'authenticated MCP initialize'

    try {
      Invoke-WebRequest -Uri "$BaseUrl/mcp" -Method POST -Headers $headers -Body '{"jsonrpc":"2.0","method":"notifications/initialized"}' -UseBasicParsing -TimeoutSec 30 | Out-Null
    } catch {
      # Some streamable HTTP implementations do not require the notification for stateless requests.
    }

    $tools = Invoke-McpJson -Method 'tools/list' -Params @{} -Id 1002 -Headers $headers
    $toolNames = @($tools.result.tools | ForEach-Object { $_.name })
    Assert-True ($toolNames.Count -gt 0) "authenticated MCP tools/list returned $($toolNames.Count) tools"

    foreach ($prefix in @('arabold_docs', 'depwire', 'tentra', 'sequential_thinking', 'context_fabric', 'filesystem', 'playwright', 'cursor_agent_mcp', 'agentcore_memory', 'agentcore_project_router')) {
      Assert-True (@($toolNames | Where-Object { $_ -like "$prefix*" }).Count -gt 0) "expected MCP tool prefix present: $prefix"
    }
    foreach ($pattern in @('swarm', 'postgres', 'psql', 'whole_drive', 'bifrost_admin')) {
      Assert-True (@($toolNames | Where-Object { $_ -match $pattern }).Count -eq 0) "forbidden MCP tool pattern absent: $pattern"
    }
  } catch {
    Write-Host "FAIL  authenticated MCP protocol validation: $($_.Exception.Message)"
    $failed = $true
  }
}

if (Test-Path -LiteralPath $CursorMcpPath) {
  try {
    $cursorRaw = Get-Content -LiteralPath $CursorMcpPath -Raw -Encoding UTF8
    $cursorJson = $cursorRaw | ConvertFrom-Json -Depth 20
    $serverNames = @($cursorJson.mcpServers.PSObject.Properties.Name)
    Assert-True ($serverNames.Count -eq 1) 'Cursor global MCP has exactly one server entry'
    Assert-True ($serverNames -contains 'agentcore-gateway') 'Cursor global MCP contains agentcore-gateway'
    Assert-True ($serverNames -notcontains 'MCP_DOCKER') 'Cursor global MCP does not contain MCP_DOCKER'
    Assert-True ($cursorJson.mcpServers.'agentcore-gateway'.url -eq "$BaseUrl/mcp") 'Cursor global MCP endpoint matches gateway'
    Assert-True ($cursorRaw -match '\$\{env:BIFROST_MCP_VIRTUAL_KEY\}') 'Cursor global MCP uses env placeholder'
    Assert-True ($cursorRaw -notmatch 'sk-[A-Za-z0-9_-]{20,}') 'Cursor global MCP has no obvious secret literal'
  } catch {
    Write-Host "FAIL  Cursor MCP config validation: $($_.Exception.Message)"
    $failed = $true
  }
} else {
  Write-Host "FAIL  Cursor MCP config missing: $CursorMcpPath"
  $failed = $true
}

if ($failed) {
  Write-Host 'RESULT: FAILED'
  exit 1
}
Write-Host 'RESULT: PASSED'
exit 0
