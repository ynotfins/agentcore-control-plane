#Requires -Version 5.1
# Inventory IDE MCP configs vs common_mcp_policy.yaml (orchestration entrypoint).
[CmdletBinding()]
param(
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [string]$OutJson = ""
)
$ErrorActionPreference = "Stop"
$policy = Join-Path $RepoRoot "scripts\maf_recall\common_mcp_policy.yaml"
$expectedUrl = "http://127.0.0.1:8080/mcp"
$expectedName = "agentcore-gateway"
$candidates = @(
  (Join-Path $env:USERPROFILE ".cursor\mcp.json"),
  (Join-Path $env:USERPROFILE ".claude\mcp.json"),
  (Join-Path $env:APPDATA "Claude\claude_desktop_config.json"),
  (Join-Path $RepoRoot ".cursor\mcp.json")
)
$helper = Join-Path $RepoRoot ".agentcore\scripts\Inventory-IdeMcp.ps1"
if (Test-Path $helper) {
  Write-Host "Delegating to $helper"
  & $helper -RepoRoot $RepoRoot
  return
}
$findings = @()
foreach ($path in $candidates) {
  $exists = Test-Path -LiteralPath $path
  $row = [ordered]@{ path = $path; exists = $exists; has_expected_gateway_url = $false; suspicious_patterns = @() }
  if ($exists) {
    $raw = [System.IO.File]::ReadAllText($path)
    if ($raw -match [regex]::Escape($expectedUrl)) { $row.has_expected_gateway_url = $true }
    foreach ($pat in @("65432", "openrouter.ai/mcp", "swarmrecall", "localhost:5432/agent_memory")) {
      if ($raw -match [regex]::Escape($pat)) { $row.suspicious_patterns += $pat }
    }
    if ($raw -match "BIFROST_MCP_VIRTUAL_KEY") { $row.auth_env_ref = $true }
  }
  $findings += [pscustomobject]$row
}
$result = [pscustomobject]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  policy = $policy
  expected_name = $expectedName
  expected_url = $expectedUrl
  findings = $findings
}
if (-not $OutJson) { $OutJson = Join-Path $RepoRoot "audits\maf_recall_ide_mcp_inventory_latest.json" }
[System.IO.File]::WriteAllText($OutJson, ($result | ConvertTo-Json -Depth 6))
Write-Host "Wrote inventory: $OutJson"
