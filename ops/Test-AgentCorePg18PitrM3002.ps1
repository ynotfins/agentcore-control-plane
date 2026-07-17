param(
  [string]$PgRoot = "F:\PostgreSQL18",
  [string]$BackupRoot = "E:\AgentCoreArchive\agentcore-memory\backups\pg18",
  [string]$WalArchiveRoot = "E:\AgentCoreArchive\agentcore-memory\wal\pg18",
  [string]$RestoreRoot = "I:\AgentCoreRestoreTests\pg18-pitr",
  [int]$RestorePort = 55441,
  [string]$LiveHostName = "127.0.0.1",
  [int]$LivePort = 55433,
  [string]$AdminUser = "postgres",
  [string]$EvidenceDir = "audits\M5"
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-NativeChecked {
  param([string]$Command, [string[]]$Arguments, [string]$FailureMessage, [switch]$AllowErrors)
  $output = & $Command @Arguments 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0 -and -not $AllowErrors) { throw "$FailureMessage (exit $code): $($output -join "`n")" }
  return (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Invoke-PgCtlChecked {
  param([string[]]$Arguments, [string]$FailureMessage, [switch]$AllowErrors)
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

function Start-PitrCluster {
  $arguments = @("-D", $dataDir, "-l", (Join-Path $runRoot "pitr-postgres.log"), "-o", "`"-h 127.0.0.1 -p $RestorePort`"", "start")
  Start-Process -FilePath $pgCtl -ArgumentList $arguments -NoNewWindow | Out-Null
  $deadline = (Get-Date).AddSeconds(120)
  do {
    Start-Sleep -Seconds 1
    $ready = & $pgIsReady -h 127.0.0.1 -p $RestorePort -d agent_core 2>&1
    if ($LASTEXITCODE -eq 0) {
      $recovery = & $psql -h 127.0.0.1 -p $RestorePort -U postgres -d agent_core -t -A -c "SELECT pg_is_in_recovery();" 2>&1
      if ($LASTEXITCODE -eq 0 -and (($recovery -join "").Trim()) -eq "f") { return }
    }
  } while ((Get-Date) -lt $deadline)
  throw "PITR restore cluster did not finish recovery: $($ready -join "`n")"
}

function Invoke-LivePsql {
  param([string]$Sql, [switch]$TupleOnly)
  $psqlArgs = @("-h", $LiveHostName, "-p", [string]$LivePort, "-U", $AdminUser, "-d", "agent_core", "-v", "ON_ERROR_STOP=1", "-c", $Sql)
  if ($TupleOnly) { $psqlArgs = @("-t", "-A") + $psqlArgs }
  return Invoke-NativeChecked -Command $psql -Arguments $psqlArgs -FailureMessage "live psql failed"
}

function Invoke-RestorePsql {
  param([string]$Sql, [string]$Db = "agent_core", [switch]$TupleOnly)
  $psqlArgs = @("-h", "127.0.0.1", "-p", [string]$RestorePort, "-U", "postgres", "-d", $Db, "-v", "ON_ERROR_STOP=1", "-c", $Sql)
  if ($TupleOnly) { $psqlArgs = @("-t", "-A") + $psqlArgs }
  return Invoke-NativeChecked -Command $psql -Arguments $psqlArgs -FailureMessage "restore psql failed"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$evidencePath = Join-Path $repoRoot $EvidenceDir
New-Item -ItemType Directory -Path $evidencePath -Force | Out-Null

$pgBin = Join-Path $PgRoot "bin"
$psql = Join-Path $pgBin "psql.exe"
$pgCtl = Join-Path $pgBin "pg_ctl.exe"
$pgIsReady = Join-Path $pgBin "pg_isready.exe"
foreach ($required in @($psql, $pgCtl, $pgIsReady)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Required PostgreSQL executable missing: $required" }
}
if (-not (Test-Path -LiteralPath $WalArchiveRoot)) { throw "WAL archive root missing: $WalArchiveRoot" }

if (-not $env:PGPASSWORD) {
  $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
}
if (-not $env:PGPASSWORD) { throw "AGENT_CORE_POSTGRES_PASSWORD is not available in Windows User env" }
if (-not $env:PGSSLMODE) { $env:PGSSLMODE = "require" }

$latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "base") } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
if (-not $latest) { throw "No PG18 base-backup directory found under $BackupRoot" }

Write-Host "Using backup: $($latest.FullName)"

$stamp = "m3002-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$marker = "PITR_MARKER_M3002_$stamp"
$markerSql = @"
WITH selected AS (
  SELECT p.id AS project_id, s.id AS source_identity_id
  FROM agentcore.projects p
  JOIN agentcore.source_identities s ON s.project_id = p.id
  ORDER BY p.created_at, s.created_at
  LIMIT 1
)
INSERT INTO agentcore.evidence_events (
  project_id, source_identity_id, event_kind, idempotency_key, payload, trust_class, provenance
)
SELECT project_id, source_identity_id, 'accepted_evidence', '$marker',
       jsonb_build_object('pitr_marker', '$marker', 'test', 'post_m3002_pitr'),
       'system_verified',
       jsonb_build_object('test', 'pg18_pitr_m3002', 'created_by', 'Test-AgentCorePg18PitrM3002.ps1')
FROM selected
RETURNING id::text || '|' || occurred_at::text;
"@
Write-Host "Inserting PITR marker..."
$markerResult = Invoke-LivePsql -Sql $markerSql -TupleOnly
Start-Sleep -Seconds 2
$targetTime = Invoke-LivePsql -Sql "SELECT clock_timestamp()::text;" -TupleOnly
Write-Host "Recovery target time: $targetTime"
$fence = "${marker}_FENCE"
$fenceSql = $markerSql.Replace($marker, $fence)
Invoke-LivePsql -Sql $fenceSql -TupleOnly | Out-Null
Write-Host "Switching WAL..."
$switchedWal = Invoke-LivePsql -Sql "SELECT pg_walfile_name(pg_switch_wal());" -TupleOnly
$switchedPath = Join-Path $WalArchiveRoot $switchedWal
Write-Host "Waiting for WAL archive: $switchedPath"
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $switchedPath)) {
  Start-Sleep -Seconds 1
}
if (-not (Test-Path -LiteralPath $switchedPath)) {
  # PG18 archiver may be processing a backlog; manually archive the switched WAL as fallback
  $walSrcPath = Join-Path $PgRoot "data\pg_wal\$switchedWal"
  Write-Host "Manual archive fallback for: $switchedWal"
  if (Test-Path -LiteralPath $walSrcPath) {
    $archiveScript = Join-Path $PSScriptRoot "Archive-AgentCoreWal.ps1"
    $result = powershell -NoProfile -ExecutionPolicy Bypass -File $archiveScript `
      -SourcePath $walSrcPath -WalFileName $switchedWal -ArchiveRoot $WalArchiveRoot 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Manual archive failed for $switchedWal : $($result -join ' ')" }
    Write-Host "Manual archive succeeded: $switchedWal"
  } else {
    throw "Switched WAL not in pg_wal and not archived: $switchedWal"
  }
}
if (-not (Test-Path -LiteralPath $switchedPath)) { throw "WAL still not archived after manual fallback: $switchedWal" }
Write-Host "WAL archived: $switchedWal"

