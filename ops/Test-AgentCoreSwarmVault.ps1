param(
  [string]$RepoRoot = "D:\github\vendor\swarm\swarmvault",
  [string]$VaultRoot = "F:\AgentCore\agentmemory\swarmvault"
)

$ErrorActionPreference = "Stop"

function Add-Result {
  param(
    [System.Collections.Generic.List[object]]$Results,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail
  )
  $Results.Add([pscustomobject]@{
    name = $Name
    passed = $Passed
    detail = $Detail
  }) | Out-Null
}

$results = [System.Collections.Generic.List[object]]::new()
$cliPath = Join-Path $RepoRoot "packages\cli\dist\index.js"
$configPath = Join-Path $VaultRoot "swarmvault.config.json"
$schemaPath = Join-Path $VaultRoot "swarmvault.schema.md"

Add-Result $results "source repo" (Test-Path -LiteralPath $RepoRoot) $RepoRoot
Add-Result $results "built cli" (Test-Path -LiteralPath $cliPath) $cliPath
Add-Result $results "runtime root" (Test-Path -LiteralPath $VaultRoot) $VaultRoot

foreach ($dirName in @("raw", "wiki", "state", "agent")) {
  $path = Join-Path $VaultRoot $dirName
  Add-Result $results "dir:$dirName" (Test-Path -LiteralPath $path) $path
}

Add-Result $results "config file" (Test-Path -LiteralPath $configPath) $configPath
Add-Result $results "schema file" (Test-Path -LiteralPath $schemaPath) $schemaPath

$envFiles = Get-ChildItem -LiteralPath $VaultRoot -Recurse -Force -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^\.env(\..+)?$' } |
  Select-Object -ExpandProperty FullName
Add-Result $results "no env files" ($envFiles.Count -eq 0) ($(if ($envFiles.Count) { $envFiles -join ", " } else { "none found" }))

if (Test-Path -LiteralPath $configPath) {
  $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
  $heuristicOk = $config.providers.local.type -eq "heuristic"
  $sqliteOk = $config.retrieval.backend -eq "sqlite"
  Add-Result $results "heuristic provider" $heuristicOk $config.providers.local.type
  Add-Result $results "sqlite retrieval" $sqliteOk $config.retrieval.backend
}

$mcpHelp = & node $cliPath mcp --help 2>&1
Add-Result $results "mcp help" ($LASTEXITCODE -eq 0) (($mcpHelp -join "`n").Trim())

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 6
if (-not $allPassed) { exit 1 }
