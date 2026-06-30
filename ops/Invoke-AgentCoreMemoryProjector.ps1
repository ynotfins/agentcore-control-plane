param(
  [ValidateSet("Project")]
  [string]$Mode = "Project",
  [int]$Limit = 25,
  [string]$PsqlPath = "F:\AgentCore\postgres_runtime_engine\pgsql\bin\psql.exe",
  [string]$Database = "agent_core",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$UserName = "agent_read",
  [string]$PasswordEnv = "AGENT_CORE_AGENT_READ_PASSWORD",
  [string]$SwarmRecallConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json",
  [string]$StateRoot = "F:\AgentCore\agentmemory\projection-state",
  [string]$VaultRoot = "F:\AgentCore\agentmemory\swarmvault",
  [string]$SwarmVaultRepoRoot = "D:\github\vendor\swarm\swarmvault"
)

$ErrorActionPreference = "Stop"

function Get-RequiredEnvValue {
  param([string]$Name)
  foreach ($scope in @("Process", "User", "Machine")) {
    $value = [Environment]::GetEnvironmentVariable($Name, $scope)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      return $value
    }
  }
  throw "Required environment variable not found in Process/User/Machine scope: $Name"
}

function Read-JsonFile {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return $null
  }
  return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Write-JsonFile {
  param(
    [string]$Path,
    [object]$Value
  )
  $parent = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  $Value | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $Path -Encoding utf8
}

function Get-SwarmRecallConfig {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "SwarmRecall config not found: $Path"
  }
  return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-ProjectionSummaryPath {
  param([string]$Root)
  return Join-Path $Root "summary.json"
}

function Get-ProjectionEntriesRoot {
  param([string]$Root)
  return Join-Path $Root "entries"
}

function Get-ProjectionEntryPath {
  param(
    [string]$Root,
    [string]$SourceId
  )
  return Join-Path (Get-ProjectionEntriesRoot -Root $Root) "$SourceId.json"
}

function New-ProjectionSummary {
  return [ordered]@{
    version = 1
    updated_at = $null
    checkpoint = [ordered]@{
      created_at = "1970-01-01T00:00:00Z"
      id = "00000000-0000-0000-0000-000000000000"
    }
    totals = [ordered]@{
      projected_rows = 0
      swarmrecall_success = 0
      swarmvault_success = 0
      swarmvault_skipped = 0
      failures = 0
    }
  }
}

function Read-ProjectionSummary {
  param([string]$Root)
  $summaryPath = Get-ProjectionSummaryPath -Root $Root
  $summary = Read-JsonFile -Path $summaryPath
  if ($null -eq $summary) {
    $summary = New-ProjectionSummary
    Write-JsonFile -Path $summaryPath -Value $summary
  }
  return $summary
}

function Write-ProjectionSummary {
  param(
    [string]$Root,
    [object]$Summary
  )
  $Summary.updated_at = (Get-Date).ToUniversalTime().ToString("o")
  Write-JsonFile -Path (Get-ProjectionSummaryPath -Root $Root) -Value $Summary
}

function Read-ProjectionEntry {
  param(
    [string]$Root,
    [string]$SourceId
  )
  return Read-JsonFile -Path (Get-ProjectionEntryPath -Root $Root -SourceId $SourceId)
}

function Write-ProjectionEntry {
  param(
    [string]$Root,
    [string]$SourceId,
    [object]$Entry
  )
  $Entry.updated_at = (Get-Date).ToUniversalTime().ToString("o")
  Write-JsonFile -Path (Get-ProjectionEntryPath -Root $Root -SourceId $SourceId) -Value $Entry
}

function ConvertTo-ProjectionTimestamp {
  param([object]$Value)

  if ($null -eq $Value) {
    return $null
  }

  if ($Value -is [DateTimeOffset]) {
    return $Value.ToString("o")
  }

  if ($Value -is [DateTime]) {
    return ([DateTimeOffset]$Value).ToString("o")
  }

  return ([DateTimeOffset]::Parse([string]$Value, [System.Globalization.CultureInfo]::InvariantCulture)).ToString("o")
}

