param(
  [string]$PgRoot = "F:\PostgreSQL18",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55433,
  [string]$Database = "agent_core",
  [string]$AdminUser = "postgres",
  [string]$ArtifactRoot = "H:\AgentRuntime\agentcore-memory\artifacts",
  [string]$EvidenceDir = "audits\M2"
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$pgBin = Join-Path $PgRoot "bin"
$psql = Join-Path $pgBin "psql.exe"
$createdb = Join-Path $pgBin "createdb.exe"
$dropdb = Join-Path $pgBin "dropdb.exe"
$pgIsReady = Join-Path $pgBin "pg_isready.exe"
$upMigration = Join-Path $repoRoot "migrations\m2\001_up_canonical_identity_immutable_evidence.sql"
$downMigration = Join-Path $repoRoot "migrations\m2\001_down_canonical_identity_immutable_evidence.sql"
$evidencePath = Join-Path $repoRoot $EvidenceDir
New-Item -ItemType Directory -Path $evidencePath -Force | Out-Null

if (-not (Test-Path $psql)) { throw "psql not found at $psql" }
if (-not (Test-Path $upMigration)) { throw "M2 up migration missing: $upMigration" }
if (-not (Test-Path $downMigration)) { throw "M2 down migration missing: $downMigration" }

$env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
$env:PGSSLMODE = "require"
if (-not $env:PGPASSWORD) { throw "AGENT_CORE_POSTGRES_PASSWORD is not available in Windows User env" }

function Invoke-Psql {
  param(
    [string]$Sql,
    [string]$Db = $Database,
    [string]$User = $AdminUser,
    [switch]$TupleOnly
  )
  $tmp = Join-Path $env:TEMP ("agentcore-sql-{0}.sql" -f ([guid]::NewGuid().ToString("N")))
  $Sql | Set-Content -LiteralPath $tmp -Encoding utf8
  $args = @("-h", $HostName, "-p", [string]$Port, "-U", $User, "-d", $Db, "-v", "ON_ERROR_STOP=1", "-f", $tmp)
  if ($TupleOnly) { $args = @("-t", "-A") + $args }
  $previousEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & $psql @args 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousEap
  }
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  if ($code -ne 0) {
    throw "psql failed ($code): $($out -join "`n")"
  }
  return (($out | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Invoke-PsqlFile {
  param(
    [string]$Path,
    [string]$Db = $Database
  )
  $previousEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & $psql -h $HostName -p $Port -U $AdminUser -d $Db -v ON_ERROR_STOP=1 -f $Path 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousEap
  }
  if ($code -ne 0) {
    throw "psql file failed ($code): $Path`n$($out -join "`n")"
  }
  return (($out | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Invoke-ExpectFailure {
  param(
    [string]$Name,
    [string]$Sql
  )
  $tmp = Join-Path $env:TEMP ("agentcore-fail-{0}.sql" -f ([guid]::NewGuid().ToString("N")))
  $Sql | Set-Content -LiteralPath $tmp -Encoding utf8
  $previousEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & $psql -h $HostName -p $Port -U $AdminUser -d $Database -v ON_ERROR_STOP=1 -f $tmp 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousEap
  }
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  if ($code -eq 0) {
    throw "Expected failure did not occur: $Name"
  }
  return "$Name`: PASS expected failure`n$($out -join "`n")"
}

function Restart-Pg18 {
  $script = @"
Restart-Service "AgentCore-PostgreSQL18" -Force
Start-Sleep -Seconds 5
Get-Service "AgentCore-PostgreSQL18" | Select-Object Name,Status | ConvertTo-Json
"@
  $scriptPath = Join-Path $env:TEMP "agentcore-pg18-restart.ps1"
  $script | Set-Content -LiteralPath $scriptPath -Encoding utf8
  $proc = Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs -Wait -PassThru
  if ($proc.ExitCode -ne 0) { throw "PG18 restart failed with exit code $($proc.ExitCode)" }
  $ready = & $pgIsReady -h $HostName -p $Port 2>&1
  if ($LASTEXITCODE -ne 0) { throw "PG18 not ready after restart: $ready" }
}

$runId = Get-Date -Format "yyyyMMddHHmmss"
$summary = [ordered]@{
  run_id = $runId
  started_at = (Get-Date).ToUniversalTime().ToString("o")
  database = "$HostName`:$Port/$Database"
  migration = "m2.001"
  checks = @()
}

function Add-Check {
  param([string]$Name, [string]$Result, [string]$Detail = "")
  $script:summary.checks += [ordered]@{ name = $Name; result = $Result; detail = $Detail }
}

try {
  # 1. Verify migration reversibility in a disposable database.
  $rollbackDb = "agentcore_m2_rollback_$runId"
  & $createdb -h $HostName -p $Port -U $AdminUser $rollbackDb 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "createdb failed for $rollbackDb" }
  Invoke-Psql "CREATE EXTENSION IF NOT EXISTS pgcrypto; CREATE EXTENSION IF NOT EXISTS vector;" -Db $rollbackDb | Out-Null
  Invoke-PsqlFile -Path $upMigration -Db $rollbackDb | Out-Null
  $schemaExists = Invoke-Psql "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name='agentcore');" -Db $rollbackDb -TupleOnly
  if ($schemaExists -ne "t") { throw "agentcore schema missing in rollback test after up migration" }
  Invoke-PsqlFile -Path $downMigration -Db $rollbackDb | Out-Null
  $schemaAfterDown = Invoke-Psql "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name='agentcore');" -Db $rollbackDb -TupleOnly
  if ($schemaAfterDown -ne "f") { throw "agentcore schema still present after down migration" }
  & $dropdb -h $HostName -p $Port -U $AdminUser $rollbackDb 2>&1 | Out-Null
  Add-Check "versioned reversible migration" "PASS" "up/down tested in disposable database $rollbackDb"

  # 2. Apply migration to agent_core if not already applied.
  $alreadyApplied = Invoke-Psql "SELECT EXISTS (SELECT 1 FROM agentcore.schema_migrations WHERE version = 'm2.001');" -TupleOnly
  if ($alreadyApplied -ne "t") {
    Invoke-PsqlFile -Path $upMigration -Db $Database | Out-Null
    Add-Check "live M2 migration applied" "PASS" "migrations/m2/001_up_canonical_identity_immutable_evidence.sql"
  } else {
    Add-Check "live M2 migration applied" "PASS" "m2.001 already present in schema_migrations"
  }

  # 3. Seed identities for two projects.
  $seedSql = @"
WITH
machine AS (
  INSERT INTO agentcore.machines (machine_name, hardware_ref)
  VALUES ('CHAOSCENTRAL', 'D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md')
  ON CONFLICT (machine_name) DO UPDATE SET hardware_ref = EXCLUDED.hardware_ref
  RETURNING id
),
usr AS (
  INSERT INTO agentcore.users (username, display_name)
  VALUES ('ynotf', 'Tony Valentine')
  ON CONFLICT (username) DO UPDATE SET display_name = EXCLUDED.display_name
  RETURNING id
),
repo AS (
  INSERT INTO agentcore.repositories (repo_key, canonical_path, remote_url)
  VALUES ('agentcore-control-plane', 'D:\github\agentcore-control-plane', 'https://github.com/ynotfins/agentcore-control-plane.git')
  ON CONFLICT (canonical_path) DO UPDATE SET remote_url = EXCLUDED.remote_url
  RETURNING id
),
wt AS (
  INSERT INTO agentcore.worktrees (repository_id, worktree_path, branch_name, head_commit)
  SELECT id, 'D:\github\agentcore-control-plane', 'task/authority-reconciliation', 'm2-$runId' FROM repo
  ON CONFLICT (worktree_path) DO UPDATE SET head_commit = EXCLUDED.head_commit
  RETURNING id, repository_id
),
project_a AS (
  INSERT INTO agentcore.projects (project_key, project_name, repository_id, primary_worktree_id, root_path, current_milestone)
  SELECT 'm2_project_a_$runId', 'M2 Project A', wt.repository_id, wt.id, 'D:\github\agentcore-control-plane', 'M2' FROM wt
  RETURNING id
),
project_b AS (
  INSERT INTO agentcore.projects (project_key, project_name, repository_id, primary_worktree_id, root_path, current_milestone)
  SELECT 'm2_project_b_$runId', 'M2 Project B', wt.repository_id, wt.id, 'D:\github\agentcore-control-plane', 'M2' FROM wt
  RETURNING id
),
pwt_a AS (
  INSERT INTO agentcore.project_worktrees (project_id, worktree_id, is_primary)
  SELECT project_a.id, wt.id, true FROM project_a, wt
  ON CONFLICT DO NOTHING
),
pwt_b AS (
  INSERT INTO agentcore.project_worktrees (project_id, worktree_id, is_primary)
  SELECT project_b.id, wt.id, false FROM project_b, wt
  ON CONFLICT DO NOTHING
),
client AS (
  INSERT INTO agentcore.ide_clients (client_key, display_name, profile_id)
  VALUES ('cursor-$runId', 'Cursor', 'builder-core')
  ON CONFLICT (client_key) DO UPDATE SET display_name = EXCLUDED.display_name
  RETURNING id
),
agent AS (
  INSERT INTO agentcore.agents (agent_key, display_name, model_hint)
  VALUES ('cursor-agent-$runId', 'Cursor Agent', 'unknown')
  ON CONFLICT (agent_key) DO UPDATE SET display_name = EXCLUDED.display_name
  RETURNING id
),
session AS (
  INSERT INTO agentcore.sessions (project_id, client_id, agent_id, session_key)
  SELECT project_a.id, client.id, agent.id, 'session-$runId' FROM project_a, client, agent
  RETURNING id, project_id, client_id, agent_id
),
run AS (
  INSERT INTO agentcore.runs (session_id, run_key)
  SELECT id, 'run-$runId' FROM session
  RETURNING id, session_id
),
workflow AS (
  INSERT INTO agentcore.workflows (project_id, workflow_key, display_name)
  SELECT project_a.id, 'workflow-$runId', 'M2 Test Workflow' FROM project_a
  RETURNING id, project_id
),
thread AS (
  INSERT INTO agentcore.workflow_threads (workflow_id, thread_key)
  SELECT id, 'thread-$runId' FROM workflow
  RETURNING id, workflow_id
),
source AS (
  INSERT INTO agentcore.source_identities (
    machine_id, user_id, project_id, repository_id, worktree_id, client_id, agent_id,
    session_id, run_id, workflow_thread_id, source_label, trust_class
  )
  SELECT machine.id, usr.id, project_a.id, wt.repository_id, wt.id, client.id, agent.id,
         session.id, run.id, thread.id, 'm2-source-$runId', 'operator_verified'
  FROM machine, usr, project_a, wt, client, agent, session, run, thread
  RETURNING id
)
SELECT jsonb_build_object(
  'project_a', (SELECT id FROM project_a),
  'project_b', (SELECT id FROM project_b),
  'source_a', (SELECT id FROM source),
  'client', (SELECT id FROM client),
  'agent', (SELECT id FROM agent),
  'session', (SELECT id FROM session),
  'run', (SELECT id FROM run),
  'thread', (SELECT id FROM thread)
)::text;
"@
  $ids = (Invoke-Psql $seedSql -TupleOnly) | ConvertFrom-Json
  Add-Check "separate identities seeded" "PASS" ("project_a={0}; project_b={1}; source={2}" -f $ids.project_a, $ids.project_b, $ids.source_a)

  # 4. Idempotent immutable evidence append.
  $appendSql = @"
SET agentcore.current_project_id = '$($ids.project_a)';
SELECT agentcore.append_evidence_event(
  '$($ids.project_a)', '$($ids.source_a)', 'decision', 'idem-$runId',
  '{"decision":"m2-idempotency"}'::jsonb, NULL, 'operator_verified',
  '{"source":"Test-M2CanonicalIdentity.ps1"}'::jsonb
);
SELECT agentcore.append_evidence_event(
  '$($ids.project_a)', '$($ids.source_a)', 'decision', 'idem-$runId',
  '{"decision":"m2-idempotency-duplicate"}'::jsonb, NULL, 'operator_verified',
  '{"source":"Test-M2CanonicalIdentity.ps1"}'::jsonb
);
SELECT count(*) FROM agentcore.evidence_events
WHERE source_identity_id = '$($ids.source_a)' AND idempotency_key = 'idem-$runId';
"@
  $appendOut = Invoke-Psql $appendSql -TupleOnly
  $lines = @($appendOut -split "`n" | Where-Object {
    $_.Trim() -match '^[0-9a-fA-F-]{36}$' -or $_.Trim() -match '^\d+$'
  })
  $eventId1 = $lines[0].Trim()
  $eventId2 = $lines[1].Trim()
  $eventCount = [int]$lines[2].Trim()
  if ($eventId1 -ne $eventId2 -or $eventCount -ne 1) {
    throw "idempotency failed: event1=$eventId1 event2=$eventId2 count=$eventCount"
  }
  Add-Check "idempotent event submission" "PASS" "duplicate submission returned same event id and one row"

  # 5. UPDATE/DELETE denied to normal service role, and cross-project function write rejected.
  $denyUpdate = Invoke-ExpectFailure -Name "agentcore_ingest update evidence denied" -Sql @"
SET ROLE agentcore_ingest;
UPDATE agentcore.evidence_events SET payload = '{}'::jsonb WHERE id = '$eventId1';
"@
  $denyDelete = Invoke-ExpectFailure -Name "agentcore_ingest delete evidence denied" -Sql @"
SET ROLE agentcore_ingest;
DELETE FROM agentcore.evidence_events WHERE id = '$eventId1';
"@
  Add-Check "UPDATE/DELETE denied to normal roles" "PASS" "agentcore_ingest cannot update or delete evidence"

  $crossProject = Invoke-ExpectFailure -Name "Project A cannot write Project B" -Sql @"
SET agentcore.current_project_id = '$($ids.project_a)';
SELECT agentcore.append_evidence_event(
  '$($ids.project_b)', '$($ids.source_a)', 'decision', 'cross-project-$runId',
  '{"bad":true}'::jsonb, NULL, 'project_verified', '{}'::jsonb
);
"@
  Add-Check "cross-project write rejected" "PASS" "security-definer function enforces current project boundary"

  # 6. Content-addressed large payload externalization on H:.
  $payload = ("M2 large payload {0} " -f $runId) * 4096
  $payloadBytes = [Text.Encoding]::UTF8.GetBytes($payload)
  $sha = [System.BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($payloadBytes)).Replace("-", "").ToLowerInvariant()
  $artifactDir = Join-Path $ArtifactRoot ("sha256\{0}" -f $sha.Substring(0,2))
  New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null
  $artifactPath = Join-Path $artifactDir ($sha + ".txt")
  [IO.File]::WriteAllBytes($artifactPath, $payloadBytes)
  $verifySha = [System.BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([IO.File]::ReadAllBytes($artifactPath))).Replace("-", "").ToLowerInvariant()
  if ($verifySha -ne $sha) { throw "artifact hash mismatch" }
  $artifactSql = @"
SET agentcore.current_project_id = '$($ids.project_a)';
INSERT INTO agentcore.artifact_objects (project_id, sha256, bytes, storage_uri, mime_type, trust_class, source_identity_id)
VALUES ('$($ids.project_a)', '$sha', $($payloadBytes.Length), '$($artifactPath.Replace("'", "''"))', 'text/plain', 'operator_verified', '$($ids.source_a)')
RETURNING id;
"@
  $artifactId = @((Invoke-Psql $artifactSql -TupleOnly) -split "`n" | Where-Object {
    $_.Trim() -match '^[0-9a-fA-F-]{36}$'
  })[0].Trim()
  $artifactEventSql = @"
SET agentcore.current_project_id = '$($ids.project_a)';
SELECT agentcore.append_evidence_event(
  '$($ids.project_a)', '$($ids.source_a)', 'accepted_evidence', 'artifact-$runId',
  '{"externalized":true}'::jsonb, '$artifactId', 'operator_verified',
  '{"sha256":"$sha","storage_uri":"$($artifactPath.Replace("\", "\\"))"}'::jsonb
);
"@
  $artifactEventId = @((Invoke-Psql $artifactEventSql -TupleOnly) -split "`n" | Where-Object {
    $_.Trim() -match '^[0-9a-fA-F-]{36}$'
  })[0].Trim()
  Add-Check "content-addressed large payload externalized" "PASS" "artifact=$artifactPath sha256=$sha event=$artifactEventId"

  # 7. Queue, claim, lease, dead-letter restart recovery.
  $queueSql = @"
SET agentcore.current_project_id = '$($ids.project_a)';
SELECT agentcore.enqueue_work('$($ids.project_a)', 'recover-$runId', 'm2-test', '{"case":"recover"}'::jsonb, 3);
SELECT * FROM agentcore.claim_work('$($ids.project_a)', '$($ids.source_a)', 1);
SELECT agentcore.enqueue_work('$($ids.project_a)', 'dead-$runId', 'm2-test', '{"case":"dead"}'::jsonb, 1);
SELECT * FROM agentcore.claim_work('$($ids.project_a)', '$($ids.source_a)', 1);
SELECT agentcore.create_capability_lease('$($ids.project_a)', '$($ids.source_a)', 'dummy.tool', 'M2.Q1-$runId', 1, 'restart recovery test', ARRAY['execute']);
"@
  $queueOut = Invoke-Psql $queueSql -TupleOnly
  Start-Sleep -Seconds 2
  Restart-Pg18
  $recoverSql = @"
SELECT * FROM agentcore.recover_expired_work();
SELECT status, count(*) FROM agentcore.work_queue
WHERE dedupe_key IN ('recover-$runId', 'dead-$runId')
GROUP BY status ORDER BY status;
SELECT count(*) FROM agentcore.dead_letters dl
JOIN agentcore.work_queue q ON q.id = dl.work_item_id
WHERE q.dedupe_key = 'dead-$runId';
SELECT status, count(*) FROM agentcore.capability_leases
WHERE tool_name = 'dummy.tool' AND step_id = 'M2.Q1-$runId'
GROUP BY status;
SELECT count(*) FROM agentcore.work_queue
WHERE dedupe_key IN ('recover-$runId', 'dead-$runId');
SELECT count(*) FROM agentcore.work_claims
WHERE status = 'active';
"@
  $recoverOut = Invoke-Psql $recoverSql -TupleOnly
  $recoverEvidence = Join-Path $evidencePath "queue-restart-recovery-output.txt"
  $recoverOut | Set-Content -LiteralPath $recoverEvidence -Encoding utf8
  $recoverLines = @($recoverOut -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  $hasPending = $recoverLines -contains "pending|1"
  $hasDead = $recoverLines -contains "dead|1"
  $deadLetterCount = @($recoverLines | Where-Object { $_ -eq "1" }).Count -ge 1
  $hasExpiredLease = $recoverLines -contains "expired|1"
  $totalQueueCount = $recoverLines -contains "2"
  $noActiveClaims = $recoverLines[-1] -eq "0"
  if (-not ($hasPending -and $hasDead -and $deadLetterCount -and $hasExpiredLease -and $totalQueueCount -and $noActiveClaims)) {
    throw "queue/lease/dead-letter restart recovery did not produce expected statuses: $recoverOut"
  }
  Add-Check "queue claim lease dead-letter restart recovery" "PASS" "controlled PG18 restart; pending=1, dead=1, dead_letters=1, expired_leases=1; evidence=$recoverEvidence"

  # 8. IDE configs do not expose DB credentials.
  $idePaths = @(
    "C:\Users\ynotf\.cursor\mcp.json",
    "C:\Users\ynotf\.codex\config.toml",
    "C:\Users\ynotf\.claude.json",
    "C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json",
    "C:\Users\ynotf\.minimax\mcp\mcp.json",
    "C:\Users\ynotf\.mavis\mcp\mcp.json",
    "C:\Users\ynotf\.gemini\config\mcp_config.json",
    "C:\Users\ynotf\AppData\Roaming\interpreter\config.json"
  )
  $hits = @()
  foreach ($path in $idePaths) {
    if (Test-Path $path) {
      $text = Get-Content -LiteralPath $path -Raw -ErrorAction SilentlyContinue
      if ($text -match "PGPASSWORD|postgresql://|agentcore_(read|ingest|worker|admin|backup|cognee)") {
        $hits += $path
      }
    }
  }
  if ($hits.Count -gt 0) { throw "IDE configs expose DB credential markers: $($hits -join ', ')" }
  Add-Check "no IDE database credentials" "PASS" "live managed IDE config files contain no PostgreSQL credential markers"

  $summary.completed_at = (Get-Date).ToUniversalTime().ToString("o")
  $summary.result = "PASS"
  $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $evidencePath "m2-acceptance-summary.json") -Encoding utf8
  $summary.checks | ForEach-Object { "{0}: {1} - {2}" -f $_.name, $_.result, $_.detail } |
    Set-Content -LiteralPath (Join-Path $evidencePath "m2-acceptance-summary.txt") -Encoding utf8
  Write-Output "PASS: M2 acceptance checks completed"
  Write-Output (Join-Path $evidencePath "m2-acceptance-summary.json")
}
catch {
  $summary.completed_at = (Get-Date).ToUniversalTime().ToString("o")
  $summary.result = "FAIL"
  $summary.error = $_.Exception.Message
  $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $evidencePath "m2-acceptance-summary.json") -Encoding utf8
  Write-Error $_
  exit 1
}
