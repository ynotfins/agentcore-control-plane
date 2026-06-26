param(
  [ValidateSet("Version", "Init", "Next", "Doctor", "Mcp")]
  [string]$Mode = "Version",
  [string]$RepoRoot = "D:\github\vendor\swarm\swarmvault",
  [string]$VaultRoot = "F:\AgentCore\agentmemory\swarmvault",
  [switch]$Json
)

$ErrorActionPreference = "Stop"

$cliPath = Join-Path $RepoRoot "packages\cli\dist\index.js"
if (-not (Test-Path -LiteralPath $RepoRoot)) {
  throw "SwarmVault source repo not found: $RepoRoot"
}
if (-not (Test-Path -LiteralPath $cliPath)) {
  throw "SwarmVault CLI build output not found: $cliPath"
}
if (-not (Test-Path -LiteralPath $VaultRoot)) {
  throw "SwarmVault runtime root not found: $VaultRoot"
}

$env:SWARMVAULT_OUT = $VaultRoot
$cliArgs = @($cliPath)

switch ($Mode) {
  "Version" { $cliArgs += "--version" }
  "Init" {
    $cliArgs += "init"
    if ($Json) { $cliArgs += "--json" }
  }
  "Next" {
    $cliArgs += "next"
    if ($Json) { $cliArgs += "--json" }
  }
  "Doctor" {
    $cliArgs += "doctor"
    if ($Json) { $cliArgs += "--json" }
  }
  "Mcp" {
    $cliArgs += "mcp"
    if ($Json) { $cliArgs += "--json" }
  }
}

Push-Location $VaultRoot
try {
  & node @cliArgs
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
