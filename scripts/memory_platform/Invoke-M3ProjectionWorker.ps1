param(
  [string]$PgRoot = "F:\PostgreSQL18",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55433,
  [string]$Database = "agent_core",
  [string]$AdminUser = "postgres",
  [string]$ProjectKey,
  [string]$ProjectRoot = "D:\github\agentcore-control-plane",
  [string]$GlobalStatePath = "C:\Users\ynotf\.agentcore\GLOBAL_STATE.md",
  [switch]$SimulateAtomicFailure
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$pgBin = Join-Path $PgRoot "bin"
$psql = Join-Path $pgBin "psql.exe"
if (-not (Test-Path $psql)) { throw "psql not found at $psql" }

$env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
$env:PGSSLMODE = "require"
if (-not $env:PGPASSWORD) { throw "AGENT_CORE_POSTGRES_PASSWORD is not available in Windows User env" }

function Invoke-PsqlValue {
  param([string]$Sql)
  $tmp = Join-Path $env:TEMP ("agentcore-proj-{0}.sql" -f ([guid]::NewGuid().ToString("N")))
  $Sql | Set-Content -LiteralPath $tmp -Encoding utf8
  $old = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & $psql -h $HostName -p $Port -U $AdminUser -d $Database -t -A -v ON_ERROR_STOP=1 -f $tmp 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $old
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  }
  if ($code -ne 0) { throw "psql failed ($code): $($out -join "`n")" }
  return (($out | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Get-Sha256Text {
  param([string]$Text)
  $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
  return [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
}

function Write-ProjectionAtomic {
  param(
    [string]$Path,
    [string]$Content
  )
  $dir = Split-Path -Parent $Path
  New-Item -ItemType Directory -Path $dir -Force | Out-Null
  $tmp = "$Path.tmp"
  $prev = "$Path.previous"
  $Content | Set-Content -LiteralPath $tmp -Encoding utf8 -NoNewline
  if ($SimulateAtomicFailure) {
    throw "Simulated projection failure after temp write before replace: $tmp"
  }
  if (Test-Path -LiteralPath $Path) {
    Copy-Item -LiteralPath $Path -Destination $prev -Force
  }
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}

$projectWhere = if ($ProjectKey) {
  "WHERE project_key = '$($ProjectKey.Replace("'", "''"))'"
} else {
  "ORDER BY created_at DESC LIMIT 1"
}

$projectJson = Invoke-PsqlValue @"
SELECT jsonb_build_object(
  'project_id', id,
  'project_key', project_key,
  'project_name', project_name,
  'root_path', root_path,
  'current_milestone', current_milestone,
  'created_at', created_at
)::text
FROM agentcore.projects
$projectWhere;
"@
if (-not $projectJson) { throw "No project found for projection" }
$project = $projectJson | ConvertFrom-Json
$ProjectKey = $project.project_key
$projectId = [string]$project.project_id

$sourceRevision = Invoke-PsqlValue @"
SELECT coalesce(max(created_at)::text, 'no-events')
FROM (
  SELECT created_at FROM agentcore.evidence_events WHERE project_id = '$projectId'
  UNION ALL
  SELECT created_at FROM agentcore.context_summaries WHERE project_id = '$projectId'
  UNION ALL
  SELECT created_at FROM agentcore.fact_proposals WHERE project_id = '$projectId'
) s;
"@

$statsJson = Invoke-PsqlValue @"
SELECT jsonb_build_object(
  'events', (SELECT count(*) FROM agentcore.evidence_events WHERE project_id = '$projectId'),
  'summaries', (SELECT count(*) FROM agentcore.context_summaries WHERE project_id = '$projectId'),
  'l0', (SELECT count(*) FROM agentcore.evidence_events WHERE project_id = '$projectId'),
  'l1', (SELECT count(*) FROM agentcore.context_summaries WHERE project_id = '$projectId' AND level = 'L1'),
  'l2', (SELECT count(*) FROM agentcore.context_summaries WHERE project_id = '$projectId' AND level = 'L2'),
  'l3', (SELECT count(*) FROM agentcore.context_summaries WHERE project_id = '$projectId' AND level = 'L3'),
  'proposals', (SELECT count(*) FROM agentcore.fact_proposals WHERE project_id = '$projectId' AND status = 'proposed')
)::text;
"@
$stats = $statsJson | ConvertFrom-Json

$decisionsText = Invoke-PsqlValue @"
SELECT coalesce(string_agg('- ' || payload::text, E'\n' ORDER BY accepted_at), '- No decisions recorded.')
FROM agentcore.evidence_events
WHERE project_id = '$projectId'
  AND event_kind = 'decision';
"@

$contextIndex = Invoke-PsqlValue @"
SELECT coalesce(string_agg(
  '- ' || level::text || ' [' || bucket::text || '] ' || title || ' — ' ||
  left(summary_sha256, 12) || ' tokens=' || token_count::text,
  E'\n' ORDER BY level, created_at
), '- No summaries recorded.')
FROM agentcore.context_summaries
WHERE project_id = '$projectId';
"@

$timeline = Invoke-PsqlValue @"
SELECT coalesce(string_agg(
  '- ' || to_char(accepted_at AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI:SS') || 'Z ' ||
  event_kind::text || ' ' || left(id::text, 8),
  E'\n' ORDER BY accepted_at
), '- No events recorded.')
FROM agentcore.evidence_events
WHERE project_id = '$projectId';
"@

$header = @"
<!-- Generated by Invoke-M3ProjectionWorker.ps1. PostgreSQL is canonical; do not hand-edit. -->
<!-- project_key=$ProjectKey project_id=$projectId source_revision=$sourceRevision -->
"@

$projectStateBody = @"
$header
# STATE — $($project.project_name)

Project key: `$ProjectKey`
Current Milestone: `$($project.current_milestone)`
Source revision: `$sourceRevision`

## Current Truth

- PostgreSQL is canonical.
- Agents contribute through `agentcore-memory`; STATE files are generated projections.
- Active context and stable/static context are separated by `context_bucket`.

## Counts

- L0 raw accepted events: $($stats.l0)
- L1 event-span summaries: $($stats.l1)
- L2 session summaries: $($stats.l2)
- L3 project chronology summaries: $($stats.l3)
- Open fact proposals: $($stats.proposals)

## Recent Chronology

$timeline
"@
$projectStateHash = Get-Sha256Text $projectStateBody
$projectState = "$projectStateBody`n`nContent SHA-256: `$projectStateHash`n"

$decisionsBody = @"
$header
# DECISIONS — $($project.project_name)

$decisionsText
"@
$decisionsHash = Get-Sha256Text $decisionsBody
$decisions = "$decisionsBody`n`nContent SHA-256: `$decisionsHash`n"

$contextBody = @"
$header
# CONTEXT INDEX — $($project.project_name)

## Summary Index

$contextIndex
"@
$contextHash = Get-Sha256Text $contextBody
$context = "$contextBody`n`nContent SHA-256: `$contextHash`n"

$globalBody = @"
<!-- Generated by Invoke-M3ProjectionWorker.ps1. PostgreSQL is canonical; do not hand-edit. -->
<!-- source_revision=$sourceRevision -->
# GLOBAL_STATE — AgentCore

## Active Project Snapshot

- Project: $($project.project_name) (`$ProjectKey`)
- Project ID: `$projectId`
- Current Milestone: `$($project.current_milestone)`
- Events: $($stats.events)
- Summaries: $($stats.summaries)

## Authority

Read order: PROJECT_ANCHOR.md -> DOC_AUTHORITY.md -> BLUEPRINT.md -> CONTEXT_BLOCK.md -> docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md.
"@
$globalHash = Get-Sha256Text $globalBody
$global = "$globalBody`n`nContent SHA-256: `$globalHash`n"

$projectAgentCore = Join-Path $ProjectRoot ".agentcore"
$paths = [ordered]@{
  global_state = $GlobalStatePath
  project_state = (Join-Path $projectAgentCore "STATE.md")
  decisions = (Join-Path $projectAgentCore "DECISIONS.md")
  context_index = (Join-Path $projectAgentCore "CONTEXT_INDEX.md")
}

Write-ProjectionAtomic -Path $paths.global_state -Content $global
Write-ProjectionAtomic -Path $paths.project_state -Content $projectState
Write-ProjectionAtomic -Path $paths.decisions -Content $decisions
Write-ProjectionAtomic -Path $paths.context_index -Content $context

$records = @(
  @{ kind = "global_state"; path = $paths.global_state; hash = $globalHash; project = "NULL" },
  @{ kind = "project_state"; path = $paths.project_state; hash = $projectStateHash; project = "'$projectId'" },
  @{ kind = "decisions"; path = $paths.decisions; hash = $decisionsHash; project = "'$projectId'" },
  @{ kind = "context_index"; path = $paths.context_index; hash = $contextHash; project = "'$projectId'" }
)
foreach ($record in $records) {
  $safePath = $record.path.Replace("'", "''")
  $sql = "SELECT agentcore.record_projection_revision($($record.project), '$($record.kind)', '$safePath', '$($record.hash)', '$($sourceRevision.Replace("'", "''"))');"
  Invoke-PsqlValue $sql | Out-Null
}

[pscustomobject]@{
  project_key = $ProjectKey
  project_id = $projectId
  source_revision = $sourceRevision
  paths = $paths
  hashes = [ordered]@{
    global_state = $globalHash
    project_state = $projectStateHash
    decisions = $decisionsHash
    context_index = $contextHash
  }
} | ConvertTo-Json -Depth 8
