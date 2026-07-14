<#
.SYNOPSIS
  Cut non-Swarm IDE MCP baselines over to the single agentcore-gateway Bifrost entry.

.DESCRIPTION
  - Backs up each supported IDE config
  - Removes baseline direct MCP entries listed in the Bifrost upstream registry
  - Removes SwarmRecall/SwarmVault IDE entries from non-Swarm IDEs (Swarm products untouched)
  - Installs a single agentcore-gateway HTTP entry
  - Does NOT modify OpenClaw/ClawX
  - Never commits secrets; may materialize BIFROST_MCP_VIRTUAL_KEY into live config only when
    the client cannot expand ${env:...} in headers

.NOTES
  Evidence is written under ops/bifrost/evidence/ (sanitized).
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$EvidenceRoot = '',
  [switch]$DryRun,
  [string[]]$Clients = @(
    'cursor',
    'minimax',
    'mavis',
    'claude-desktop',
    'claude-code',
    'codex',
    'antigravity',
    'open-interpreter'
  )
)

$ErrorActionPreference = 'Stop'

if (-not $EvidenceRoot) {
  $EvidenceRoot = Join-Path $RepoRoot ('ops\bifrost\evidence\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null

$registryPath = Join-Path $RepoRoot 'contracts\bifrost-upstream-mcp-registry.json'
$gatewayPath = Join-Path $RepoRoot 'contracts\agentcore-gateway-client.json'
$registry = Get-Content -LiteralPath $registryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$gateway = Get-Content -LiteralPath $gatewayPath -Raw -Encoding UTF8 | ConvertFrom-Json

$baselineIds = @($registry.servers.PSObject.Properties.Name)
$baselineIds += @('swarmrecall', 'swarmvault', 'SwarmRecall', 'SwarmVault', 'github', 'github-mcp')
$baselineIds = $baselineIds | Select-Object -Unique

function Get-VirtualKeyValue {
  $vk = [Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY', 'User')
  if ([string]::IsNullOrWhiteSpace($vk)) {
    $vk = [Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY', 'Process')
  }
  if ([string]::IsNullOrWhiteSpace($vk)) {
    $vk = [Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY', 'Machine')
  }
  return $vk
}

function Backup-File([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    return $null
  }
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $backup = "$Path.bifrost-cutover-$stamp.bak"
  Copy-Item -LiteralPath $Path -Destination $backup -Force
  return $backup
}

function New-GatewayJsonEntry {
  param(
    [bool]$SupportsEnvHeaders,
    [string]$TypeField = 'http'
  )
  $vk = Get-VirtualKeyValue
  $authHeader = if ($SupportsEnvHeaders) {
    'Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}'
  } else {
    if ([string]::IsNullOrWhiteSpace($vk)) {
      throw 'BIFROST_MCP_VIRTUAL_KEY is required for clients that cannot expand env headers'
    }
    "Bearer $vk"
  }
  return [ordered]@{
    type    = $TypeField
    url     = $gateway.url
    headers = [ordered]@{
      Authorization = $authHeader
    }
    timeout = [int]$gateway.timeout_seconds
  }
}

function Write-SanitizedEvidence {
  param(
    [string]$Client,
    [hashtable]$Payload
  )
  # Redact Authorization bearer values
  $json = $Payload | ConvertTo-Json -Depth 12
  $json = [regex]::Replace($json, 'Bearer\s+[^\s"]+', 'Bearer ***REDACTED***')
  $path = Join-Path $EvidenceRoot "$Client.json"
  Set-Content -LiteralPath $path -Value $json -Encoding UTF8
}

function Update-JsonMcpServers {
  param(
    [string]$ClientName,
    [string]$ConfigPath,
    [string]$ServersKey = 'mcpServers',
    [bool]$SupportsEnvHeaders = $true
  )

  $result = [ordered]@{
    client     = $ClientName
    path       = $ConfigPath
    existed    = (Test-Path -LiteralPath $ConfigPath)
    backup     = $null
    removed    = @()
    action     = 'skip'
  }

  if (-not (Test-Path -LiteralPath $ConfigPath)) {
    # Create minimal file
    $dir = Split-Path -Parent $ConfigPath
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $obj = [ordered]@{ $ServersKey = [ordered]@{} }
  } else {
    $result.backup = Backup-File -Path $ConfigPath
    $obj = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $obj.$ServersKey) {
      $obj | Add-Member -NotePropertyName $ServersKey -NotePropertyValue ([pscustomobject]@{}) -Force
    }
  }

  $servers = $obj.$ServersKey
  $toRemove = @()
  foreach ($prop in @($servers.PSObject.Properties)) {
    $name = $prop.Name
    if ($name -eq 'agentcore-gateway') { continue }
    $lower = $name.ToLowerInvariant()
    $isCursorDockerGateway = $ClientName -eq 'cursor' -and $lower -eq 'mcp_docker'
    if ($baselineIds -contains $name -or $baselineIds -contains $lower -or $lower -match 'swarm(recall|vault|claw)' -or $isCursorDockerGateway) {
      $toRemove += $name
    }
  }
  foreach ($name in $toRemove) {
    $servers.PSObject.Properties.Remove($name)
    $result.removed += $name
  }

  $entry = New-GatewayJsonEntry -SupportsEnvHeaders:$SupportsEnvHeaders
  # Attach/replace gateway entry
  if ($servers.PSObject.Properties.Name -contains 'agentcore-gateway') {
    $servers.PSObject.Properties.Remove('agentcore-gateway')
  }
  $servers | Add-Member -NotePropertyName 'agentcore-gateway' -NotePropertyValue ([pscustomobject]$entry) -Force

  $result.action = if ($DryRun) { 'dry-run' } else { 'updated' }
  if (-not $DryRun) {
    $obj | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ConfigPath -Encoding UTF8
  }
  Write-SanitizedEvidence -Client $ClientName -Payload $result
  return $result
}

function Update-CodexToml {
  param([string]$ConfigPath)

  $result = [ordered]@{
    client  = 'codex'
    path    = $ConfigPath
    existed = (Test-Path -LiteralPath $ConfigPath)
    backup  = $null
    removed = @()
    action  = 'skip'
  }
  if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Write-SanitizedEvidence -Client 'codex' -Payload $result
    return $result
  }

  $result.backup = Backup-File -Path $ConfigPath
  $lines = Get-Content -LiteralPath $ConfigPath -Encoding UTF8
  $out = New-Object System.Collections.Generic.List[string]
  $i = 0
  $skipping = $false
  while ($i -lt $lines.Count) {
    $line = $lines[$i]
    if ($line -match '^\s*\[mcp_servers\.([^\]]+)\]\s*$') {
      $sectionName = $Matches[1].Trim('"').Trim("'")
      $lower = $sectionName.ToLowerInvariant()
      $isGateway = ($sectionName -eq 'agentcore-gateway')
      $isBaseline = ($baselineIds -contains $sectionName) -or ($baselineIds -contains $lower) -or ($lower -match 'swarm(recall|vault|claw)') -or ($lower -eq 'mcp_docker')
      if ($isBaseline -and -not $isGateway) {
        $skipping = $true
        $result.removed += $sectionName
        $i++
        continue
      }
      if ($isGateway) {
        $skipping = $true
        $i++
        continue
      }
      $skipping = $false
      $out.Add($line) | Out-Null
      $i++
      continue
    }
    if ($skipping) {
      if ($line -match '^\s*\[') {
        $skipping = $false
        continue
      }
      $i++
      continue
    }
    $out.Add($line) | Out-Null
    $i++
  }

  # Codex constructs the Authorization: Bearer header from this environment
  # variable. Do not place a ${env:...} placeholder in static http_headers.
  $block = @(
    '',
    '[mcp_servers.agentcore-gateway]',
    'url = "http://127.0.0.1:8080/mcp"',
    'bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"',
    'enabled = true',
    'startup_timeout_sec = 300',
    'tool_timeout_sec = 300'
  )
  foreach ($b in $block) { $out.Add($b) | Out-Null }

  $result.action = if ($DryRun) { 'dry-run' } else { 'updated' }
  if (-not $DryRun) {
    Set-Content -LiteralPath $ConfigPath -Value $out -Encoding UTF8
  }
  Write-SanitizedEvidence -Client 'codex' -Payload $result
  return $result
}

$summary = @()

foreach ($client in $Clients) {
  switch ($client) {
    'cursor' {
      $summary += Update-JsonMcpServers -ClientName 'cursor' -ConfigPath 'C:\Users\ynotf\.cursor\mcp.json' -SupportsEnvHeaders:$true
    }
    'minimax' {
      $summary += Update-JsonMcpServers -ClientName 'minimax' -ConfigPath 'C:\Users\ynotf\.minimax\mcp\mcp.json' -SupportsEnvHeaders:$true
    }
    'mavis' {
      $summary += Update-JsonMcpServers -ClientName 'mavis' -ConfigPath 'C:\Users\ynotf\.mavis\mcp\mcp.json' -SupportsEnvHeaders:$true
    }
    'claude-desktop' {
      $summary += Update-JsonMcpServers -ClientName 'claude-desktop' -ConfigPath 'C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json' -SupportsEnvHeaders:$false
    }
    'claude-code' {
      $path = 'C:\Users\ynotf\.claude.json'
      if (Test-Path -LiteralPath $path) {
        $summary += Update-JsonMcpServers -ClientName 'claude-code' -ConfigPath $path -SupportsEnvHeaders:$true
      } else {
        $payload = [ordered]@{ client = 'claude-code'; path = $path; existed = $false; action = 'skipped-missing' }
        Write-SanitizedEvidence -Client 'claude-code' -Payload $payload
        $summary += $payload
      }
    }
    'codex' {
      $summary += Update-CodexToml -ConfigPath 'C:\Users\ynotf\.codex\config.toml'
    }
    'antigravity' {
      $summary += Update-JsonMcpServers -ClientName 'antigravity-gemini' -ConfigPath 'C:\Users\ynotf\.gemini\config\mcp_config.json' -SupportsEnvHeaders:$true
      $summary += Update-JsonMcpServers -ClientName 'antigravity-appdata' -ConfigPath 'C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json' -SupportsEnvHeaders:$true
    }
    'open-interpreter' {
      $summary += Update-JsonMcpServers -ClientName 'open-interpreter' -ConfigPath 'C:\Users\ynotf\AppData\Roaming\interpreter\config.json' -SupportsEnvHeaders:$false
    }
    default {
      Write-Warning "Unknown client skipped: $client"
    }
  }
}

Write-Host "[Cutover] Evidence: $EvidenceRoot"
Write-Host '[Cutover] OpenClaw/ClawX intentionally not modified.'
Write-Host '[Cutover] Swarm product installs untouched; Swarm IDE entries removed from non-Swarm baselines where present.'

$summaryPath = Join-Path $EvidenceRoot 'summary.json'
($summary | ConvertTo-Json -Depth 8) -replace 'Bearer\s+[^\s"]+', 'Bearer ***REDACTED***' |
  Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host '[Cutover] Complete'
