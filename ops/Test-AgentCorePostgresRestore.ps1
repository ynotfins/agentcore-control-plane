param(
  [string]$PgRoot = "F:\PostgreSQL18",
  [string]$BackupRoot = "E:\AgentCoreArchive\agentcore-memory\backups\pg18",
  [string]$RestoreRoot = "I:\AgentCoreRestoreTests\pg18",
  [int]$RestorePort = 55439,
  [string[]]$Databases = @("agent_core", "cognee_core"),
  [string]$EvidenceDir = "audits\M5"
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-NativeChecked {
  param(
    [string]$Command,
    [string[]]$Arguments,
    [string]$FailureMessage,
    [switch]$AllowErrors
  )
  $output = & $Command @Arguments 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0 -and -not $AllowErrors) {
    throw "$FailureMessage (exit $code): $($output -join "`n")"
  }
  return [pscustomobject]@{
    exit_code = $code
    output = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
  }
}

function Invoke-PgCtlChecked {
  param(
    [string[]]$Arguments,
    [string]$FailureMessage,
    [switch]$AllowErrors
  )
  $stdout = Join-Path $env:TEMP ("agentcore-pgctl-out-{0}.log" -f ([guid]::NewGuid().ToString("N")))
  $stderr = Join-Path $env:TEMP ("agentcore-pgctl-err-{0}.log" -f ([guid]::NewGuid().ToString("N")))
  $proc = Start-Process -FilePath $pgCtl -ArgumentList $Arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $output = @()
  if (Test-Path -LiteralPath $stdout) { $output += Get-Content -LiteralPath $stdout -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $stderr) { $output += Get-Content -LiteralPath $stderr -ErrorAction SilentlyContinue }
  Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
  if ($proc.ExitCode -ne 0 -and -not $AllowErrors) {
    throw "$FailureMessage (exit $($proc.ExitCode)): $($output -join "`n")"
  }
  return (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Start-RestoreCluster {
  $arguments = @("-D", $dataDir, "-l", $logPath, "-o", "`"-h 127.0.0.1 -p $RestorePort`"", "start")
  Start-Process -FilePath $pgCtl -ArgumentList $arguments -NoNewWindow | Out-Null
  $deadline = (Get-Date).AddSeconds(45)
  do {
    Start-Sleep -Seconds 1
    $ready = & $pgIsReady -h 127.0.0.1 -p $RestorePort -d postgres 2>&1
    if ($LASTEXITCODE -eq 0) { return }
  } while ((Get-Date) -lt $deadline)
  throw "restore cluster did not become ready: $($ready -join "`n")"
}

function Invoke-Psql {
  param([string]$Sql, [string]$Db = "postgres", [switch]$TupleOnly)
  $psqlArgs = @("-h", "127.0.0.1", "-p", [string]$RestorePort, "-U", "postgres", "-d", $Db, "-v", "ON_ERROR_STOP=1", "-c", $Sql)
  if ($TupleOnly) { $psqlArgs = @("-t", "-A") + $psqlArgs }
  $result = Invoke-NativeChecked -Command $psql -Arguments $psqlArgs -FailureMessage "psql failed"
  return $result.output.Trim()
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$evidencePath = Join-Path $repoRoot $EvidenceDir
New-Item -ItemType Directory -Path $evidencePath -Force | Out-Null

$pgBin = Join-Path $PgRoot "bin"
$initdb = Join-Path $pgBin "initdb.exe"
$pgCtl = Join-Path $pgBin "pg_ctl.exe"
$psql = Join-Path $pgBin "psql.exe"
$createdb = Join-Path $pgBin "createdb.exe"
$pgRestore = Join-Path $pgBin "pg_restore.exe"
$pgIsReady = Join-Path $pgBin "pg_isready.exe"

foreach ($required in @($initdb, $pgCtl, $psql, $createdb, $pgRestore, $pgIsReady)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Required PostgreSQL executable missing: $required" }
}

$latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "backup-manifest.json") } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
if (-not $latest) { throw "No PG18 backup manifest directory found under $BackupRoot" }

$manifestPath = Join-Path $latest.FullName "backup-manifest.json"
$logicalRoot = Join-Path $latest.FullName "logical"
$globalsPath = Join-Path $logicalRoot "globals-no-role-passwords.sql"
if (-not (Test-Path -LiteralPath $globalsPath)) { throw "Globals dump missing: $globalsPath" }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runRoot = Join-Path $RestoreRoot $stamp
$dataDir = Join-Path $runRoot "data"
$logPath = Join-Path $runRoot "restore-postgres.log"
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null

$started = $false
try {
  Invoke-NativeChecked -Command $initdb -Arguments @("-D", $dataDir, "-U", "postgres", "-A", "trust", "--encoding=UTF8", "--locale=C") -FailureMessage "initdb failed" | Out-Null
  Start-RestoreCluster
  $started = $true

  $roleSql = @"
DO `$`$
DECLARE role_name text;
BEGIN
  FOREACH role_name IN ARRAY ARRAY['agentcore_read','agentcore_ingest','agentcore_worker','agentcore_admin','agentcore_backup','agentcore_cognee']
  LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
      EXECUTE format('CREATE ROLE %I NOLOGIN', role_name);
    END IF;
  END LOOP;
END
`$`$;
"@
  Invoke-Psql -Sql $roleSql | Out-Null

  foreach ($database in $Databases) {
    $dumpPath = Join-Path $logicalRoot "$database.dump"
    if (-not (Test-Path -LiteralPath $dumpPath)) { throw "Database dump missing: $dumpPath" }
    Invoke-NativeChecked -Command $createdb -Arguments @("-h", "127.0.0.1", "-p", [string]$RestorePort, "-U", "postgres", $database) -FailureMessage "createdb $database failed" | Out-Null
    Invoke-NativeChecked -Command $pgRestore -Arguments @("-h", "127.0.0.1", "-p", [string]$RestorePort, "-U", "postgres", "-d", $database, $dumpPath) -FailureMessage "pg_restore $database failed" | Out-Null
  }

  $validation = [ordered]@{}
  $validation.agent_core_extensions = Invoke-Psql -Db "agent_core" -TupleOnly -Sql "SELECT jsonb_agg(extname || '=' || extversion ORDER BY extname)::text FROM pg_extension;"
  $validation.agentcore_roles = Invoke-Psql -TupleOnly -Sql "SELECT jsonb_agg(rolname ORDER BY rolname)::text FROM pg_roles WHERE rolname LIKE 'agentcore_%';"
  $rowCountsMap = [ordered]@{}
  foreach ($tableName in @(
    "agentcore.evidence_events",
    "agentcore.context_summaries",
    "agentcore.projection_revisions",
    "agentcore.retrieval_documents",
    "agentcore.knowledge_promotions"
  )) {
    $exists = Invoke-Psql -Db "agent_core" -TupleOnly -Sql "SELECT to_regclass('$tableName') IS NOT NULL;"
    if ($exists.Trim() -eq "t") {
      $rowCountsMap[$tableName] = [int64](Invoke-Psql -Db "agent_core" -TupleOnly -Sql "SELECT COUNT(*)::text FROM $tableName;")
    } else {
      $rowCountsMap[$tableName] = $null
    }
  }
  $validation.agent_core_row_counts = $rowCountsMap
  $validation.cognee_tables = Invoke-Psql -Db "cognee_core" -TupleOnly -Sql "SELECT COUNT(*)::text FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema');"

  $report = [pscustomobject]@{
    ok = $true
    backup_path = $latest.FullName
    manifest = $manifestPath
    restore_root = $runRoot
    restore_port = $RestorePort
    restored_databases = $Databases
    validation = $validation
    validated_at = (Get-Date).ToUniversalTime().ToString("o")
  }
  $reportPath = Join-Path $evidencePath "pg18-restore-test-$stamp.json"
  $report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding utf8
  $report | ConvertTo-Json -Depth 10
}
finally {
  if ($started) {
    Invoke-PgCtlChecked -Arguments @("-D", $dataDir, "stop", "-m", "fast", "-w") -FailureMessage "restore cluster stop failed" -AllowErrors | Out-Null
  }
}
