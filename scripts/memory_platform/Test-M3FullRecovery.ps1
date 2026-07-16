[CmdletBinding()]
param(
  [string]$PgBin = "F:\PostgreSQL18\bin",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55433,
  [string]$AdminUser = "postgres",
  [string]$ScratchRoot = "D:\test"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runId = [DateTimeOffset]::UtcNow.ToString("yyyyMMddHHmmss")
$sourceDb = "agentcore_m3_full_recovery_$runId"
$restoreDb = "${sourceDb}_restore"
$dumpPath = Join-Path $ScratchRoot "$sourceDb.dump"
$password = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
if (-not $password) {
  throw "AGENT_CORE_POSTGRES_PASSWORD is unavailable in Windows User scope"
}
$env:PGPASSWORD = $password

function Invoke-PgTool {
  param([string]$Tool, [string[]]$Arguments)
  & (Join-Path $PgBin $Tool) @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$Tool failed with exit code $LASTEXITCODE"
  }
}

function Get-GraphFingerprint {
  param([string]$Database)
  $sql = @"
SELECT jsonb_build_object(
  'events', (SELECT count(*) FROM agentcore.evidence_events),
  'event_hash', (SELECT encode(digest(coalesce(string_agg(id::text || payload::text, ',' ORDER BY id), ''), 'sha256'), 'hex') FROM agentcore.evidence_events),
  'summaries', (SELECT count(*) FROM agentcore.context_summaries),
  'summary_hash', (SELECT encode(digest(coalesce(string_agg(id::text || summary_sha256, ',' ORDER BY id), ''), 'sha256'), 'hex') FROM agentcore.context_summaries),
  'source_edges', (SELECT count(*) FROM agentcore.context_source_edges),
  'recovery_operations', (SELECT count(*) FROM agentcore.recovery_operations),
  'snapshots', (SELECT count(*) FROM agentcore.project_snapshots),
  'profiles', (SELECT count(*) FROM agentcore.model_context_profiles),
  'future_limit', (SELECT hard_context_limit FROM agentcore.model_context_profiles WHERE profile_name = 'future-above-million')
)::text;
"@
  $value = & (Join-Path $PgBin "psql.exe") -q -h $HostName -p $Port -U $AdminUser -d $Database -t -A -v ON_ERROR_STOP=1 -c $sql
  if ($LASTEXITCODE -ne 0) {
    throw "graph fingerprint query failed"
  }
  return ($value | Out-String).Trim()
}

Invoke-PgTool "dropdb.exe" @("-h", $HostName, "-p", "$Port", "-U", $AdminUser, "--if-exists", $sourceDb)
Invoke-PgTool "dropdb.exe" @("-h", $HostName, "-p", "$Port", "-U", $AdminUser, "--if-exists", $restoreDb)

try {
  Invoke-PgTool "createdb.exe" @("-h", $HostName, "-p", "$Port", "-U", $AdminUser, $sourceDb)
  Invoke-PgTool "psql.exe" @(
    "-q", "-h", $HostName, "-p", "$Port", "-U", $AdminUser, "-d", $sourceDb,
    "-v", "ON_ERROR_STOP=1",
    "-c", "CREATE EXTENSION pgcrypto; CREATE EXTENSION vector;",
    "-f", (Join-Path $repo "migrations\m2\001_up_canonical_identity_immutable_evidence.sql"),
    "-f", (Join-Path $repo "migrations\m3\001_up_lossless_context_state_projections.sql"),
    "-f", (Join-Path $repo "migrations\m3\002_up_unbounded_recovery_context_profiles.sql")
  )

  $oldDatabase = $env:AGENTCORE_PG_DATABASE
  $oldRepo = $env:AGENTCORE_REPO_PATH
  $oldArtifacts = $env:AGENTCORE_HOT_ARTIFACT_ROOT
  try {
    $env:AGENTCORE_PG_DATABASE = $sourceDb
    $env:AGENTCORE_REPO_PATH = $repo
    $env:AGENTCORE_HOT_ARTIFACT_ROOT = Join-Path $ScratchRoot "$sourceDb-artifacts"
    & python (Join-Path $repo "scripts\agentcore_memory\integration_test_recovery.py")
    if ($LASTEXITCODE -ne 0) {
      throw "recovery integration test failed"
    }
  }
  finally {
    $env:AGENTCORE_PG_DATABASE = $oldDatabase
    $env:AGENTCORE_REPO_PATH = $oldRepo
    $env:AGENTCORE_HOT_ARTIFACT_ROOT = $oldArtifacts
  }

  $before = Get-GraphFingerprint $sourceDb
  Invoke-PgTool "pg_dump.exe" @(
    "-h", $HostName, "-p", "$Port", "-U", $AdminUser, "-d", $sourceDb,
    "--format=custom", "--no-owner", "--no-acl", "--file", $dumpPath
  )
  Invoke-PgTool "createdb.exe" @("-h", $HostName, "-p", "$Port", "-U", $AdminUser, $restoreDb)
  Invoke-PgTool "pg_restore.exe" @(
    "-h", $HostName, "-p", "$Port", "-U", $AdminUser, "-d", $restoreDb,
    "--no-owner", "--no-acl", "--exit-on-error", $dumpPath
  )
  $after = Get-GraphFingerprint $restoreDb
  if ($before -ne $after) {
    throw "backup/restore changed the event/source/summary graph`nBEFORE $before`nAFTER  $after"
  }

  Write-Output "PASS: M3 full recovery, summary correction, stable pagination, and backup/restore graph integrity"
  Write-Output $after
}
finally {
  Invoke-PgTool "dropdb.exe" @("-h", $HostName, "-p", "$Port", "-U", $AdminUser, "--if-exists", $restoreDb)
  Invoke-PgTool "dropdb.exe" @("-h", $HostName, "-p", "$Port", "-U", $AdminUser, "--if-exists", $sourceDb)
  Remove-Item -LiteralPath $dumpPath -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath (Join-Path $ScratchRoot "$sourceDb-artifacts") -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath (Join-Path $ScratchRoot "$sourceDb-cold-e") -Recurse -Force -ErrorAction SilentlyContinue
}
