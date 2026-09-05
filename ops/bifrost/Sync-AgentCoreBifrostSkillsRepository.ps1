#Requires -Version 7.0
<#
.SYNOPSIS
  Dry-run-first sync for approved AgentCore skills into the Bifrost Skills Repository.

.DESCRIPTION
  Reads the approved local skill folders from one or more roots, builds Bifrost
  Skills API payloads, scans outgoing strings for obvious secret material, and
  compares by skill name against GET /api/skills. By default this is read-only
  and reports would_create or would_update. POST/PUT calls are made only with
  -Apply.
#>
[CmdletBinding()]
param(
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$SkillRoot = 'D:\github\agentcore-control-plane\.agents\skills',
  [string[]]$AdditionalSkillRoot = @('C:\Users\ynotf\.agents\skills'),
  [string[]]$IncludeSkill = @('agentcore-project-lifecycle', 'langfuse'),
  [switch]$Apply,
  [switch]$UpdateExisting,
  [string]$AdminApiKey = '',
  [switch]$OutputJson,
  [switch]$TestMode,
  [string]$TestListResponsePath = '',
  [string]$TestWriteLogPath = ''
)

$ErrorActionPreference = 'Stop'

$ApprovedSkills = @('agentcore-project-lifecycle', 'langfuse', 'nia')
$MaxSupportingFileBytes = 65536
$script:TestWriteCalls = @()

function Get-EnvValue([string]$Name) {
  $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if (-not $value) { $value = [Environment]::GetEnvironmentVariable($Name, 'User') }
  return $value
}

function Read-JsonFile([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return $null
  }
  return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100 -ErrorAction Stop
}

function Get-PropertyValue($Object, [string[]]$Names) {
  if ($null -eq $Object) { return $null }
  foreach ($name in $Names) {
    if ($Object -is [System.Collections.IDictionary] -and $Object.Contains($name)) {
      return $Object[$name]
    }
    $property = $Object.PSObject.Properties[$name]
    if ($null -ne $property) { return $property.Value }
  }
  return $null
}

function Get-SkillRootPath {
  $repoRoot = $null
  try {
    $candidate = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($candidate)) {
      $repoRoot = [string]$candidate
    }
  } catch {
    $repoRoot = $null
  }
  if (-not $repoRoot) {
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
  }
  return (Resolve-Path -LiteralPath $repoRoot).Path
}

function Resolve-SkillRoots([string[]]$Roots) {
  $resolved = @()
  foreach ($root in $Roots) {
    if ([string]::IsNullOrWhiteSpace($root)) { continue }
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
    $path = (Resolve-Path -LiteralPath $root -ErrorAction Stop).Path
    if ($path -notin $resolved) { $resolved += $path }
  }
  if (@($resolved).Count -eq 0) {
    throw 'No existing skill roots were found'
  }
  return @($resolved)
}

function Find-SkillInRoots([string]$Name, [string[]]$Roots) {
  foreach ($root in $Roots) {
    $skillPath = Join-Path $root $Name
    $skillMdPath = Join-Path $skillPath 'SKILL.md'
    if (Test-Path -LiteralPath $skillMdPath -PathType Leaf) {
      return [pscustomobject]@{
        Path = $skillPath
        Root = $root
      }
    }
  }
  return $null
}

function ConvertTo-SlashPath([string]$Path) {
  return ($Path -replace '\\', '/')
}

function Get-RelativePath([string]$Base, [string]$Path) {
  return ConvertTo-SlashPath ([System.IO.Path]::GetRelativePath($Base, $Path))
}

