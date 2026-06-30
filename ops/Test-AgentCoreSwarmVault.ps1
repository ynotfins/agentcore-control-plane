param(
  [string]$RepoRoot = "D:\github\vendor\swarm\swarmvault",
  [string]$VaultRoot = "F:\AgentCore\agentmemory\swarmvault"
)

$ErrorActionPreference = "Stop"

function Invoke-WithRetry {
  param(
    [scriptblock]$ScriptBlock,
    [int]$MaxAttempts = 5,
    [int]$DelaySeconds = 2,
    [string]$RetryLabel = "operation"
  )

  $lastOutput = $null
  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $output = & $ScriptBlock
    $exitCode = $LASTEXITCODE
    $text = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    $isTransientLock = $text -match "database is locked" -or $text -match "EPERM: operation not permitted, rename"
    if ($exitCode -eq 0 -or -not $isTransientLock -or $attempt -eq $MaxAttempts) {
      return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $text
        Attempts = $attempt
      }
    }
    Start-Sleep -Seconds $DelaySeconds
    $lastOutput = $text
  }

  return [pscustomobject]@{
    ExitCode = 1
    Output = $lastOutput
    Attempts = $MaxAttempts
  }
}

function Invoke-WithSwarmVaultMutex {
  param(
    [scriptblock]$ScriptBlock,
    [string]$MutexName = "Global\AgentCore.SwarmVault.Validation"
  )

  $mutex = [System.Threading.Mutex]::new($false, $MutexName)
  $lockTaken = $false
  try {
    $lockTaken = $mutex.WaitOne([TimeSpan]::FromMinutes(2))
    if (-not $lockTaken) {
      throw "Timed out waiting for SwarmVault validation mutex: $MutexName"
    }
    return & $ScriptBlock
  } finally {
    if ($lockTaken) {
      $mutex.ReleaseMutex() | Out-Null
    }
    $mutex.Dispose()
  }
}

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

$env:SWARMVAULT_OUT = $VaultRoot
$doctorResult = Invoke-WithSwarmVaultMutex {
  Invoke-WithRetry -RetryLabel "swarmvault doctor" -ScriptBlock { & node $cliPath doctor --json 2>&1 }
}
Add-Result $results "doctor json" ($doctorResult.ExitCode -eq 0) ($doctorResult.Output + "`nattempts=" + [string]$doctorResult.Attempts)

$queryResult = Invoke-WithSwarmVaultMutex {
  Invoke-WithRetry -RetryLabel "swarmvault query" -ScriptBlock { & node $cliPath query --json "What is the current AgentCore SwarmVault status?" 2>&1 }
}
Add-Result $results "query json" ($queryResult.ExitCode -eq 0) ($queryResult.Output + "`nattempts=" + [string]$queryResult.Attempts)

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 6
if (-not $allPassed) { exit 1 }
