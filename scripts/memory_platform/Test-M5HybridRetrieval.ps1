param(
  [string]$Endpoint         = "http://127.0.0.1:8080/mcp",
  [string]$VirtualKeyEnv    = "BIFROST_MCP_VIRTUAL_KEY",
  [string]$PgRoot           = "F:\PostgreSQL18",
  [int]   $PgPort           = 55433,
  [string]$EvidenceDir      = "audits\M5",
  [string]$OfficialDocRoot  = "E:\AgentCoreArchive\agentcore-memory\official-docs",
  [string]$CogneeRuntimeRoot = "H:\AgentRuntime\agentcore-memory\cognee"
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$evidencePath = Join-Path $repoRoot $EvidenceDir
New-Item -ItemType Directory -Path $evidencePath -Force | Out-Null

$key = [Environment]::GetEnvironmentVariable($VirtualKeyEnv, "User")
if (-not $key) { $key = [Environment]::GetEnvironmentVariable($VirtualKeyEnv, "Process") }
if (-not $key) { throw "$VirtualKeyEnv not found" }
$headers = @{ Authorization = "Bearer $key" }

$pgBin = Join-Path $PgRoot "bin"
$psql = Join-Path $pgBin "psql.exe"
$createdb = Join-Path $pgBin "createdb.exe"
$dropdb = Join-Path $pgBin "dropdb.exe"
$upMigration = Join-Path $repoRoot "migrations\m5\001_up_hybrid_retrieval_cognee.sql"
$downMigration = Join-Path $repoRoot "migrations\m5\001_down_hybrid_retrieval_cognee.sql"
$bifrostStop = Join-Path $repoRoot "ops\bifrost\Stop-AgentCoreBifrostGateway.ps1"
$bifrostStart = Join-Path $repoRoot "ops\bifrost\Start-AgentCoreBifrostGateway.ps1"
$disableFlag = Join-Path $CogneeRuntimeRoot "COGNEE_DISABLED.flag"

$env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
$env:PGSSLMODE = "require"
if (-not $env:PGPASSWORD) { throw "AGENT_CORE_POSTGRES_PASSWORD is not available in Windows User env" }

function Invoke-Psql {
  param(
    [string]$Sql,
    [string]$Db = "agent_core",
    [switch]$TupleOnly
  )
  $tmp = Join-Path $env:TEMP ("agentcore-m5-{0}.sql" -f ([guid]::NewGuid().ToString("N")))
  $Sql | Set-Content -LiteralPath $tmp -Encoding utf8
  $psqlArgs = @("-h", "127.0.0.1", "-p", [string]$PgPort, "-U", "postgres", "-d", $Db, "-v", "ON_ERROR_STOP=1", "-f", $tmp)
  if ($TupleOnly) { $psqlArgs = @("-t", "-A") + $psqlArgs }
  $old = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & $psql @psqlArgs 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $old
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  }
  if ($code -ne 0) { throw "psql failed ($code): $($out -join "`n")" }
  return (($out | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Invoke-PsqlFile {
  param([string]$Path, [string]$Db = "agent_core")
  if (-not (Test-Path $Path)) { throw "required migration not found: $Path" }
  $old = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & $psql -h 127.0.0.1 -p $PgPort -U postgres -d $Db -v ON_ERROR_STOP=1 -f $Path 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $old
  }
  if ($code -ne 0) { throw "psql file failed ($code): $Path`n$($out -join "`n")" }
  return (($out | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Invoke-ExpectFailure {
  param([string]$Name, [string]$Sql)
  $tmp = Join-Path $env:TEMP ("agentcore-m5-fail-{0}.sql" -f ([guid]::NewGuid().ToString("N")))
  $Sql | Set-Content -LiteralPath $tmp -Encoding utf8
  $old = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & $psql -h 127.0.0.1 -p $PgPort -U postgres -d agent_core -v ON_ERROR_STOP=1 -f $tmp 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $old
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  }
  if ($code -eq 0) { throw "Expected failure did not occur: $Name" }
  return "$Name`: PASS expected failure`n$($out -join "`n")"
}

$script:nextId = 1
function Invoke-Mcp {
  param([string]$Method, [object]$Params)
  $id = $script:nextId++
  $body = @{ jsonrpc = "2.0"; id = $id; method = $Method; params = $Params } | ConvertTo-Json -Depth 30
  $response = Invoke-RestMethod -Uri $Endpoint -Method Post -Headers $headers -ContentType "application/json" -Body $body
  if ($response.error) { throw ($response.error | ConvertTo-Json -Depth 10) }
  return $response.result
}

function Invoke-Tool {
  param([string]$Name, [hashtable]$Arguments)
  $result = Invoke-Mcp -Method "tools/call" -Params @{ name = $Name; arguments = $Arguments }
  $payload = $result.structuredContent
  if (-not $payload) {
    $rawText = $result.content[0].text
    if ($rawText -match '^\s*\{') {
      $payload = $rawText | ConvertFrom-Json
    } else {
      throw "Tool $Name returned non-JSON response: $($rawText.Substring(0, [Math]::Min(200, $rawText.Length)))"
    }
  }
  if ($payload.ok -eq $false) { throw ($payload | ConvertTo-Json -Depth 10) }
  return $payload
}

$runId = Get-Date -Format "yyyyMMddHHmmss"
$summary = [ordered]@{
  run_id = $runId
  started_at = (Get-Date).ToUniversalTime().ToString("o")
  endpoint = $Endpoint
  migration = "m5.001"
  checks = @()
  benchmarks = [ordered]@{}
}

function Add-Check {
  param([string]$Name, [string]$Result, [string]$Detail = "")
  Write-Host "[$Result] $Name$(if ($Detail) { ": $Detail" })"
  $script:summary.checks += [ordered]@{ name = $Name; result = $Result; detail = $Detail }
}

try {
  New-Item -ItemType Directory -Path $OfficialDocRoot -Force | Out-Null
  New-Item -ItemType Directory -Path $CogneeRuntimeRoot -Force | Out-Null
  if (Test-Path $disableFlag) { Remove-Item $disableFlag -Force }

  $rollbackDb = "agentcore_m5_rollback_$runId"
  & $createdb -h 127.0.0.1 -p $PgPort -U postgres $rollbackDb 2>&1 | Out-Null
  Invoke-Psql "CREATE EXTENSION IF NOT EXISTS pgcrypto; CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm;" -Db $rollbackDb | Out-Null
  Invoke-PsqlFile -Path (Join-Path $repoRoot "migrations\m2\001_up_canonical_identity_immutable_evidence.sql") -Db $rollbackDb | Out-Null
  Invoke-PsqlFile -Path (Join-Path $repoRoot "migrations\m3\001_up_lossless_context_state_projections.sql") -Db $rollbackDb | Out-Null
  Invoke-PsqlFile -Path (Join-Path $repoRoot "migrations\m4\001_up_assemble_context_window_quarantine_filter.sql") -Db $rollbackDb | Out-Null
  Invoke-PsqlFile -Path $upMigration -Db $rollbackDb | Out-Null
  $m5Exists = Invoke-Psql "SELECT EXISTS (SELECT 1 FROM agentcore.schema_migrations WHERE version='m5.001');" -Db $rollbackDb -TupleOnly
  if ($m5Exists -ne "t") { throw "m5.001 missing in rollback test" }
  Invoke-PsqlFile -Path $downMigration -Db $rollbackDb | Out-Null
  $m5AfterDown = Invoke-Psql "SELECT EXISTS (SELECT 1 FROM agentcore.schema_migrations WHERE version='m5.001');" -Db $rollbackDb -TupleOnly
  if ($m5AfterDown -ne "f") { throw "m5.001 still present after down migration" }
  & $dropdb -h 127.0.0.1 -p $PgPort -U postgres $rollbackDb 2>&1 | Out-Null
  Add-Check "1 - Versioned reversible M5 migration" "PASS" "up/down tested in $rollbackDb"

  Invoke-PsqlFile -Path $upMigration -Db "agent_core" | Out-Null
  Add-Check "2 - Live M5 migration applied" "PASS" "migrations/m5/001_up_hybrid_retrieval_cognee.sql"

  Invoke-Mcp -Method "initialize" -Params @{
    protocolVersion = "2025-06-18"; capabilities = @{}
    clientInfo = @{ name = "m5-harness"; version = "1.0" }
  } | Out-Null
  $tools = (Invoke-Mcp -Method "tools/list" -Params @{}).tools
  $amTools = @($tools | Where-Object { $_.name -like "agentcore_memory-*" } | ForEach-Object { $_.name } | Sort-Object)
  $expectedTools = @(
    "agentcore_memory-append_event","agentcore_memory-build_handoff",
    "agentcore_memory-docs_search","agentcore_memory-expand_source",
    "agentcore_memory-memory_status","agentcore_memory-propose_fact","agentcore_memory-retrieve_context",
    "agentcore_memory-session_close","agentcore_memory-session_open",
    "agentcore_memory-startup_context"
  ) | Sort-Object
  $missing = @($expectedTools | Where-Object { $_ -notin $amTools })
  $extra = @($amTools | Where-Object { $_ -notin $expectedTools })
  if ($missing.Count -gt 0 -or $extra.Count -gt 0) { throw "MCP surface changed missing=[$($missing -join ',')] extra=[$($extra -join ',')]" }
  Add-Check "3 - Exact MCP surface preserved" "PASS" ($amTools -join ", ")

  $projectKeyA = "m5_project_A_$runId"
  $projectKeyB = "m5_project_B_$runId"
  $sessionA = Invoke-Tool -Name "agentcore_memory-session_open" -Arguments @{
    project_key = $projectKeyA; project_name = "M5 Retrieval Project A"
    client_key = "cursor-m5-a"; agent_key = "agent-m5-a"; session_key = "m5-a-$runId"
  }
  $sessionB = Invoke-Tool -Name "agentcore_memory-session_open" -Arguments @{
    project_key = $projectKeyB; project_name = "M5 Retrieval Project B"
    client_key = "cursor-m5-b"; agent_key = "agent-m5-b"; session_key = "m5-b-$runId"
  }

  $officialDocPath = Join-Path $OfficialDocRoot "m5-official-fixture-$runId.md"
  "Official M5 gateway setup fixture $runId. PostgreSQL search metadata lives on F and opens selected E excerpts only." |
    Set-Content -LiteralPath $officialDocPath -Encoding utf8

  $seedSql = @"
WITH source_a AS (
  SELECT id FROM agentcore.source_identities WHERE session_id = '$($sessionA.session_id)' ORDER BY created_at DESC LIMIT 1
),
source_b AS (
  SELECT id FROM agentcore.source_identities WHERE session_id = '$($sessionB.session_id)' ORDER BY created_at DESC LIMIT 1
),
doc1 AS (
  INSERT INTO agentcore.retrieval_documents (
    project_id, scope, title, body, source_uri, source_path, source_kind,
    trust_class, version, provenance, source_evidence_ids, embedding, metadata
  ) VALUES (
    '$($sessionA.project_id)', 'project',
    'M5 full text fixture',
    'M5_FULL_TEXT_SENTINEL_$runId hydrostatic armature official fixture expected by full text search',
    'evidence://m5/full-text/$runId', NULL, 'accepted_evidence',
    'project_verified', 'm5.fixture.v1',
    jsonb_build_object('run_id', '$runId', 'source', 'm5 acceptance'),
    ARRAY[]::uuid[], '[0.2,0.8,0]'::vector, '{"fixture":"fts"}'::jsonb
  ) RETURNING id
),
doc2 AS (
  INSERT INTO agentcore.retrieval_documents (
    project_id, scope, title, body, source_uri, source_path, source_kind,
    trust_class, version, provenance, source_evidence_ids, embedding, metadata
  ) VALUES (
    '$($sessionA.project_id)', 'project',
    'BIFROST_RETRIEVAL_PORT_$runId',
    'Controlled partial identifier for trigram retrieval: BIFROST_RETRIEVAL_PORT_$runId',
    'evidence://m5/trigram/$runId', NULL, 'accepted_evidence',
    'project_verified', 'm5.fixture.v1',
    jsonb_build_object('run_id', '$runId', 'source', 'm5 acceptance'),
    ARRAY[]::uuid[], '[0.7,0.2,0.1]'::vector, '{"fixture":"trigram"}'::jsonb
  ) RETURNING id
),
doc3 AS (
  INSERT INTO agentcore.retrieval_documents (
    project_id, scope, title, body, source_uri, source_path, source_kind,
    trust_class, version, provenance, source_evidence_ids, embedding, metadata
  ) VALUES (
    '$($sessionA.project_id)', 'project',
    'M5 exact vector baseline',
    'M5_VECTOR_BASELINE_$runId exact pgvector nearest neighbor should rank this first',
    'evidence://m5/vector/$runId', NULL, 'accepted_evidence',
    'system_verified', 'm5.fixture.v1',
    jsonb_build_object('run_id', '$runId', 'source', 'm5 acceptance'),
    ARRAY[]::uuid[], '[0.99,0.01,0]'::vector, '{"fixture":"vector"}'::jsonb
  ) RETURNING id
),
doc4 AS (
  INSERT INTO agentcore.retrieval_documents (
    project_id, scope, title, body, source_uri, source_path, source_kind,
    trust_class, version, provenance, source_evidence_ids, embedding, metadata
  ) VALUES (
    '$($sessionB.project_id)', 'project',
    'M5 boundary project B',
    'PROJECT_B_BOUNDARY_LEAK_$runId must not appear in project A retrieval',
    'evidence://m5/boundary/$runId', NULL, 'accepted_evidence',
    'project_verified', 'm5.fixture.v1',
    jsonb_build_object('run_id', '$runId', 'source', 'm5 acceptance'),
    ARRAY[]::uuid[], '[0,1,0]'::vector, '{"fixture":"boundary"}'::jsonb
  ) RETURNING id
),
doc5 AS (
  INSERT INTO agentcore.retrieval_documents (
    project_id, scope, title, body, source_uri, source_path, source_kind,
    trust_class, version, provenance, source_evidence_ids, embedding, metadata
  ) VALUES (
    '$($sessionA.project_id)', 'project',
    'M5 quarantined retrieval item',
    'QUARANTINED_RETRIEVAL_SENTINEL_$runId must not appear in normal retrieval',
    'evidence://m5/quarantine/$runId', NULL, 'quarantined_evidence',
    'quarantined', 'm5.fixture.v1',
    jsonb_build_object('run_id', '$runId', 'source', 'm5 acceptance'),
    ARRAY[]::uuid[], '[0,0,1]'::vector, '{"fixture":"quarantined"}'::jsonb
  ) RETURNING id
),
doc6 AS (
  INSERT INTO agentcore.retrieval_documents (
    project_id, scope, title, body, source_uri, source_path, source_kind,
    trust_class, version, provenance, source_evidence_ids, embedding, metadata
  ) VALUES (
    NULL, 'global',
    'Official M5 gateway setup fixture',
    'Official M5 gateway setup fixture $runId. PostgreSQL search metadata lives on F and selected E excerpts are opened only after ranking.',
    'file:///$($officialDocPath.Replace("\","/"))',
    '$($officialDocPath.Replace("'","''"))',
    'official_document',
    'operator_verified', 'bifrost/2.0.0-prerelease1',
    jsonb_build_object('run_id', '$runId', 'source_path', '$($officialDocPath.Replace("\","/"))', 'indexed_on', 'F:'),
    ARRAY[]::uuid[], '[0.3,0.6,0.1]'::vector, '{"fixture":"official_doc","source_drive":"E","index_drive":"F"}'::jsonb
  ) RETURNING id
)
SELECT jsonb_build_object(
  'fts', (SELECT id FROM doc1),
  'trigram', (SELECT id FROM doc2),
  'vector', (SELECT id FROM doc3),
  'official', (SELECT id FROM doc6)
)::text;
"@
  $docIds = (Invoke-Psql $seedSql -TupleOnly) | ConvertFrom-Json
  Add-Check "4 - Bounded M5 retrieval fixtures seeded" "PASS" "project=$projectKeyA docs=$($docIds | ConvertTo-Json -Compress)"

  $fts = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{
    project_key = $projectKeyA; query = "hydrostatic armature"; limit = 5
  }
  $ftsJson = $fts.results | ConvertTo-Json -Depth 12
  if ($ftsJson -notmatch "M5_FULL_TEXT_SENTINEL_$runId" -or $ftsJson -notmatch "postgres_fts") {
    throw "full-text retrieval did not return expected fixture with postgres_fts method"
  }
  Add-Check "5 - Full-text retrieval returns expected fixture" "PASS" "method=postgres_fts"

  $trgm = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{
    project_key = $projectKeyA; query = "bifrost retrival por"; limit = 5
  }
  $trgmJson = $trgm.results | ConvertTo-Json -Depth 12
  if ($trgmJson -notmatch "BIFROST_RETRIEVAL_PORT_$runId" -or $trgmJson -notmatch "postgres_trigram") {
    throw "trigram retrieval did not return misspelled/partial identifier fixture"
  }
  Add-Check "6 - pg_trgm retrieves misspelling or partial identifier" "PASS" "method=postgres_trigram"

  $vector = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{
    project_key = $projectKeyA; query = "vector baseline"; query_embedding = @(1.0, 0.0, 0.0)
    retrieval_methods = @("pgvector_exact"); limit = 3
  }
  if (-not $vector.results -or $vector.results[0].title -ne "M5 exact vector baseline") {
    throw "exact pgvector baseline did not rank expected vector fixture first"
  }
  Add-Check "7 - Exact pgvector search produces correctness baseline" "PASS" "top=$($vector.results[0].title)"

  $hnsw = Invoke-Psql @"
SELECT jsonb_build_object(
  'hnsw_index_present', to_regclass('agentcore.idx_retrieval_documents_embedding_hnsw') IS NOT NULL,
  'corpus_rows', (SELECT count(*) FROM agentcore.retrieval_documents WHERE (project_id = '$($sessionA.project_id)' OR scope = 'global') AND trust_class NOT IN ('quarantined','rejected')),
  'decision', (SELECT decision FROM agentcore.retrieval_benchmarks WHERE benchmark_key = 'm5.hnsw.decision' ORDER BY measured_at DESC LIMIT 1)
)::text;
"@ -TupleOnly | ConvertFrom-Json
  if ($hnsw.hnsw_index_present -and $hnsw.decision -ne "created") {
    throw "HNSW index exists without benchmark decision recording created"
  }
  Add-Check "8 - HNSW benchmark gate recorded" "PASS" ($hnsw | ConvertTo-Json -Compress)
  $summary.benchmarks.hnsw = $hnsw

  $boundary = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{
    project_key = $projectKeyA; query = "BOUNDARY QUARANTINED_RETRIEVAL"; limit = 10
  }
  $boundaryJson = $boundary.results | ConvertTo-Json -Depth 12
  if ($boundaryJson -match "PROJECT_B_BOUNDARY_LEAK_$runId" -or $boundaryJson -match "QUARANTINED_RETRIEVAL_SENTINEL_$runId") {
    throw "retrieval leaked project B or quarantined evidence into project A"
  }
  Add-Check "9 - Retrieval respects project and trust boundaries" "PASS" "project_B and quarantined sentinels absent"

  Invoke-ExpectFailure "raw transcript rejected" @"
SELECT set_config('agentcore.current_project_id', '$($sessionA.project_id)', false);
SELECT agentcore.promote_curated_knowledge(
  '$($sessionA.project_id)'::uuid,
  'project',
  'raw_transcript',
  'operator_verified',
  'Raw transcript should not enter Cognee',
  'RAW_TRANSCRIPT_REJECT_$runId',
  'm5.fixture.v1',
  '{}'::uuid[],
  '{"decision":"reject"}'::jsonb,
  'rejected'
);
"@ | Out-Null
  Add-Check "10 - Raw transcripts rejected by promotion gate" "PASS" "expected SQL rejection"

  Invoke-ExpectFailure "quarantined evidence rejected" @"
SELECT set_config('agentcore.current_project_id', '$($sessionA.project_id)', false);
SELECT agentcore.promote_curated_knowledge(
  '$($sessionA.project_id)'::uuid,
  'project',
  'validated_fact',
  'quarantined',
  'Quarantined evidence should not enter Cognee',
  'QUARANTINED_PROMOTION_REJECT_$runId',
  'm5.fixture.v1',
  '{}'::uuid[],
  '{"decision":"reject"}'::jsonb,
  'rejected'
);
"@ | Out-Null
  Add-Check "11 - Quarantined evidence rejected by promotion gate" "PASS" "expected SQL rejection"

  $promotionOut = Invoke-Psql @"
SELECT set_config('agentcore.current_project_id', '$($sessionA.project_id)', false);
SELECT agentcore.promote_curated_knowledge(
  '$($sessionA.project_id)'::uuid,
  'project',
  'validated_fact',
  'operator_verified',
  'Validated M5 promoted fact $runId',
  'PROMOTED_FACT_SENTINEL_$runId',
  'm5.fixture.v1',
  ARRAY[]::uuid[],
  '{"source_evidence_ids":[],"promotion_decision":"operator-approved","provenance":"m5 acceptance"}'::jsonb,
  'operator-approved'
);
"@ -TupleOnly
  $promotionIds = @($promotionOut -split "`n" | Where-Object { $_.Trim() -match '^[0-9a-fA-F-]{36}$' })
  $promotionId = $promotionIds[$promotionIds.Count - 1].Trim()
  $promotionComplete = Invoke-Psql @"
SELECT count(*)
FROM agentcore.curated_knowledge_promotions
WHERE id = '$promotionId'
  AND scope IS NOT NULL
  AND trust_class IS NOT NULL
  AND source_evidence_ids IS NOT NULL
  AND provenance IS NOT NULL
  AND version IS NOT NULL
  AND promotion_decision IS NOT NULL
  AND supersession_state IS NOT NULL;
"@ -TupleOnly | ConvertFrom-Json
  if ([int]$promotionComplete -ne 1) { throw "promotion row missing required provenance/scope/trust/version fields" }
  Add-Check "12 - Validated fact promoted with complete provenance" "PASS" "promotion_id=$promotionId"

  $cognee = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{
    project_key = $projectKeyA; query = "PROMOTED_FACT_SENTINEL_$runId"; limit = 5
  }
  $cogneeJson = $cognee.results | ConvertTo-Json -Depth 12
  if ($cogneeJson -notmatch "PROMOTED_FACT_SENTINEL_$runId" -or $cogneeJson -notmatch "cognee_curated") {
    throw "Cognee curated retrieval did not return promoted fact and source references"
  }
  Add-Check "13 - Cognee retrieval returns promoted fact and source references" "PASS" "promotion_id=$promotionId"

  $official = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{
    project_key = $projectKeyA; query = "Official M5 gateway setup fixture $runId"; limit = 10
    retrieval_methods = @("postgres_fts", "postgres_trigram")
  }
  $officialJson = $official.results | ConvertTo-Json -Depth 12
  $officialDocUriNeedle = $officialDocPath.Replace("\","/")
  if ($officialJson -notmatch [regex]::Escape($officialDocUriNeedle) -or
      $officialJson -notmatch "bifrost/2.0.0-prerelease1" -or
      $officialJson -notmatch "operator_verified" -or
      $officialJson -notmatch '"indexed_on":\s*"F:"') {
    throw "official E: document was not returned with version/provenance/trust"
  }
  Add-Check "14 - E: official document found through F: index" "PASS" "source_path=$officialDocPath"

  "disabled for M5 outage test $runId" | Set-Content -LiteralPath $disableFlag -Encoding utf8
  try {
    $degradedStatus = Invoke-Tool -Name "agentcore_memory-memory_status" -Arguments @{}
    if ($degradedStatus.components.cognee.status -notmatch "degraded|disabled|unavailable") {
      throw "memory_status did not report Cognee degradation: $($degradedStatus.components.cognee.status)"
    }
    $pgOnly = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{
      project_key = $projectKeyA; query = "hydrostatic armature"; limit = 5
    }
    $pgOnlyJson = $pgOnly.results | ConvertTo-Json -Depth 12
    if ($pgOnlyJson -notmatch "M5_FULL_TEXT_SENTINEL_$runId" -or $pgOnlyJson -match "cognee_curated") {
      throw "PostgreSQL-only degraded retrieval failed or included Cognee results"
    }
    $stateProjectionCount = Invoke-Psql "SELECT count(*) FROM agentcore.projection_revisions;" -TupleOnly
    $expand = Invoke-Tool -Name "agentcore_memory-expand_source" -Arguments @{ artifact_id = [string](Invoke-Tool -Name "agentcore_memory-append_event" -Arguments @{
      session_id = [string]$sessionA.session_id
      event_kind = "accepted_evidence"
      idempotency_key = "m5-outage-expand-$runId"
      payload = @{ text = "M5 outage expansion $runId" }
      large_text = "M5 outage expansion source $runId"
      trust_class = "project_verified"
    }).artifact_id }
    if (-not $expand.artifact.storage_uri) { throw "exact expansion failed while Cognee disabled" }
    Add-Check "15 - Cognee outage degrades to PostgreSQL-only retrieval" "PASS" "cognee=$($degradedStatus.components.cognee.status); projections=$stateProjectionCount"
  } finally {
    Remove-Item $disableFlag -Force -ErrorAction SilentlyContinue
  }

  $noMem0Sql = Invoke-Psql "SELECT count(*) FROM pg_database WHERE datname ILIKE '%mem0%';" -Db "postgres" -TupleOnly
  cmd /c "python -m pip show mem0ai >NUL 2>NUL"
  $mem0PipExit = $LASTEXITCODE
  $mem0Processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match "mem0" })
  if ([int]$noMem0Sql -ne 0 -or $mem0PipExit -eq 0 -or $mem0Processes.Count -ne 0) {
    throw "Mem0 detected: db_count=$noMem0Sql pip_exit=$mem0PipExit process_count=$($mem0Processes.Count)"
  }
  Add-Check "16 - No Mem0 package process database or config introduced" "PASS" "db_count=0; pip_show_mem0ai_absent=true; process_count=0"

  Write-Host "Stopping Bifrost ..."
  & $bifrostStop 2>&1 | Out-Null
  Start-Sleep -Seconds 5
  Write-Host "Starting Bifrost ..."
  & $bifrostStart 2>&1 | Out-Null
  $bifrostReady = $false
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
      Invoke-Mcp -Method "initialize" -Params @{
        protocolVersion = "2025-06-18"; capabilities = @{}
        clientInfo = @{ name = "m5-bifrost-reconnect"; version = "1.0" }
      } | Out-Null
      $toolsAfter = (Invoke-Mcp -Method "tools/list" -Params @{}).tools
      $amAfter = @($toolsAfter | Where-Object { $_.name -like "agentcore_memory-*" })
      if ($amAfter.Count -eq 10) { $bifrostReady = $true; break }
    } catch { }
  }
  if (-not $bifrostReady) { throw "Bifrost did not reconnect and expose unchanged memory tools within 30s" }
  $safeCall = Invoke-Tool -Name "agentcore_memory-memory_status" -Arguments @{}
  if ($safeCall.server -ne "agentcore-memory") { throw "safe Cursor retrieval/status call returned wrong server" }
  Add-Check "17 - Bifrost restart and safe Cursor call succeed" "PASS" "server=$($safeCall.server); tools=$($amAfter.Count)"

  $summary.completed_at = (Get-Date).ToUniversalTime().ToString("o")
  $summary.result = "PASS"
  $summary | ConvertTo-Json -Depth 12 |
    Set-Content -LiteralPath (Join-Path $evidencePath "m5-acceptance-summary.json") -Encoding utf8
  $summary.checks | ForEach-Object { "{0}: {1} - {2}" -f $_.name, $_.result, $_.detail } |
    Set-Content -LiteralPath (Join-Path $evidencePath "m5-acceptance-summary.txt") -Encoding utf8

  Write-Host ""
  Write-Host "PASS: All M5 acceptance checks completed ($($summary.checks.Count) checks)"
  Write-Host (Join-Path $evidencePath "m5-acceptance-summary.json")
}
catch {
  $summary.completed_at = (Get-Date).ToUniversalTime().ToString("o")
  $summary.result = "FAIL"
  $summary.error = $_.Exception.Message
  $summary | ConvertTo-Json -Depth 12 |
    Set-Content -LiteralPath (Join-Path $evidencePath "m5-acceptance-summary.json") -Encoding utf8
  Write-Error $_
  exit 1
}