function Get-SkillFrontmatter([string]$Body) {
  $result = [ordered]@{}
  $lines = $Body -split "`r?`n"
  if ($lines.Count -lt 3 -or $lines[0].Trim() -ne '---') {
    return $result
  }

  $currentKey = $null
  for ($i = 1; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($line.Trim() -eq '---') { break }
    if ($line -match '^([A-Za-z0-9_-]+):\s*(.*)$') {
      $currentKey = $matches[1]
      $value = $matches[2].Trim()
      if ($value -eq '') {
        $result[$currentKey] = @()
      } else {
        $result[$currentKey] = $value.Trim('"').Trim("'")
      }
      continue
    }
    if ($currentKey -and $line -match '^\s*-\s*(.+)$') {
      $items = @($result[$currentKey])
      $items += $matches[1].Trim().Trim('"').Trim("'")
      $result[$currentKey] = @($items)
    }
  }
  return $result
}

function Remove-Frontmatter([string]$Body) {
  $lines = $Body -split "`r?`n"
  if ($lines.Count -lt 3 -or $lines[0].Trim() -ne '---') {
    return $Body
  }
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq '---') {
      if ($i + 1 -ge $lines.Count) { return '' }
      return ($lines[($i + 1)..($lines.Count - 1)] -join "`n")
    }
  }
  return $Body
}

function Get-SkillDescription([string]$Body, [string]$Name) {
  $bodyWithoutFrontmatter = Remove-Frontmatter $Body
  foreach ($line in ($bodyWithoutFrontmatter -split "`r?`n")) {
    $trimmed = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
    if ($trimmed -match '^#+\s*(.+)$') {
      return $matches[1].Trim()
    }
    if ($trimmed -notmatch '^(```|---|\||>|[-*]\s+|\d+\.\s+)') {
      return $trimmed
    }
  }
  return "AgentCore skill: $Name"
}

function Test-SecretFileName([string]$RelativePath) {
  $leaf = [System.IO.Path]::GetFileName($RelativePath)
  return $leaf -match '(?i)(^|[._-])(secret|secrets|token|tokens|apikey|api-key|api_key|credential|credentials|private-key|private_key|id_rsa|env)([._-]|$)|^\.env($|\.)|\.pem$|\.pfx$|\.key$|\.ppk$'
}

function Test-ExcludedDirectory([string]$RelativePath) {
  $segments = $RelativePath -split '[\\/]'
  return @($segments | Where-Object { $_ -in @('.agentcore-skill-backups', '.git', 'node_modules', '__pycache__') }).Count -gt 0
}

function Test-TextFile([string]$Path) {
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  if ($bytes.Count -eq 0) { return $true }
  if (@($bytes | Where-Object { $_ -eq 0 }).Count -gt 0) { return $false }
  $sample = if ($bytes.Count -gt 4096) { $bytes[0..4095] } else { $bytes }
  $controlCount = @($sample | Where-Object { $_ -lt 32 -and $_ -notin @(9, 10, 13) }).Count
  return $controlCount -eq 0
}

function Get-MimeType([string]$Path) {
  if ([System.IO.Path]::GetExtension($Path).ToLowerInvariant() -eq '.json') {
    return 'application/json'
  }
  return 'text/plain'
}

function Get-SupportingFiles([string]$SkillPath) {
  $files = @()
  foreach ($file in (Get-ChildItem -LiteralPath $SkillPath -Recurse -File -Force | Sort-Object FullName)) {
    $relativePath = Get-RelativePath $SkillPath $file.FullName
    if ($relativePath -eq 'SKILL.md') { continue }
    if (Test-ExcludedDirectory $relativePath) { continue }
    if (Test-SecretFileName $relativePath) { continue }
    if ($file.Length -gt $MaxSupportingFileBytes) { continue }
    if (-not (Test-TextFile $file.FullName)) { continue }
    $files += [pscustomobject]@{
      path = $relativePath
      source_type = 'text'
      content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
      mime_type = Get-MimeType $file.FullName
    }
  }
  return @($files)
}

function Get-ExtraFrontmatter($Frontmatter) {
  $extra = [ordered]@{}
  foreach ($key in $Frontmatter.Keys) {
    if ($key -in @('name', 'description', 'version', 'license', 'compatibility', 'allowed-tools', 'allowed_tools')) {
      continue
    }
    $extra[$key] = $Frontmatter[$key]
  }
  return $extra
}

