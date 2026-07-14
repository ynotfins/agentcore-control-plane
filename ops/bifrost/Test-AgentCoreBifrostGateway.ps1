<#
.SYNOPSIS
  Health-test the AgentCore Bifrost MCP Gateway without printing secrets.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane'
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
Assert-True ($null -ne $listening) 'TCP 127.0.0.1:8080 listening'

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

if ($failed) {
  Write-Host 'RESULT: FAILED'
  exit 1
}
Write-Host 'RESULT: PASSED'
exit 0
