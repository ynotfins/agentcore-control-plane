#Requires -Version 5.1
# Docker/WSL placement checks: expect engine data under F:\Docker\wsl
[CmdletBinding()]
param(
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [string]$ExpectedDockerRoot = "F:\Docker\wsl",
  [string]$OutJson = ""
)
$ErrorActionPreference = "Stop"
$helper = Join-Path $RepoRoot ".agentcore\scripts\Docker-Tune.ps1"
if (Test-Path $helper) {
  Write-Host "Delegating to $helper"
  & $helper -ExpectedDockerRoot $ExpectedDockerRoot
  return
}
$checks = @()
function Add-Check([string]$Name, [bool]$Ok, [string]$Detail) {
  $script:checks += [pscustomobject]@{ name = $Name; ok = $Ok; detail = $Detail }
}
Add-Check "expected_root_string" $true $ExpectedDockerRoot
Add-Check "expected_root_exists" (Test-Path -LiteralPath $ExpectedDockerRoot) $ExpectedDockerRoot
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
Add-Check "docker_cli_present" ([bool]$dockerCmd) ($(if ($dockerCmd) { $dockerCmd.Source } else { "docker not on PATH" }))
if ($dockerCmd) {
  try {
    $info = docker info | Out-String
    $onF = ($info -match "F:[\\/]Docker")
    Add-Check "docker_info_mentions_F_Docker" ([bool]$onF) "parsed docker info"
  } catch {
    Add-Check "docker_info" $false $_.Exception.Message
  }
}
$wsl = Get-Command wsl -ErrorAction SilentlyContinue
if ($wsl) {
  try {
    $null = wsl -l -v
    Add-Check "wsl_list" $true "wsl -l -v ok"
  } catch {
    Add-Check "wsl_list" $false $_.Exception.Message
  }
} else {
  Add-Check "wsl_cli" $false "wsl not on PATH"
}
foreach ($bad in @("C:\Docker", "D:\Docker")) {
  Add-Check ("avoid_" + $bad.Replace("\","_")) (-not (Test-Path -LiteralPath $bad)) "should not be primary engine root"
}
$result = [pscustomobject]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  expected_docker_root = $ExpectedDockerRoot
  app_bind_root = "I:\LocalApps"
  checks = $checks
}
if (-not $OutJson) { $OutJson = Join-Path $RepoRoot "audits\maf_recall_docker_tune_latest.json" }
[System.IO.File]::WriteAllText($OutJson, ($result | ConvertTo-Json -Depth 6))
Write-Host "Wrote: $OutJson"