function Sync-ProjectionSummaryTotals {
  param(
    [string]$Root,
    [object]$Summary
  )

  $entryRoot = Get-ProjectionEntriesRoot -Root $Root
  $entryFiles = @(Get-ChildItem -LiteralPath $entryRoot -Filter *.json -ErrorAction SilentlyContinue)
  $projectedRows = 0
  $swarmRecallSuccess = 0
  $swarmVaultSuccess = 0
  $swarmVaultSkipped = 0
  $failures = 0

  foreach ($file in $entryFiles) {
    $entry = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
    if ($entry.swarmrecall.status -eq "projected") {
      $swarmRecallSuccess++
    }
    if ($entry.swarmvault.status -eq "projected") {
      $swarmVaultSuccess++
    }
    if ($entry.swarmvault.status -eq "skipped") {
      $swarmVaultSkipped++
    }
    if ($entry.swarmrecall.status -eq "failed" -or $entry.swarmvault.status -eq "failed") {
      $failures++
    }
    if ($entry.swarmrecall.status -eq "projected" -and @("projected", "skipped") -contains [string]$entry.swarmvault.status) {
      $projectedRows++
    }
  }

  $Summary.totals.projected_rows = $projectedRows
  $Summary.totals.swarmrecall_success = $swarmRecallSuccess
  $Summary.totals.swarmvault_success = $swarmVaultSuccess
  $Summary.totals.swarmvault_skipped = $swarmVaultSkipped
  $Summary.totals.failures = $failures
}