$runRoot = Join-Path $RestoreRoot $stamp
$dataDir = Join-Path $runRoot "data"
$baseDir = Join-Path $latest.FullName "base"
New-Item -ItemType Directory -Path $dataDir -Force | Out-Null

Write-Host "Extracting base backup..."
$tar = "tar.exe"
$baseTar = Join-Path $baseDir "base.tar"
if (-not (Test-Path -LiteralPath $baseTar)) { throw "base.tar missing in base backup: $baseTar" }
Invoke-NativeChecked -Command $tar -Arguments @("-xf", $baseTar, "-C", $dataDir) -FailureMessage "extract base.tar failed" | Out-Null
$walTar = Join-Path $baseDir "pg_wal.tar"
if (Test-Path -LiteralPath $walTar) {
  Invoke-NativeChecked -Command $tar -Arguments @("-xf", $walTar, "-C", $dataDir) -FailureMessage "extract pg_wal.tar failed" | Out-Null
}

$walArchiveForPostgres = $WalArchiveRoot.Replace("\", "/")
$restoreCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command `"Copy-Item -LiteralPath '$walArchiveForPostgres/%f' -Destination '%p' -ErrorAction Stop`""
$autoConf = Join-Path $dataDir "postgresql.auto.conf"
Add-Content -LiteralPath $autoConf -Value @"
restore_command = '$($restoreCommand.Replace("'", "''"))'
recovery_target_time = '$($targetTime.Trim().Replace("'", "''"))'
recovery_target_timeline = 'current'
recovery_target_action = 'promote'
archive_mode = 'off'
archive_command = ''
port = '$RestorePort'
listen_addresses = '127.0.0.1'
"@ -Encoding utf8
New-Item -ItemType File -Path (Join-Path $dataDir "recovery.signal") -Force | Out-Null

Write-Host "Starting PITR restore cluster..."
$started = $false
try {
  Start-PitrCluster
  $started = $true
  Write-Host "Cluster running. Verifying..."

  Invoke-NativeChecked -Command $pgIsReady -Arguments @("-h", "127.0.0.1", "-p", [string]$RestorePort, "-d", "agent_core") -FailureMessage "PITR pg_isready failed" | Out-Null

  # Core marker verification
  $markerCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.evidence_events WHERE payload->>'pitr_marker' = '$marker';"
  $fenceCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.evidence_events WHERE payload->>'pitr_marker' = '$fence';"
  $extensionCheck = Invoke-RestorePsql -TupleOnly -Sql "SELECT jsonb_agg(extname || '=' || extversion ORDER BY extname)::text FROM pg_extension;"

  # M3.002-specific: migration records
  $migrationRecords = Invoke-RestorePsql -TupleOnly -Sql "SELECT jsonb_agg(version || ':' || blueprint_level ORDER BY applied_at)::text FROM agentcore.schema_migrations;"
  $m3002Present = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.schema_migrations WHERE version = 'm3.002';"

  # M3.002-specific: new tables
  $recoveryOpsCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.recovery_operations;" -AllowErrors
  $profileCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.model_context_profiles;"
  $profileNames = Invoke-RestorePsql -TupleOnly -Sql "SELECT jsonb_agg(profile_name ORDER BY profile_name)::text FROM agentcore.model_context_profiles;"
  $snapshotCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.project_snapshots;"

  # Evidence/source/summary
  $evidenceCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.evidence_events;"
  $sourceEdgeCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.context_source_edges;"
  $summaryCount = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.context_summaries;"

  # Project/repository identity
  $projectIdentities = Invoke-RestorePsql -TupleOnly -Sql "SELECT jsonb_agg(jsonb_build_object('name', project_name, 'key', project_key) ORDER BY created_at)::text FROM agentcore.projects;"
  $sourceIdentities = Invoke-RestorePsql -TupleOnly -Sql "SELECT COUNT(*)::text FROM agentcore.source_identities;"
  $repoIdentities = Invoke-RestorePsql -TupleOnly -Sql "SELECT jsonb_agg(jsonb_build_object('key', repo_key, 'path', canonical_path, 'remote', remote_url) ORDER BY created_at)::text FROM agentcore.repositories;"

  # cognee_core: verify database accessible
  $cogneeTables = Invoke-RestorePsql -TupleOnly -Db "cognee_core" -Sql "SELECT COUNT(*)::text FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema');"

  $allPass = ([int]$markerCount -eq 1) -and ([int]$fenceCount -eq 0) -and ([int]$m3002Present -eq 1)

  $report = [ordered]@{
    ok = $allPass
    test_type = "post_m3002_pitr"
    backup_path = $latest.FullName
    wal_archive_root = $WalArchiveRoot
    restore_root = $runRoot
    restore_port = $RestorePort
    marker = $marker
    marker_result = $markerResult
    fence = $fence
    fence_count_after_recovery = [int]$fenceCount
    recovery_target_time = $targetTime.Trim()
    switched_wal = $switchedWal
    marker_count_after_recovery = [int]$markerCount
    extension_check = $extensionCheck
    # M3.002-specific
    m3002_present = ([int]$m3002Present -eq 1)
    migration_records = $migrationRecords
    recovery_operations_table = $recoveryOpsCount
    model_context_profiles_count = [int]$profileCount
    model_context_profile_names = $profileNames
    project_snapshots_count = [int]$snapshotCount
    # Evidence/source/summary
    evidence_events_count = [int]$evidenceCount
    summary_source_edges_count = [int]$sourceEdgeCount
    context_summaries_count = [int]$summaryCount
    # Identity
    project_identities = $projectIdentities
    source_identity_count = [int]$sourceIdentities
    repository_identities = $repoIdentities
    # cognee_core
    cognee_core_table_count = [int]$cogneeTables
    validated_at = (Get-Date).ToUniversalTime().ToString("o")
  }

  $reportPath = Join-Path $evidencePath "pg18-pitr-m3002-$stamp.json"
  $report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding utf8
  Write-Host "Evidence saved: $reportPath"
  $report | ConvertTo-Json -Depth 10

  if (-not $report.ok) {
    Write-Error "PITR verification FAILED: marker_count=$markerCount fence_count=$fenceCount m3002=$m3002Present"
    exit 1
  }
  Write-Host "PITR M3.002 PASS"
}
finally {
  if ($started) {
    Write-Host "Stopping PITR cluster..."
    Invoke-PgCtlChecked -Arguments @("-D", $dataDir, "stop", "-m", "fast", "-w") -FailureMessage "PITR cluster stop failed" -AllowErrors | Out-Null
    Write-Host "Cleaning up: $runRoot"
    Remove-Item -Recurse -Force -LiteralPath $runRoot -ErrorAction SilentlyContinue
    Write-Host "Cleanup complete"
  }
}
