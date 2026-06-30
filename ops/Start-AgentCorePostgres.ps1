param(
  [string]$EngineRoot = "F:\AgentCore\postgres_runtime_engine\pgsql",
  [string]$DataDir = "F:\AgentCore\database_cluster",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$Database = "agent_core",
  [string]$User = "agent_read",
  [switch]$StartIfStopped,
  [int]$ReadyTimeoutSeconds = 150
)

$ErrorActionPreference = "Stop"

function Add-Check {
  param(
    [System.Collections.Generic.List[object]]$Checks,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail
  )
  $Checks.Add([pscustomobject]@{
    name = $Name
    passed = $Passed
    detail = $Detail
  }) | Out-Null
}

function Invoke-AgentCoreNative {
  param(
    [string]$Command,
    [string[]]$Arguments
  )

  $previousNativePref = $null
  $hadNativePref = Test-Path Variable:PSNativeCommandUseErrorActionPreference
  if ($hadNativePref) {
    $previousNativePref = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
  }
  try {
    $output = & $Command @Arguments 2>&1
    return [pscustomobject]@{
      ExitCode = $LASTEXITCODE
      Output = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
  } catch {
    return [pscustomobject]@{
      ExitCode = 1
      Output = $_.Exception.Message
    }
  } finally {
    if ($hadNativePref) {
      $PSNativeCommandUseErrorActionPreference = $previousNativePref
    }
  }
}

$checks = [System.Collections.Generic.List[object]]::new()
$pgCtl = Join-Path $EngineRoot "bin\pg_ctl.exe"
$psql = Join-Path $EngineRoot "bin\psql.exe"
$initdb = Join-Path $EngineRoot "bin\initdb.exe"
$pgIsReady = Join-Path $EngineRoot "bin\pg_isready.exe"
$startupLogDir = Join-Path $DataDir "startup-logs"
if (-not (Test-Path -LiteralPath $startupLogDir)) {
  New-Item -ItemType Directory -Path $startupLogDir -Force | Out-Null
}
$logPath = Join-Path $startupLogDir ("pg-startup-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

function Test-AgentCoreTcpPort {
  param(
    [string]$Address,
    [int]$PortNumber
  )
  $client = [Net.Sockets.TcpClient]::new()
  try {
    $iar = $client.BeginConnect($Address, $PortNumber, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(750, $false)
    if ($ok) {
      $client.EndConnect($iar)
    }
    return [bool]$ok
  } catch {
    return $false
  } finally {
    $client.Close()
  }
}

function Move-AgentCoreStalePostmasterPid {
  param(
    [string]$ClusterDir,
    [string]$ExpectedHost,
    [int]$ExpectedPort,
    [System.Collections.Generic.List[object]]$Checks
  )

  $pidPath = Join-Path $ClusterDir "postmaster.pid"
  if (-not (Test-Path -LiteralPath $pidPath)) {
    return
  }

  $resolvedCluster = (Resolve-Path -LiteralPath $ClusterDir).Path.TrimEnd("\")
  $resolvedPid = (Resolve-Path -LiteralPath $pidPath).Path
  if (-not $resolvedPid.StartsWith($resolvedCluster, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to inspect PostgreSQL pid file outside cluster directory: $resolvedPid"
  }

  $pidLine = (Get-Content -LiteralPath $pidPath -TotalCount 1 -ErrorAction Stop)
  $pidValue = 0
  [void][int]::TryParse($pidLine, [ref]$pidValue)
  $processAlive = $false
  if ($pidValue -gt 0) {
    $processAlive = [bool](Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
  }
  $portAlive = Test-AgentCoreTcpPort -Address $ExpectedHost -PortNumber $ExpectedPort

  if (-not $processAlive -and -not $portAlive) {
    $stalePath = Join-Path $ClusterDir ("postmaster.pid.stale-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    Move-Item -LiteralPath $pidPath -Destination $stalePath -Force
    Add-Check $Checks "stale postmaster.pid moved" $true $stalePath
  } else {
    Add-Check $Checks "postmaster.pid active" $true "pid=$pidValue processAlive=$processAlive portAlive=$portAlive"
  }
}

if (-not $env:PGPASSWORD) {
  if ($User -eq "agent_read") {
    $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_READ_PASSWORD", "User")
  } elseif ($User -eq "agent_ingest") {
    $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_INGEST_PASSWORD", "User")
  } elseif ($User -eq "agent_admin") {
    $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_ADMIN_PASSWORD", "User")
  } elseif ($User -eq "postgres") {
    $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
  }
}
if (-not $env:PGSSLMODE) {
  $env:PGSSLMODE = "require"
}

Add-Check $checks "engine root" (Test-Path -LiteralPath $EngineRoot) $EngineRoot
Add-Check $checks "pg_ctl" (Test-Path -LiteralPath $pgCtl) $pgCtl
Add-Check $checks "psql" (Test-Path -LiteralPath $psql) $psql
Add-Check $checks "initdb" (Test-Path -LiteralPath $initdb) $initdb
Add-Check $checks "pg_isready" (Test-Path -LiteralPath $pgIsReady) $pgIsReady
Add-Check $checks "data directory" (Test-Path -LiteralPath $DataDir) $DataDir

if (-not (Test-Path -LiteralPath $pgCtl)) {
  $report = [pscustomobject]@{
    ok = $false
    hint = "PostgreSQL engine was not found. Keep or restore drive letter F:, or pass -EngineRoot X:\AgentCore\postgres_runtime_engine\pgsql."
    checks = $checks
  }
  $report | ConvertTo-Json -Depth 6
  exit 2
}

$statusOutput = Invoke-AgentCoreNative -Command $pgCtl -Arguments @("-D", $DataDir, "status")
$running = $statusOutput.ExitCode -eq 0
Add-Check $checks "server status before start" $true $statusOutput.Output

if (-not $running -and $StartIfStopped) {
  Move-AgentCoreStalePostmasterPid -ClusterDir $DataDir -ExpectedHost $HostName -ExpectedPort $Port -Checks $checks
  $startOutput = Invoke-AgentCoreNative -Command $pgCtl -Arguments @("-D", $DataDir, "-l", $logPath, "start")
  Add-Check $checks "server start" ($startOutput.ExitCode -eq 0) $startOutput.Output
  $statusOutput = Invoke-AgentCoreNative -Command $pgCtl -Arguments @("-D", $DataDir, "status")
  $running = $statusOutput.ExitCode -eq 0
}

if ($running -and (Test-Path -LiteralPath $pgIsReady)) {
  $deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
  do {
    $readyOutput = Invoke-AgentCoreNative -Command $pgIsReady -Arguments @("-h", $HostName, "-p", [string]$Port)
    $ready = $readyOutput.ExitCode -eq 0
    if ($ready) { break }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)
  Add-Check $checks "postgres readiness" $ready $readyOutput.Output
}

Add-Check $checks "server running" $running $statusOutput.Output

if ($running -and (Test-Path -LiteralPath $psql)) {
  $query = "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
  $psqlOutput = Invoke-AgentCoreNative -Command $psql -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $User, "-d", $Database, "-t", "-A", "-c", $query)
  Add-Check $checks "pgvector extension" ($psqlOutput.ExitCode -eq 0 -and $psqlOutput.Output.Length -gt 0) $psqlOutput.Output

  $countOutput = Invoke-AgentCoreNative -Command $psql -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $User, "-d", $Database, "-t", "-A", "-c", "SELECT COUNT(*) FROM global_vector_memory_store;")
  Add-Check $checks "vector table query" ($countOutput.ExitCode -eq 0) $countOutput.Output
}

$failed = @($checks | Where-Object { -not $_.passed })
$result = [pscustomobject]@{
  ok = $failed.Count -eq 0
  engine_root = $EngineRoot
  data_dir = $DataDir
  database = "$HostName`:$Port/$Database"
  start_if_stopped = [bool]$StartIfStopped
  checks = $checks
}

$result | ConvertTo-Json -Depth 6
if ($failed.Count -gt 0) { exit 1 }