function Invoke-AgentCorePsqlJsonLines {
  param(
    [string]$Sql,
    [string]$PsqlExe,
    [string]$DbHost,
    [int]$DbPort,
    [string]$DbName,
    [string]$DbUser,
    [string]$DbPassword
  )
  $env:PGPASSWORD = $DbPassword
  try {
    $output = & $PsqlExe -h $DbHost -p $DbPort -U $DbUser -d $DbName -t -A -v ON_ERROR_STOP=1 -c $Sql 2>&1
    if ($LASTEXITCODE -ne 0) {
      throw "psql failed: $($output -join "`n")"
    }
    return @($output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  } finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
  }
}

function Get-CheckpointQuery {
  param(
    [string]$CreatedAt,
    [string]$SourceId,
    [int]$RowLimit
  )
  return @"
WITH source_rows AS (
  SELECT
    id::text AS id,
    created_at,
    agent_signature,
    associated_project_path,
    document_source,
    content_chunk,
    metadata::text AS metadata_text
  FROM global_vector_memory_store
  WHERE
    (created_at > '$CreatedAt'::timestamptz)
    OR (created_at = '$CreatedAt'::timestamptz AND id::text > '$SourceId')
  ORDER BY created_at ASC, id ASC
  LIMIT $RowLimit
)
SELECT row_to_json(source_rows)::text FROM source_rows;
"@
}

function Get-ProjectionBacklogCount {
  param(
    [string]$CreatedAt,
    [string]$SourceId,
    [string]$PsqlExe,
    [string]$DbHost,
    [int]$DbPort,
    [string]$DbName,
    [string]$DbUser,
    [string]$DbPassword
  )
  $sql = @"
SELECT COUNT(*)
FROM global_vector_memory_store
WHERE
  (created_at > '$CreatedAt'::timestamptz)
  OR (created_at = '$CreatedAt'::timestamptz AND id::text > '$SourceId');
"@
  $lines = Invoke-AgentCorePsqlJsonLines -Sql $sql -PsqlExe $PsqlExe -DbHost $DbHost -DbPort $DbPort -DbName $DbName -DbUser $DbUser -DbPassword $DbPassword
  $first = @($lines | Select-Object -First 1)[0]
  $firstText = ([string]$first).Trim()
  return [int]$firstText
}

function ConvertTo-ProjectionCategory {
  param(
    [string]$DocumentSource,
    [string]$Content,
    [object]$Metadata
  )
  $sourceKind = [string]$Metadata.source_kind
  if ($sourceKind -eq "decision" -or $DocumentSource -match "decision") { return "decision" }
  if ($sourceKind -eq "fact" -or $DocumentSource -match "fact|inventory|schema") { return "fact" }
  if ($Content -match "summary" -or $DocumentSource -match "summary") { return "session_summary" }
  return "context"
}

function ConvertTo-ProjectionTags {
  param(
    [string]$AgentSignature,
    [string]$ProjectPath,
    [string]$DocumentSource,
    [object]$Metadata
  )
  $tags = New-Object System.Collections.Generic.List[string]
  $maxTagLength = 50
  foreach ($candidate in @(
    $AgentSignature,
    (Split-Path -Leaf $ProjectPath),
    $DocumentSource,
    [string]$Metadata.platform,
    [string]$Metadata.project,
    [string]$Metadata.source_kind
  )) {
    if ([string]::IsNullOrWhiteSpace($candidate)) {
      continue
    }

    $normalized = ([string]$candidate).Trim()
    if ($normalized.Length -gt $maxTagLength) {
      $normalized = $normalized.Substring(0, $maxTagLength)
    }

    if (-not [string]::IsNullOrWhiteSpace($normalized) -and -not $tags.Contains($normalized)) {
      $tags.Add($normalized) | Out-Null
    }
  }
  return @($tags)
}

function Test-SwarmVaultProjectionCandidate {
  param([object]$Row)

  $metadata = if ($Row.metadata_text) { $Row.metadata_text | ConvertFrom-Json } else { [pscustomobject]@{} }
  $sourceKind = ([string]$metadata.source_kind).Trim().ToLowerInvariant()
  $documentSource = ([string]$Row.document_source).Trim().ToLowerInvariant()
  $storageContract = ([string]$metadata.storage_contract).Trim()
  $gatewayEntryId = ([string]$metadata.gateway_entry_id).Trim()
  $appId = ([string]$metadata.app_id).Trim()
  $projectPath = ([string]$metadata.project_path).Trim().ToLowerInvariant()
  $associatedProjectPath = ([string]$metadata.associated_project_path).Trim().ToLowerInvariant()

  $isGoverned = $false
  if ($storageContract -eq "mcp-control-plane.global-memory.v1") {
    $isGoverned = $true
  } elseif (-not [string]::IsNullOrWhiteSpace($gatewayEntryId)) {
    $isGoverned = $true
  } elseif (-not [string]::IsNullOrWhiteSpace($appId) -and $appId -eq "codex-managed") {
    $isGoverned = $true
  }

  if (-not $isGoverned) {
    return $false
  }

  $legacyOpsRoot = "d:\mcp-control-plane"
  if ($projectPath -eq $legacyOpsRoot -or $associatedProjectPath -eq $legacyOpsRoot -or $documentSource.StartsWith($legacyOpsRoot)) {
    return $false
  }

  $approvedKinds = @(
    "architecture",
    "contract",
    "decision",
    "documentation",
    "fact",
    "guide",
    "handoff",
    "index",
    "inventory",
    "investigation",
    "policy",
    "report",
    "research",
    "runbook",
    "schema",
    "summary",
    "verification"
  )
  if ($approvedKinds -contains $sourceKind) {
    return $true
  }

  if ($documentSource -match '\.(md|markdown|txt|rst|adoc)$') {
    return $true
  }

  if ($documentSource -match 'architecture|bootstrap|contract|decision|design|docs?|guide|handoff|inventory|investigation|policy|readme|report|research|runbook|schema|spec|storage|summary|verification') {
    return $true
  }

  return $false
}

function Invoke-SwarmRecallProjection {
  param(
    [object]$Row,
    [object]$SwarmRecallConfig
  )
  $apiKey = Get-RequiredEnvValue -Name $SwarmRecallConfig.auth.apiKeyEnv
  $metadata = if ($Row.metadata_text) { $Row.metadata_text | ConvertFrom-Json } else { [pscustomobject]@{} }
  $content = [string]$Row.content_chunk
  $contentTruncated = $false
  if ($content.Length -gt 9950) {
    $content = $content.Substring(0, 9950) + "... [truncated by agentcore projector]"
    $contentTruncated = $true
  }
  $body = [ordered]@{
    content = $content
    category = ConvertTo-ProjectionCategory -DocumentSource ([string]$Row.document_source) -Content ([string]$Row.content_chunk) -Metadata $metadata
    importance = 0.6
    tags = ConvertTo-ProjectionTags -AgentSignature ([string]$Row.agent_signature) -ProjectPath ([string]$Row.associated_project_path) -DocumentSource ([string]$Row.document_source) -Metadata $metadata
    metadata = [ordered]@{
      source_memory_id = [string]$Row.id
      source_created_at = [string]$Row.created_at
      source_contract = "agent_core.global_vector_memory_store"
      source_document = [string]$Row.document_source
      source_project_path = [string]$Row.associated_project_path
      source_agent_signature = [string]$Row.agent_signature
      source_metadata = $metadata
      projection = [ordered]@{
        projector = "agentcore-control-plane"
        mode = "gateway-governed"
        content_truncated = $contentTruncated
      }
    }
  }

  $headers = @{
    Authorization = "Bearer $apiKey"
    "Content-Type" = "application/json"
  }
  $uri = $SwarmRecallConfig.api.url.TrimEnd("/") + "/api/v1/memory"
  $jsonBody = $body | ConvertTo-Json -Depth 16
  return Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $jsonBody
}

function New-SwarmVaultProjectionMarkdown {
  param(
    [object]$Row,
    [string]$OutputPath
  )
  $metadata = if ($Row.metadata_text) { $Row.metadata_text | ConvertFrom-Json } else { [pscustomobject]@{} }
  $content = @(
    "# AgentCore Memory Projection"
    ""
    "- Source memory id: $($Row.id)"
    "- Created at: $($Row.created_at)"
    "- Agent signature: $($Row.agent_signature)"
    "- Project path: $($Row.associated_project_path)"
    "- Document source: $($Row.document_source)"
    "- Platform: $($metadata.platform)"
    ""
    "## Content"
    ""
    $Row.content_chunk
    ""
    "## Metadata"
    ""
    '```json'
    (($metadata | ConvertTo-Json -Depth 16))
    '```'
    ""
  ) -join "`r`n"

  $parent = Split-Path -Parent $OutputPath
  if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  Set-Content -LiteralPath $OutputPath -Value $content -Encoding utf8
}

function Invoke-SwarmVaultProjection {
  param(
    [string[]]$Files,
    [string]$InputRoot,
    [string]$VaultRepoRoot,
    [string]$VaultRuntimeRoot
  )
  if ($Files.Count -eq 0) {
    return $null
  }

  $ingestScript = Join-Path (Split-Path -Parent $PSCommandPath) "Invoke-AgentCoreSwarmVaultIngest.ps1"
  $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ingestScript -InputPath $InputRoot -RepoRoot $VaultRepoRoot -VaultRoot $VaultRuntimeRoot -Compile -Json 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "SwarmVault projection ingest failed: $($output -join "`n")"
  }
  return ($output -join "`n").Trim()
}

if ($Mode -ne "Project") {
  throw "Unsupported mode: $Mode"
}

if (-not (Test-Path -LiteralPath $PsqlPath)) {
  throw "psql executable not found: $PsqlPath"
}

$summary = Read-ProjectionSummary -Root $StateRoot
$swarmRecallConfig = Get-SwarmRecallConfig -Path $SwarmRecallConfigPath
$dbPassword = Get-RequiredEnvValue -Name $PasswordEnv
$query = Get-CheckpointQuery -CreatedAt ([string]$summary.checkpoint.created_at) -SourceId ([string]$summary.checkpoint.id) -RowLimit $Limit
$rows = Invoke-AgentCorePsqlJsonLines -Sql $query -PsqlExe $PsqlPath -DbHost $HostName -DbPort $Port -DbName $Database -DbUser $UserName -DbPassword $dbPassword

$runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stagingRoot = Join-Path $StateRoot ("swarmvault-staging\" + $runStamp)
$pendingFiles = New-Object System.Collections.Generic.List[string]
$processed = New-Object System.Collections.Generic.List[object]

foreach ($line in $rows) {
  $row = $line | ConvertFrom-Json
  $entry = Read-ProjectionEntry -Root $StateRoot -SourceId $row.id
  if ($null -eq $entry) {
    $entry = [ordered]@{
      source_id = [string]$row.id
      source_created_at = ConvertTo-ProjectionTimestamp -Value $row.created_at
      swarmrecall = [ordered]@{ status = "pending"; projected_at = $null; remote_id = $null; detail = $null }
      swarmvault = [ordered]@{ status = "pending"; projected_at = $null; artifact_path = $null; detail = $null }
    }
  }

  try {
    if ($entry.swarmrecall.status -ne "projected") {
      $recallResponse = Invoke-SwarmRecallProjection -Row $row -SwarmRecallConfig $swarmRecallConfig
      $entry.swarmrecall.status = "projected"
      $entry.swarmrecall.projected_at = (Get-Date).ToUniversalTime().ToString("o")
      $entry.swarmrecall.remote_id = [string]$recallResponse.id
      $entry.swarmrecall.detail = "stored via local API"
      $summary.totals.swarmrecall_success++
    }

    if ($entry.swarmvault.status -ne "projected" -and $entry.swarmvault.status -ne "skipped") {
      if (Test-SwarmVaultProjectionCandidate -Row $row) {
        $artifactDir = Join-Path $stagingRoot ([string]$row.id)
        $artifactPath = Join-Path $artifactDir "memory.md"
        New-SwarmVaultProjectionMarkdown -Row $row -OutputPath $artifactPath
        $pendingFiles.Add($artifactPath) | Out-Null
        $entry.swarmvault.status = "staged"
        $entry.swarmvault.artifact_path = $artifactPath
        $entry.swarmvault.detail = "staged for curated vault ingest"
      } else {
        $entry.swarmvault.status = "skipped"
        $entry.swarmvault.artifact_path = $null
        $entry.swarmvault.detail = "not curated for SwarmVault projection"
        $summary.totals.swarmvault_skipped++
      }
    }

    Write-ProjectionEntry -Root $StateRoot -SourceId $row.id -Entry $entry
    $processed.Add([pscustomobject]@{ row = $row; entry = $entry }) | Out-Null
  } catch {
    if ($entry.swarmrecall.status -ne "projected") {
      $entry.swarmrecall.status = "failed"
      $entry.swarmrecall.detail = $_.Exception.Message
    }
    if ($entry.swarmvault.status -ne "projected" -and $entry.swarmvault.status -ne "skipped") {
      $entry.swarmvault.status = "failed"
      $entry.swarmvault.detail = $_.Exception.Message
    }
    Write-ProjectionEntry -Root $StateRoot -SourceId $row.id -Entry $entry
    $summary.totals.failures++
    break
  }
}

if ($pendingFiles.Count -gt 0) {
  $vaultDetail = Invoke-SwarmVaultProjection -Files @($pendingFiles) -InputRoot $stagingRoot -VaultRepoRoot $SwarmVaultRepoRoot -VaultRuntimeRoot $VaultRoot
  foreach ($item in $processed) {
    if ($item.entry.swarmvault.status -eq "staged") {
      $item.entry.swarmvault.status = "projected"
      $item.entry.swarmvault.projected_at = (Get-Date).ToUniversalTime().ToString("o")
      $item.entry.swarmvault.detail = $vaultDetail
      Write-ProjectionEntry -Root $StateRoot -SourceId $item.row.id -Entry $item.entry
      $summary.totals.swarmvault_success++
    }
  }
}

foreach ($item in $processed) {
  if ($item.entry.swarmrecall.status -eq "projected" -and @("projected", "skipped") -contains $item.entry.swarmvault.status) {
    $summary.checkpoint.created_at = ConvertTo-ProjectionTimestamp -Value $item.row.created_at
    $summary.checkpoint.id = [string]$item.row.id
  } else {
    break
  }
}

Sync-ProjectionSummaryTotals -Root $StateRoot -Summary $summary
Write-ProjectionSummary -Root $StateRoot -Summary $summary

$backlog = Get-ProjectionBacklogCount -CreatedAt ([string]$summary.checkpoint.created_at) -SourceId ([string]$summary.checkpoint.id) -PsqlExe $PsqlPath -DbHost $HostName -DbPort $Port -DbName $Database -DbUser $UserName -DbPassword $dbPassword
[pscustomobject]@{
  mode = $Mode
  processed = $processed.Count
  backlog = $backlog
  state_root = $StateRoot
  checkpoint = $summary.checkpoint
  totals = $summary.totals
} | ConvertTo-Json -Depth 8