function Get-AllowedTools($Frontmatter) {
  $tools = Get-PropertyValue $Frontmatter @('allowed_tools', 'allowed-tools')
  if ($null -eq $tools) { return $null }
  if ($tools -is [array]) { return (@($tools) -join ', ') }
  return [string]$tools
}

function Assert-NoSecretMaterial([string]$Label, $Payload) {
  $json = $Payload | ConvertTo-Json -Depth 100 -Compress
  $patterns = @(
    @{ name = 'private_key_block'; regex = '-----BEGIN [A-Z ]*PRIVATE KEY-----' },
    @{ name = 'openai_or_provider_key'; regex = '\b(?:sk-proj|sk-or|sk-ant|sk-[A-Za-z0-9])[A-Za-z0-9_-]{20,}' },
    @{ name = 'github_pat'; regex = '\bgh[pousr]_[A-Za-z0-9_]{30,}' },
    @{ name = 'slack_token'; regex = '\bxox[baprs]-[A-Za-z0-9-]{20,}' },
    @{ name = 'google_api_key'; regex = '\bAIza[0-9A-Za-z_-]{30,}' },
    @{ name = 'bearer_literal'; regex = '(?i)\bbearer\s+[A-Za-z0-9._~+/-]{24,}' },
    @{ name = 'assigned_secret_literal'; regex = '(?i)\b(api[_-]?key|secret|token|credential)\s*[:=]\s*["'']?[A-Za-z0-9._~+/-]{24,}' }
  )
  foreach ($pattern in $patterns) {
    if ($json -match $pattern.regex) {
      throw "SECRET_SCAN_FAILED label=$Label pattern=$($pattern.name)"
    }
  }
}

function New-SkillPayload([string]$SkillPath, [string]$Name, [string]$RepoRoot, [string]$ResolvedSkillRoot) {
  $skillMdPath = Join-Path $SkillPath 'SKILL.md'
  $body = Get-Content -LiteralPath $skillMdPath -Raw -Encoding UTF8
  $frontmatter = Get-SkillFrontmatter $body
  $version = Get-PropertyValue $frontmatter @('version')
  if (-not $version) { $version = '1.0.0' }
  $description = Get-PropertyValue $frontmatter @('description')
  if (-not $description) { $description = Get-SkillDescription $body $Name }
  $allowedTools = Get-AllowedTools $frontmatter

  $payload = [ordered]@{
    name = $Name
    description = [string]$description
    skill_md_body = $body
    version = [string]$version
    compatibility = 'Codex, Claude Code'
    metadata = [ordered]@{
      source_repo = $RepoRoot
      source_root = $ResolvedSkillRoot
      source_path = Get-RelativePath $RepoRoot $SkillPath
      synced_by = 'AgentCore'
    }
    extra_frontmatter = Get-ExtraFrontmatter $frontmatter
    files = [array](Get-SupportingFiles $SkillPath)
  }

  $license = Get-PropertyValue $frontmatter @('license')
  if ($license) { $payload['license'] = [string]$license }
  if ($allowedTools) { $payload['allowed_tools'] = $allowedTools }

  return [pscustomobject]$payload
}

function Get-BifrostSkills([hashtable]$Headers) {
  if ($TestMode) {
    $fixture = Read-JsonFile $TestListResponsePath
    if ($null -eq $fixture) {
      return [pscustomobject]@{ skills = @(); total = 0; limit = 1000; offset = 0 }
    }
    return $fixture
  }
  return Invoke-RestMethod -Uri "$BaseUrl/api/skills?limit=1000&offset=0" -Headers $Headers -TimeoutSec 30
}

function Invoke-BifrostWrite([string]$Method, [string]$Uri, $Payload, [hashtable]$Headers) {
  if ($TestMode) {
    $script:TestWriteCalls += [pscustomobject]@{
      method = $Method
      uri = $Uri
      name = $Payload.name
      payload = $Payload
    }
    return [pscustomobject]@{ id = "test-$($Payload.name)" }
  }

  $body = $Payload | ConvertTo-Json -Depth 100 -Compress
  return Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers -Body $body -ContentType 'application/json' -TimeoutSec 60
}

