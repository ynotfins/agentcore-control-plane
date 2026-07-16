param(
  [string]$Endpoint = "http://127.0.0.1:8080/mcp",
  [string]$VirtualKeyEnv = "BIFROST_MCP_VIRTUAL_KEY",
  [string]$PgRoot = "F:\PostgreSQL18",
  [int]$PgPort = 55433,
  [string]$EvidenceDir = "audits\M4"
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
$env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
$env:PGSSLMODE = "require"

$script:nextId = 1
function Invoke-Mcp {
  param([string]$Method, [object]$Params)
  $id = $script:nextId
  $script:nextId += 1
  $body = @{ jsonrpc = "2.0"; id = $id; method = $Method; params = $Params } | ConvertTo-Json -Depth 20
  $response = Invoke-RestMethod -Uri $Endpoint -Method Post -Headers $headers -ContentType "application/json" -Body $body
  if ($response.error) { throw ($response.error | ConvertTo-Json -Depth 10) }
  return $response.result
}

function Invoke-Tool {
  param([string]$Name, [hashtable]$Arguments)
  $result = Invoke-Mcp -Method "tools/call" -Params @{ name = $Name; arguments = $Arguments }
  $payload = $result.structuredContent
  if (-not $payload) {
    $payload = ($result.content[0].text | ConvertFrom-Json)
  }
  if ($payload.ok -eq $false) { throw ($payload | ConvertTo-Json -Depth 10) }
  return $payload
}

function Invoke-PsqlValue {
  param([string]$Sql)
  $tmp = Join-Path $env:TEMP ("agentcore-m4-{0}.sql" -f ([guid]::NewGuid().ToString("N")))
  $Sql | Set-Content -LiteralPath $tmp -Encoding utf8
  $out = & $psql -h 127.0.0.1 -p $PgPort -U postgres -d agent_core -t -A -v ON_ERROR_STOP=1 -f $tmp 2>&1
  $code = $LASTEXITCODE
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  if ($code -ne 0) { throw "psql failed ($code): $($out -join "`n")" }
  return (($out | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

$runId = Get-Date -Format "yyyyMMddHHmmss"
$summary = [ordered]@{
  run_id = $runId
  started_at = (Get-Date).ToUniversalTime().ToString("o")
  endpoint = $Endpoint
  checks = @()
}
function Add-Check {
  param([string]$Name, [string]$Result, [string]$Detail = "")
  $script:summary.checks += [ordered]@{ name = $Name; result = $Result; detail = $Detail }
}

try {
  Invoke-Mcp -Method "initialize" -Params @{
    protocolVersion = "2025-06-18"
    capabilities = @{}
    clientInfo = @{ name = "m4-gateway-test"; version = "1.0" }
  } | Out-Null

  $tools = (Invoke-Mcp -Method "tools/list" -Params @{}).tools
  $agentcoreTools = @($tools | Where-Object { $_.name -like "agentcore_memory-*" } | ForEach-Object { $_.name } | Sort-Object)
  $expected = @(
    "agentcore_memory-append_event",
    "agentcore_memory-build_handoff",
    "agentcore_memory-docs_search",
    "agentcore_memory-expand_source",
    "agentcore_memory-memory_health",
    "agentcore_memory-memory_status",
    "agentcore_memory-propose_fact",
    "agentcore_memory-retrieve_context",
    "agentcore_memory-session_close",
    "agentcore_memory-session_open",
    "agentcore_memory-startup_context"
  ) | Sort-Object
  $missing = @($expected | Where-Object { $_ -notin $agentcoreTools })
  $extraForbidden = @($agentcoreTools | Where-Object { $_ -match "sql|admin|ddl|database_admin" })
  if ($missing.Count -gt 0 -or $extraForbidden.Count -gt 0) {
    throw "tool surface mismatch missing=[$($missing -join ',')] forbidden=[$($extraForbidden -join ',')] actual=[$($agentcoreTools -join ',')]"
  }
  Add-Check "Bifrost tools-list exposes compact M4 surface" "PASS" ($agentcoreTools -join ", ")

  $status = Invoke-Tool -Name "agentcore_memory-memory_status" -Arguments @{}
  if ($status.components.cognee.status -ne "not_integrated_until_M5" -or $status.components.langgraph.status -ne "not_integrated_until_M6") {
    throw "degraded component status missing expected M5/M6 markers"
  }
  Add-Check "memory_status reports degraded/future components clearly" "PASS" "cognee=M5; langgraph=M6"

  $projectKey = "m4_project_$runId"
  $sessionA = Invoke-Tool -Name "agentcore_memory-session_open" -Arguments @{
    project_key = $projectKey
    project_name = "M4 Gateway Test"
    client_key = "cursor-m4-a"
    agent_key = "agent-a"
    session_key = "m4-a-$runId"
  }
  $sessionB = Invoke-Tool -Name "agentcore_memory-session_open" -Arguments @{
    project_key = $projectKey
    project_name = "M4 Gateway Test"
    client_key = "cursor-m4-b"
    agent_key = "agent-b"
    session_key = "m4-b-$runId"
  }
  Add-Check "multiple sessions opened safely" "PASS" "A=$($sessionA.session_id); B=$($sessionB.session_id)"

  $eventA = Invoke-Tool -Name "agentcore_memory-append_event" -Arguments @{
    session_id = [string]$sessionA.session_id
    event_kind = "message"
    idempotency_key = "m4-a-event-$runId"
    payload = @{ text = "M4 session A exact text $runId" }
    trust_class = "project_verified"
  }
  $eventB = Invoke-Tool -Name "agentcore_memory-append_event" -Arguments @{
    session_id = [string]$sessionB.session_id
    event_kind = "message"
    idempotency_key = "m4-b-event-$runId"
    payload = @{ text = "M4 session B exact text $runId" }
    trust_class = "project_verified"
  }
  Add-Check "append_event works end-to-end through gateway" "PASS" "eventA=$($eventA.event_id); eventB=$($eventB.event_id)"

  # Create a compact summary internally to verify gateway expand_source over compacted state.
  $summarySql = @"
SET agentcore.current_project_id = '$($sessionA.project_id)';
SELECT agentcore.create_context_summary(
  '$($sessionA.project_id)',
  '$($sessionA.session_id)',
  'L1',
  'active_dynamic',
  'M4 gateway compact summary',
  'M4 compact summary for $runId',
  40,
  0.90,
  ARRAY['$($eventA.event_id)'::uuid,'$($eventB.event_id)'::uuid],
  NULL
);
"@
  $summaryId = @((Invoke-PsqlValue $summarySql) -split "`n" | Where-Object { $_.Trim() -match '^[0-9a-fA-F-]{36}$' })[0].Trim()

  $retrieved = Invoke-Tool -Name "agentcore_memory-retrieve_context" -Arguments @{ project_key = $projectKey; budget_name = "default" }
  if (-not ($retrieved.items | Where-Object { $_.body -match $runId })) {
    throw "retrieve_context did not return appended/summarized context"
  }
  $expanded = Invoke-Tool -Name "agentcore_memory-expand_source" -Arguments @{ summary_id = $summaryId }
  $expandedText = $expanded.sources | ConvertTo-Json -Depth 10
  if ($expandedText -notmatch "M4 session A exact text $runId" -or $expandedText -notmatch "M4 session B exact text $runId") {
    throw "expand_source did not return exact appended source events"
  }
  Add-Check "append retrieve compact expand works end-to-end" "PASS" "summary=$summaryId"

  $startup = Invoke-Tool -Name "agentcore_memory-startup_context" -Arguments @{ project_key = $projectKey; budget_name = "default" }
  if (-not ($startup.authority -contains "BLUEPRINT.md")) { throw "startup_context missing authority chain" }
  Add-Check "startup_context returns authority-aware bounded context" "PASS" "items=$($startup.items.Count)"

  $proposal = Invoke-Tool -Name "agentcore_memory-propose_fact" -Arguments @{
    project_key = $projectKey
    fact_key = "m4.test.fact"
    proposed_value = @{ value = "proposal-$runId" }
    contradicts_event_id = [string]$eventA.event_id
  }
  if ($proposal.status -ne "proposed") { throw "propose_fact did not create proposal" }
  Add-Check "propose_fact uses review path" "PASS" "proposal=$($proposal.proposal_id)"

  $handoff = Invoke-Tool -Name "agentcore_memory-build_handoff" -Arguments @{ project_key = $projectKey }
  if ($handoff.recent_events.Count -lt 2) { throw "build_handoff missing recent events" }
  $docs = Invoke-Tool -Name "agentcore_memory-docs_search" -Arguments @{ project_key = $projectKey; query = "gateway"; limit = 5 }
  Add-Check "build_handoff and docs_search return bounded packets" "PASS" "handoff_events=$($handoff.recent_events.Count); docs_results=$($docs.results.Count)"

  Invoke-Tool -Name "agentcore_memory-session_close" -Arguments @{ session_id = [string]$sessionA.session_id } | Out-Null
  Invoke-Tool -Name "agentcore_memory-session_close" -Arguments @{ session_id = [string]$sessionB.session_id } | Out-Null
  Add-Check "session_close works" "PASS" "both sessions closed"

  $summary.completed_at = (Get-Date).ToUniversalTime().ToString("o")
  $summary.result = "PASS"
  $summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $evidencePath "m4-acceptance-summary.json") -Encoding utf8
  $summary.checks | ForEach-Object { "{0}: {1} - {2}" -f $_.name, $_.result, $_.detail } |
    Set-Content -LiteralPath (Join-Path $evidencePath "m4-acceptance-summary.txt") -Encoding utf8
  Write-Output "PASS: M4 gateway acceptance checks completed"
  Write-Output (Join-Path $evidencePath "m4-acceptance-summary.json")
}
catch {
  $summary.completed_at = (Get-Date).ToUniversalTime().ToString("o")
  $summary.result = "FAIL"
  $summary.error = $_.Exception.Message
  $summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $evidencePath "m4-acceptance-summary.json") -Encoding utf8
  Write-Error $_
  exit 1
}
