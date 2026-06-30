param(
  [string]$StateRoot = "F:\AgentCore\agentmemory\projection-state",
  [string]$PsqlPath = "F:\AgentCore\postgres_runtime_engine\pgsql\bin\psql.exe",
  [string]$Database = "agent_core",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$UserName = "agent_read",
  [string]$PasswordEnv = "AGENT_CORE_AGENT_READ_PASSWORD",
  [string]$SwarmRecallConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json",
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

function Get-RequiredEnvValue {
  param([string]$Name)
  foreach ($scope in @("Process", "User", "Machine")) {
    $value = [Environment]::GetEnvironmentVariable($Name, $scope)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      return $value
    }
  }
  throw "Required environment variable not found in Process/User/Machine scope: $Name"
}

function ConvertTo-ProjectionTimestamp {
  param([object]$Value)

  if ($null -eq $Value) {
    return $null
  }

  if ($Value -is [DateTimeOffset]) {
    return $Value.ToString("o")
  }

  if ($Value -is [DateTime]) {
    return ([DateTimeOffset]$Value).ToString("o")
  }

  return ([DateTimeOffset]::Parse([string]$Value, [System.Globalization.CultureInfo]::InvariantCulture)).ToString("o")
}

function Invoke-AgentCoreScalarQuery {
  param(
    [string]$Sql,
    [string]$DbPassword
  )
  $env:PGPASSWORD = $DbPassword
  try {
    $output = & $PsqlPath -h $HostName -p $Port -U $UserName -d $Database -t -A -v ON_ERROR_STOP=1 -c $Sql 2>&1
    if ($LASTEXITCODE -ne 0) {
      throw ($output -join "`n")
    }
    return ($output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1).Trim()
  } finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
  }
}

function Invoke-WithRetry {
  param(
    [scriptblock]$ScriptBlock,
    [int]$MaxAttempts = 5,
    [int]$DelaySeconds = 2
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

$results = [System.Collections.Generic.List[object]]::new()
$summaryPath = Join-Path $StateRoot "summary.json"
$entryRoot = Join-Path $StateRoot "entries"
$config = Get-Content -LiteralPath $SwarmRecallConfigPath -Raw | ConvertFrom-Json
$dbPassword = Get-RequiredEnvValue -Name $PasswordEnv

Add-Result $results "projection state root" (Test-Path -LiteralPath $StateRoot) $StateRoot
Add-Result $results "projection summary" (Test-Path -LiteralPath $summaryPath) $summaryPath
Add-Result $results "projection entries root" (Test-Path -LiteralPath $entryRoot) $entryRoot

$summary = if (Test-Path -LiteralPath $summaryPath) { Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json } else { $null }
$checkpointTimestamp = if ($null -ne $summary) { ConvertTo-ProjectionTimestamp -Value $summary.checkpoint.created_at } else { $null }
if ($null -ne $summary) {
  Add-Result $results "projection checkpoint" (-not [string]::IsNullOrWhiteSpace($checkpointTimestamp)) ("created_at=" + $checkpointTimestamp + "; id=" + [string]$summary.checkpoint.id)
}

$memoryCount = Invoke-AgentCoreScalarQuery -Sql "SELECT COUNT(*) FROM global_vector_memory_store;" -DbPassword $dbPassword
Add-Result $results "canonical memory rows" ([int]$memoryCount -ge 0) $memoryCount

$backlog = if ($null -ne $summary) {
  Invoke-AgentCoreScalarQuery -Sql @"
SELECT COUNT(*)
FROM global_vector_memory_store
WHERE
  (created_at > '$checkpointTimestamp'::timestamptz)
  OR (created_at = '$checkpointTimestamp'::timestamptz AND id::text > '$([string]$summary.checkpoint.id)');
"@ -DbPassword $dbPassword
} else {
  $memoryCount
}
Add-Result $results "projection backlog count" ([int]$backlog -ge 0) $backlog

$apiHealth = (Invoke-WebRequest -UseBasicParsing -Uri ($config.api.url + "/api/v1/health")).Content
Add-Result $results "swarmrecall api health" (($apiHealth | ConvertFrom-Json).status -eq "ok") $apiHealth

$env:SWARMVAULT_OUT = $VaultRoot
$previousNativePref = $PSNativeCommandUseErrorActionPreference
$PSNativeCommandUseErrorActionPreference = $false
try {
  $queryResult = Invoke-WithSwarmVaultMutex {
    Invoke-WithRetry -ScriptBlock { & node "D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js" query --json "What is stored in the shared AgentCore vault?" 2>&1 }
  }
} finally {
  $PSNativeCommandUseErrorActionPreference = $previousNativePref
}
Add-Result $results "swarmvault query" ($queryResult.ExitCode -eq 0) ($queryResult.Output + "`nattempts=" + [string]$queryResult.Attempts)

$entryFiles = @(Get-ChildItem -LiteralPath $entryRoot -Filter *.json -ErrorAction SilentlyContinue)
$projectedEntries = @()
$swarmRecallProjected = 0
$swarmVaultProjected = 0
$swarmVaultSkipped = 0
foreach ($file in $entryFiles) {
  $entry = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
  if ($entry.swarmrecall.status -eq "projected") {
    $swarmRecallProjected++
  }
  if ($entry.swarmvault.status -eq "projected") {
    $swarmVaultProjected++
  }
  if ($entry.swarmvault.status -eq "skipped") {
    $swarmVaultSkipped++
  }
  if ($entry.swarmrecall.status -eq "projected" -and @("projected", "skipped") -contains [string]$entry.swarmvault.status) {
    $projectedEntries += $entry
  }
}
Add-Result $results "projected entries present" ($projectedEntries.Count -gt 0) ($(if ($projectedEntries.Count -gt 0) { $projectedEntries.Count } else { "none" }))
Add-Result $results "swarmrecall projected entries" ($swarmRecallProjected -gt 0) ([string]$swarmRecallProjected)
Add-Result $results "swarmvault curated entries" ($swarmVaultProjected -gt 0) ([string]$swarmVaultProjected)
Add-Result $results "swarmvault skipped entries tracked" ($swarmVaultSkipped -ge 0) ([string]$swarmVaultSkipped)

$rawSourceRoot = Join-Path $VaultRoot "raw\sources"
$wikiSourceRoot = Join-Path $VaultRoot "wiki\sources"
$rawSourceCount = @(Get-ChildItem -LiteralPath $rawSourceRoot -Filter "agentcore-memory-projection-*" -ErrorAction SilentlyContinue).Count
$wikiSourceCount = @(Get-ChildItem -LiteralPath $wikiSourceRoot -Filter "agentcore-memory-projection-*" -ErrorAction SilentlyContinue).Count
Add-Result $results "swarmvault raw source count matches curated entries" ($rawSourceCount -eq $swarmVaultProjected) ("raw=" + [string]$rawSourceCount + "; curated=" + [string]$swarmVaultProjected)
Add-Result $results "swarmvault wiki source count matches curated entries" ($wikiSourceCount -eq $swarmVaultProjected) ("wiki=" + [string]$wikiSourceCount + "; curated=" + [string]$swarmVaultProjected)

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 8
if (-not $allPassed) { exit 1 }
