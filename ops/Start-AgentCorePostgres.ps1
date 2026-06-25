param(
  [string]$EngineRoot = "F:\AgentCore\postgres_runtime_engine\pgsql",
  [string]$DataDir = "F:\AgentCore\database_cluster",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$Database = "agent_core",
  [string]$User = "agent_read",
  [switch]$StartIfStopped
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

$checks = [System.Collections.Generic.List[object]]::new()
$pgCtl = Join-Path $EngineRoot "bin\pg_ctl.exe"
$psql = Join-Path $EngineRoot "bin\psql.exe"
$initdb = Join-Path $EngineRoot "bin\initdb.exe"
$logPath = Join-Path $DataDir "server.log"

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

$statusOutput = & $pgCtl -D $DataDir status 2>&1
$running = $LASTEXITCODE -eq 0
Add-Check $checks "server status" $running (($statusOutput -join "`n").Trim())

if (-not $running -and $StartIfStopped) {
  $startOutput = & $pgCtl -D $DataDir -l $logPath start 2>&1
  Add-Check $checks "server start" ($LASTEXITCODE -eq 0) (($startOutput -join "`n").Trim())
  $statusOutput = & $pgCtl -D $DataDir status 2>&1
  $running = $LASTEXITCODE -eq 0
}

if ($running -and (Test-Path -LiteralPath $psql)) {
  $query = "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
  $psqlOutput = & $psql -h $HostName -p $Port -U $User -d $Database -t -A -c $query 2>&1
  Add-Check $checks "pgvector extension" ($LASTEXITCODE -eq 0 -and (($psqlOutput -join "").Trim().Length -gt 0)) (($psqlOutput -join "`n").Trim())

  $countOutput = & $psql -h $HostName -p $Port -U $User -d $Database -t -A -c "SELECT COUNT(*) FROM global_vector_memory_store;" 2>&1
  Add-Check $checks "vector table query" ($LASTEXITCODE -eq 0) (($countOutput -join "`n").Trim())
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
