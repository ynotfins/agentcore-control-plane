<#
.SYNOPSIS
  Read-only structural gate for Sally/SwarmClaw acceptance reports.

.DESCRIPTION
  This script does not validate Swarm internals directly and does not mutate any
  Swarm, AgentCore, Bifrost, LangGraph, IDE, database, or runtime state. It only
  checks that a Sally final acceptance report contains the minimum evidence
  categories needed before AgentCore can use it as an external Swarm acceptance
  artifact.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Path,
  [switch]$Json,
  [switch]$AllowPlaceholders
)

$ErrorActionPreference = 'Stop'

$results = [System.Collections.Generic.List[object]]::new()

function Add-EvidenceResult {
  param(
    [ValidateSet('PASS', 'FAIL')]
    [string]$Status,
    [string]$Name,
    [string]$Detail
  )
  $results.Add([pscustomobject]@{
    status = $Status
    name = $Name
    detail = $Detail
  }) | Out-Null
}

function Test-TextAny {
  param(
    [string]$Text,
    [string[]]$Patterns
  )
  foreach ($pattern in $Patterns) {
    if ($Text -match $pattern) {
      return $true
    }
  }
  return $false
}

function Test-RequiredEvidence {
  param(
    [string]$Name,
    [string]$Text,
    [string[]]$Patterns,
    [string]$FailureDetail
  )
  foreach ($pattern in $Patterns) {
    if ($Text -notmatch $pattern) {
      Add-EvidenceResult 'FAIL' $Name $FailureDetail
      return
    }
  }
  Add-EvidenceResult 'PASS' $Name 'required marker set present'
}

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
  Add-EvidenceResult 'FAIL' 'report_file' "missing: $Path"
} else {
  Add-EvidenceResult 'PASS' 'report_file' "exists: $Path"
}

$content = ''
if (Test-Path -LiteralPath $Path -PathType Leaf) {
  $content = Get-Content -Raw -LiteralPath $Path
}

$trimmed = $content.Trim()
if ([string]::IsNullOrWhiteSpace($trimmed)) {
  Add-EvidenceResult 'FAIL' 'report_not_empty' 'report is empty'
} else {
  Add-EvidenceResult 'PASS' 'report_not_empty' ("chars={0}" -f $trimmed.Length)
}

if ($trimmed -match '^\s*ORCHESTRATOR_OK\s*$') {
  Add-EvidenceResult 'FAIL' 'orchestrator_ok_only' 'ORCHESTRATOR_OK alone is health evidence, not full acceptance'
} else {
  Add-EvidenceResult 'PASS' 'orchestrator_ok_only' 'report contains more than ORCHESTRATOR_OK'
}

$secretPatterns = @(
  'sk-[A-Za-z0-9_-]{20,}',
  '(?i)\b(BIFROST_MCP_VIRTUAL_KEY|MEILI_MASTER_KEY|SWARMRECALL_API_KEY|AGENTCORE_RECALL_API_KEY|POSTGRES_PASSWORD)\b\s*[:=]\s*\S+',
  '(?i)\bBearer\s+[A-Za-z0-9._~+/-]{20,}'
)

if (Test-TextAny $content $secretPatterns) {
  Add-EvidenceResult 'FAIL' 'secret_scan' 'obvious secret/token literal pattern present'
} else {
  Add-EvidenceResult 'PASS' 'secret_scan' 'no obvious secret/token literal pattern'
}

if ($content -match '\[[^\]\r\n]{1,120}\](?!\()') {
  if ($AllowPlaceholders) {
    Add-EvidenceResult 'PASS' 'unresolved_placeholders' 'placeholder text allowed for template validation'
  } else {
    Add-EvidenceResult 'FAIL' 'unresolved_placeholders' 'unresolved bracketed placeholder text present'
  }
} else {
  Add-EvidenceResult 'PASS' 'unresolved_placeholders' 'no unresolved bracketed placeholders'
}

Test-RequiredEvidence 'timestamp' $content @(
  '(?i)\b(timestamp|time|date)\b',
  '\b20\d\d[-/]\d\d[-/]\d\d(?:\b|T)'
) 'missing explicit timestamp/date evidence'

