param(
  [string]$RepoRoot = "D:\github\vendor\swarm\swarmvault",
  [string]$VaultRoot = "F:\AgentCore\agentmemory\swarmvault",
  [int]$CliTimeoutSeconds = 45,
  [int]$QueryTimeoutSeconds = 60,
  [switch]$SkipQuery,
  [switch]$IncludeContextBuild   # context build MUTATES vault state; off by default (native-first, read-only smoke)
)

$ErrorActionPreference = "Stop"

# Native-first, timeout-bounded SwarmVault validator.
# Order: structure -> config -> mcp help -> doctor -> retrieval status -> graph stats -> query (BLOCKED on timeout).
# Read-only by default. Every native CLI call is hard-timeout-bounded and tree-killed on timeout (no infinite retry).

function Invoke-SwarmVaultNative {
  param(
    [string[]]$Arguments,
    [int]$TimeoutSeconds = 45,
    [string]$WorkingDirectory = $VaultRoot,
    [hashtable]$EnvironmentVariables = @{}
  )
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = "node"
  if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) { $psi.WorkingDirectory = $WorkingDirectory }
  if ($psi.ArgumentList) {
    foreach ($argument in $Arguments) { [void]$psi.ArgumentList.Add($argument) }
  } else {
    $psi.Arguments = (($Arguments | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join ' ')
  }
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  foreach ($name in $EnvironmentVariables.Keys) { $psi.Environment[$name] = [string]$EnvironmentVariables[$name] }
  $proc = [System.Diagnostics.Process]::new()
  $proc.StartInfo = $psi
  try {
    $null = $proc.Start()
    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()
    if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
      try { $proc.Kill($true) } catch { try { $proc.Kill() } catch {} }
      return [pscustomobject]@{ ExitCode = 124; TimedOut = $true; Output = "Timed out after $TimeoutSeconds seconds: node $($Arguments -join ' ')" }
    }
    [void]$stdoutTask.Wait(5000); [void]$stderrTask.Wait(5000)
    $output = @($stdoutTask.Result, $stderrTask.Result) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    return [pscustomobject]@{ ExitCode = $proc.ExitCode; TimedOut = $false; Output = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim() }
  } catch {
    return [pscustomobject]@{ ExitCode = 1; TimedOut = $false; Output = $_.Exception.Message }
  }
}

function Invoke-WithSwarmVaultMutex {
  param([scriptblock]$ScriptBlock, [string]$MutexName = "Global\AgentCore.SwarmVault.Validation")
  $mutex = [System.Threading.Mutex]::new($false, $MutexName)
  $lockTaken = $false
  try {
    $lockTaken = $mutex.WaitOne([TimeSpan]::FromMinutes(2))
    if (-not $lockTaken) { throw "Timed out waiting for SwarmVault validation mutex: $MutexName" }
    return & $ScriptBlock
  } finally {
    if ($lockTaken) { $mutex.ReleaseMutex() | Out-Null }
    $mutex.Dispose()
  }
}

$results = [System.Collections.Generic.List[object]]::new()
function Add-Result {
  param([string]$Name, [string]$Status, [string]$Detail)  # Status: PASS | FAIL | BLOCKED | SKIP
  $results.Add([pscustomobject]@{ name = $Name; status = $Status; passed = ($Status -eq "PASS"); detail = $Detail }) | Out-Null
}

$cliPath = Join-Path $RepoRoot "packages\cli\dist\index.js"
$configPath = Join-Path $VaultRoot "swarmvault.config.json"
$schemaPath = Join-Path $VaultRoot "swarmvault.schema.md"
$svEnv = @{ SWARMVAULT_OUT = $VaultRoot }

# --- Structure / config (read-only) ---
Add-Result "source repo" ($(if (Test-Path -LiteralPath $RepoRoot) { "PASS" } else { "FAIL" })) $RepoRoot
Add-Result "built cli" ($(if (Test-Path -LiteralPath $cliPath) { "PASS" } else { "FAIL" })) $cliPath
Add-Result "runtime root" ($(if (Test-Path -LiteralPath $VaultRoot) { "PASS" } else { "FAIL" })) $VaultRoot
foreach ($dirName in @("raw", "wiki", "state", "agent")) {
  $path = Join-Path $VaultRoot $dirName
  Add-Result "dir:$dirName" ($(if (Test-Path -LiteralPath $path) { "PASS" } else { "FAIL" })) $path
}
Add-Result "config file" ($(if (Test-Path -LiteralPath $configPath) { "PASS" } else { "FAIL" })) $configPath
Add-Result "schema file" ($(if (Test-Path -LiteralPath $schemaPath) { "PASS" } else { "FAIL" })) $schemaPath

$envFiles = Get-ChildItem -LiteralPath $VaultRoot -Recurse -Force -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^\.env(\..+)?$' } | Select-Object -ExpandProperty FullName
Add-Result "no env files" ($(if ($envFiles.Count -eq 0) { "PASS" } else { "FAIL" })) ($(if ($envFiles.Count) { $envFiles -join ", " } else { "none found" }))