if (-not $AdminApiKey) {
  $AdminApiKey = Get-EnvValue 'BIFROST_ADMIN_KEY'
}
if (-not $AdminApiKey) {
  $AdminApiKey = Get-EnvValue 'BIFROST_ADMIN_API_KEY'
}

$summary = [ordered]@{
  scanned = @()
  would_create = @()
  created = @()
  would_update = @()
  updated = @()
  skipped_existing = @()
  skipped_missing = @()
  errors = @()
  apply = [bool]$Apply
  update_existing = [bool]$UpdateExisting
}

try {
  $repoRoot = Get-SkillRootPath
  $resolvedSkillRoots = Resolve-SkillRoots (@($SkillRoot) + @($AdditionalSkillRoot))
  $headers = @{}
  if ($AdminApiKey) { $headers['Authorization'] = "Bearer $AdminApiKey" }

  $existingPayload = Get-BifrostSkills $headers
  $existingByName = @{}
  foreach ($skill in @(Get-PropertyValue $existingPayload @('skills'))) {
    $skillName = Get-PropertyValue $skill @('name')
    if (-not $skillName -or $existingByName.ContainsKey([string]$skillName)) { continue }
    $existingByName[[string]$skillName] = $skill
  }

  $requestedSkills = @($IncludeSkill | Sort-Object -Unique)
  foreach ($name in $requestedSkills) {
    if ($name -notin $ApprovedSkills) {
      $summary.errors += [pscustomobject]@{ skill = $name; error = 'skill_not_approved_for_sync' }
      continue
    }

    $skillMatch = Find-SkillInRoots $name $resolvedSkillRoots
    if ($null -eq $skillMatch) {
      $summary.skipped_missing += $name
      continue
    }

    $payload = New-SkillPayload $skillMatch.Path $name $repoRoot $skillMatch.Root
    Assert-NoSecretMaterial $name $payload
    $summary.scanned += [pscustomobject]@{
      name = $name
      file_count = @($payload.files).Count
      source_root = $skillMatch.Root
    }

    $existing = $existingByName[$name]
    if ($null -eq $existing) {
      if (-not $Apply) {
        $summary.would_create += $name
        continue
      }
      if (-not $AdminApiKey -and -not $TestMode) {
        throw 'BIFROST_ADMIN_KEY is required for live create calls'
      }
      $null = Invoke-BifrostWrite 'POST' "$BaseUrl/api/skills" $payload $headers
      $summary.created += $name
      continue
    }

    if (-not $UpdateExisting) {
      $summary.skipped_existing += $name
      continue
    }

    $existingId = Get-PropertyValue $existing @('id', 'skill_id', 'skillId')
    if (-not $existingId) {
      $summary.errors += [pscustomobject]@{ skill = $name; error = 'existing_skill_missing_id' }
      continue
    }

    if (-not $Apply) {
      $summary.would_update += $name
      continue
    }
    if (-not $AdminApiKey -and -not $TestMode) {
      throw 'BIFROST_ADMIN_KEY is required for live update calls'
    }
    $null = Invoke-BifrostWrite 'PUT' "$BaseUrl/api/skills/$existingId" $payload $headers
    $summary.updated += $name
  }
} catch {
  $summary.errors += [pscustomobject]@{ skill = $null; error = $_.Exception.Message }
} finally {
  if ($TestMode -and -not [string]::IsNullOrWhiteSpace($TestWriteLogPath)) {
    ConvertTo-Json -InputObject @($script:TestWriteCalls) -Depth 100 | Set-Content -LiteralPath $TestWriteLogPath -Encoding UTF8
  }
}

$summary | ConvertTo-Json -Depth 100

if (@($summary.errors).Count -gt 0) {
  exit 1
}
exit 0