Test-RequiredEvidence 'versions' $content @(
  '(?i)\bSwarmClaw\b.*\b(version|v\d)',
  '(?i)\bSwarmRecall\b.*\b(version|v\d)',
  '(?i)\bSwarmVault\b.*\b(version|v\d)'
) 'missing SwarmClaw/SwarmRecall/SwarmVault version evidence'

Test-RequiredEvidence 'storage_roots' $content @(
  '(?i)H:\\SwarmData',
  '(?i)H:\\SwarmRuntime',
  '(?i)E:\\SwarmBackups'
) 'missing approved H/E Swarm storage root evidence'

Test-RequiredEvidence 'service_table' $content @(
  '(?i)\b(service table|services|endpoints)\b',
  '(?i)\bSwarmClaw\b',
  '(?i)\bSwarmRecall\b',
  '(?i)\bSwarmVault\b',
  '(?i)\bMeilisearch\b',
  '(?i)\b(PostgreSQL|listener|65432)\b'
) 'missing complete Swarm service/endpoints evidence'

Test-RequiredEvidence 'swarmrecall_canary' $content @(
  '(?i)\bSwarmRecall\b',
  '(?i)\bcanary\b',
  '(?i)\b(write|POST|create)\b',
  '(?i)\b(read|GET|retrieve)\b',
  '(?i)\b(search|exact match|matched)\b'
) 'missing SwarmRecall write/read/search canary evidence'

Test-RequiredEvidence 'swarmvault_canary' $content @(
  '(?i)\bSwarmVault\b',
  '(?i)\b(search|context[- ]pack)\b',
  '(?i)\b(corpus|source count|sources|tokens?)\b'
) 'missing SwarmVault search/context-pack evidence'

Test-RequiredEvidence 'autonomous_team_canary' $content @(
  '(?i)\b(autonomous team|delegated team|team canary|Builder|QA|Reviewer)\b',
  '(?i)\b(task|delegation|created)\b',
  '(?i)\b(result|review|complete|completed)\b'
) 'missing autonomous team delegation/review/completion evidence'

Test-RequiredEvidence 'no_cross_write_boundary' $content @(
  '(?i)\b(no[- ]cross[- ]write|no writes|not touched|intentionally not touched)\b',
  '(?i)\bAgentCore\b',
  '(?i)\bBifrost\b',
  '(?i)\bLangGraph\b',
  '(?i)\bIDE\b'
) 'missing no-cross-write boundary evidence for AgentCore/Bifrost/LangGraph/IDE'

Test-RequiredEvidence 'changed_files' $content @(
  '(?i)\b(files changed|changed files|exact files changed)\b',
  '(?i)\b(files intentionally not touched|intentionally not touched|not touched)\b'
) 'missing changed/not-touched file inventory'

Test-RequiredEvidence 'backup_restore' $content @(
  '(?i)\b(backup|restore point|restore-point)\b',
  '(?i)\b(path|files|readable)\b'
) 'missing backup/restore-point evidence'

Test-RequiredEvidence 'final_status' $content @(
  '(?i)\b(final status|status)\b',
  '(?i)\b(PASS|PARTIAL|FAIL)\b'
) 'missing explicit final PASS/PARTIAL/FAIL status'

$failCount = @($results | Where-Object { $_.status -eq 'FAIL' }).Count
$passCount = @($results | Where-Object { $_.status -eq 'PASS' }).Count

if ($Json) {
  [pscustomobject]@{
    status = if ($failCount -eq 0) { 'READY' } else { 'NOT_READY' }
    pass = $passCount
    fail = $failCount
    results = @($results)
  } | ConvertTo-Json -Depth 6
} else {
  foreach ($result in $results) {
    Write-Host ("{0}  {1}: {2}" -f $result.status.PadRight(4), $result.name, $result.detail)
  }
  Write-Host ("SUMMARY status={0} pass={1} fail={2}" -f $(if ($failCount -eq 0) { 'READY' } else { 'NOT_READY' }), $passCount, $failCount)
}

if ($failCount -gt 0) {
  exit 1
}