if (Test-Path -LiteralPath $configPath) {
  $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
  Add-Result "heuristic provider" ($(if ($config.providers.local.type -eq "heuristic") { "PASS" } else { "FAIL" })) ([string]$config.providers.local.type)
  Add-Result "sqlite retrieval" ($(if ($config.retrieval.backend -eq "sqlite") { "PASS" } else { "FAIL" })) ([string]$config.retrieval.backend)
}

# Abort native CLI smokes if the CLI build is missing.
if (-not (Test-Path -LiteralPath $cliPath)) {
  Add-Result "native cli smokes" "FAIL" "CLI build missing; cannot run native smokes"
} else {
  Invoke-WithSwarmVaultMutex {
    # 1. mcp help (cheapest)
    $mcp = Invoke-SwarmVaultNative -Arguments @($cliPath, "mcp", "--help") -TimeoutSeconds $CliTimeoutSeconds -EnvironmentVariables $svEnv
    Add-Result "mcp help" ($(if ($mcp.TimedOut) { "BLOCKED" } elseif ($mcp.ExitCode -eq 0) { "PASS" } else { "FAIL" })) ($mcp.Output)

    # 2. doctor (native health smoke)
    $doctor = Invoke-SwarmVaultNative -Arguments @($cliPath, "doctor", "--json") -TimeoutSeconds $CliTimeoutSeconds -EnvironmentVariables $svEnv
    Add-Result "doctor json" ($(if ($doctor.TimedOut) { "BLOCKED" } elseif ($doctor.ExitCode -eq 0) { "PASS" } else { "FAIL" })) ($doctor.Output)

    # 3. retrieval status (read-only smoke)
    $rstat = Invoke-SwarmVaultNative -Arguments @($cliPath, "retrieval", "status") -TimeoutSeconds $CliTimeoutSeconds -EnvironmentVariables $svEnv
    Add-Result "retrieval status" ($(if ($rstat.TimedOut) { "BLOCKED" } elseif ($rstat.ExitCode -eq 0) { "PASS" } else { "FAIL" })) ($rstat.Output)

    # 4. graph stats (read-only smoke)
    $gstat = Invoke-SwarmVaultNative -Arguments @($cliPath, "graph", "stats") -TimeoutSeconds $CliTimeoutSeconds -EnvironmentVariables $svEnv
    Add-Result "graph stats" ($(if ($gstat.TimedOut) { "BLOCKED" } elseif ($gstat.ExitCode -eq 0) { "PASS" } else { "FAIL" })) ($gstat.Output)

    # 5. query (heavy; single attempt; BLOCKED on timeout, never an infinite retry)
    if ($SkipQuery) {
      Add-Result "query json" "SKIP" "skipped via -SkipQuery"
    } else {
      $q = Invoke-SwarmVaultNative -Arguments @($cliPath, "query", "--json", "What is the current AgentCore SwarmVault status?") -TimeoutSeconds $QueryTimeoutSeconds -EnvironmentVariables $svEnv
      if ($q.TimedOut) {
        Add-Result "query json" "BLOCKED" ("BLOCKED: query exceeded ${QueryTimeoutSeconds}s timeout; process tree killed. Native doctor/status smokes above indicate baseline health. Re-run with a larger -QueryTimeoutSeconds or isolate via 'node `"$cliPath`" doctor --json'.")
      } else {
        Add-Result "query json" ($(if ($q.ExitCode -eq 0) { "PASS" } else { "FAIL" })) ($q.Output)
      }
    }

    # 6. context build MUTATES vault state -> only with explicit approval
    if ($IncludeContextBuild) {
      $ctx = Invoke-SwarmVaultNative -Arguments @($cliPath, "context", "build", "AgentCore SwarmVault status smoke", "--budget", "800") -TimeoutSeconds $QueryTimeoutSeconds -EnvironmentVariables $svEnv
      Add-Result "context build (mutating)" ($(if ($ctx.TimedOut) { "BLOCKED" } elseif ($ctx.ExitCode -eq 0) { "PASS" } else { "FAIL" })) ($ctx.Output)
    } else {
      Add-Result "context build (mutating)" "SKIP" "skipped (mutates vault state); pass -IncludeContextBuild to run with approval"
    }
  }
}

# --- Overall status ---
$results | ConvertTo-Json -Depth 6
$hasFail = @($results | Where-Object { $_.status -eq "FAIL" }).Count -gt 0
$hasBlocked = @($results | Where-Object { $_.status -eq "BLOCKED" }).Count -gt 0
if ($hasFail) { Write-Output "RESULT: FAIL"; exit 1 }
if ($hasBlocked) { Write-Output "RESULT: BLOCKED"; exit 2 }
Write-Output "RESULT: PASS"
exit 0
