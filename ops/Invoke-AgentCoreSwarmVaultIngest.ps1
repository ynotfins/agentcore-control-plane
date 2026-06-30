param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,
  [string]$RepoRoot = "D:\github\vendor\swarm\swarmvault",
  [string]$VaultRoot = "F:\AgentCore\agentmemory\swarmvault",
  [switch]$Compile,
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
if (-not (Test-Path -LiteralPath $InputPath)) {
  throw "SwarmVault ingest input not found: $InputPath"
}

$env:SWARMVAULT_OUT = $VaultRoot
$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path

Push-Location $VaultRoot
try {
  $ingestArgs = @(
    $cliPath,
    "ingest",
    $resolvedInput,
    "--repo-root",
    (Split-Path -Parent $resolvedInput)
  )
  if ($Json) { $ingestArgs += "--json" }
  & node @ingestArgs
  if ($LASTEXITCODE -ne 0) {
    throw "SwarmVault ingest failed."
  }

  if ($Compile) {
    $compileArgs = @($cliPath, "compile")
    if ($Json) { $compileArgs += "--json" }
    & node @compileArgs
    if ($LASTEXITCODE -ne 0) {
      throw "SwarmVault compile failed after ingest."
    }
  }
} finally {
  Pop-Location
}
