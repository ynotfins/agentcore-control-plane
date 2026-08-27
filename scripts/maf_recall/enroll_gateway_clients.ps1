#Requires -Version 5.1
# Enroll agentcore-gateway only (orchestration entrypoint).
[CmdletBinding()]
param(
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [switch]$Apply,
  [switch]$CommitPush
)
$ErrorActionPreference = "Stop"
if ($CommitPush) {
  Set-Location -LiteralPath $RepoRoot
  git add -- "scripts/maf_recall/enroll_gateway_clients.ps1"
  git commit -m "Add MAF Recall realignment package and keep the live gateway frozen."
  if ($LASTEXITCODE -ne 0) { throw "git commit failed with $LASTEXITCODE" }
  git push origin HEAD
  if ($LASTEXITCODE -ne 0) { throw "git push failed with $LASTEXITCODE" }
  git status --short --branch
  git log -1 --oneline
  return
}
$python = Join-Path $RepoRoot "scripts\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
$helper = Join-Path $RepoRoot ".agentcore\scripts\Enroll-GatewayClients.ps1"
if (Test-Path $helper) {
  Write-Host "Delegating to $helper"
  & $helper -RepoRoot $RepoRoot -Apply:$Apply
  return
}
$cherry = Join-Path $RepoRoot "scripts\cherry\enroll_agentcore_gateway.py"
$contract = Join-Path $RepoRoot "contracts\agentcore-gateway-client.json"
if (-not (Test-Path $contract)) { throw "Missing gateway contract: $contract" }
Write-Host "Gateway contract: $contract"
Write-Host "Expected single MCP: agentcore-gateway http://127.0.0.1:8080/mcp"
if (Test-Path $cherry) {
  if ($Apply) { & $python $cherry --apply } else { & $python $cherry --dry-run }
} else {
  Write-Host "Cherry enroll helper not found; contract path validated as present."
}
Write-Host "Reminder: do not add raw Recall MCP, port 65432, or OpenRouter MCP to IDE baselines."
