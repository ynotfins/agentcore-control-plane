<#
.SYNOPSIS
  Validate current AgentCore PG18-backed state projections without mutating them.

.DESCRIPTION
  PostgreSQL 18 is canonical. This validator checks the four generated files,
  their embedded hashes, read-only attributes, current projection-revision rows,
  and malformed-output sentinels. It does not access legacy PG16, SwarmRecall
  credentials, SwarmVault, or retired projection-state directories.
#>
[CmdletBinding()]
param(
  [string]$ProjectKey = 'agentcore-control-plane',
  [string]$ProjectRoot = 'D:\github\agentcore-control-plane',
  [string]$GlobalStatePath = 'C:\Users\ynotf\.agentcore\GLOBAL_STATE.md',
  [string]$PsqlPath = 'F:\PostgreSQL18\bin\psql.exe',
  [string]$Database = 'agent_core',
  [string]$HostName = '127.0.0.1',
  [int]$Port = 55433,
  [string]$UserName = 'postgres',
  [string]$PasswordEnv = 'AGENT_CORE_POSTGRES_PASSWORD'
)

$ErrorActionPreference = 'Stop'

function Add-Result {
  param([System.Collections.Generic.List[object]]$Results, [string]$Name, [bool]$Passed, [string]$Detail)
  $Results.Add([pscustomobject]@{ name = $Name; passed = $Passed; detail = $Detail }) | Out-Null
}

function Get-ProjectionContentStatus {
  param([string]$Path)
  $bytes = [IO.File]::ReadAllBytes($Path)
  $text = [Text.Encoding]::UTF8.GetString($bytes)
  if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }
  $match = [regex]::Match($text, '(?s)^(.*)\r?\n\r?\nContent SHA-256: ([a-f0-9]{64})\r?\n?$')
  if (-not $match.Success) {
    return [pscustomobject]@{ valid = $false; detail = 'embedded content hash marker missing'; content_hash = '' }
  }
  $body = $match.Groups[1].Value
  $recorded = $match.Groups[2].Value
  $hashBytes = [Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($body))
  $computed = [BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant()
  $invalidControl = $text.ToCharArray() | Where-Object {
    $code = [int]$_
    $code -lt 32 -and $code -notin @(9, 10, 13)
  } | Select-Object -First 1
  $placeholder = $text -match '\$(ProjectKey|projectId|\(@\{)'
  $mojibakeMarker = ([char]0x00E2).ToString() + [char]0x20AC + [char]0x201D
  $mojibake = $text.Contains($mojibakeMarker)
  $valid = ($recorded -eq $computed) -and $null -eq $invalidControl -and -not $placeholder -and -not $mojibake
  return [pscustomobject]@{
    valid = $valid
    content_hash = $recorded
    text = $text
    detail = "hash_match=$($recorded -eq $computed); invalid_control=$($null -ne $invalidControl); placeholder=$placeholder; mojibake=$mojibake"
  }
}

if (-not (Test-Path -LiteralPath $PsqlPath -PathType Leaf)) { throw "psql not found at $PsqlPath" }
$password = [Environment]::GetEnvironmentVariable($PasswordEnv, 'User')
if ([string]::IsNullOrWhiteSpace($password)) { throw "$PasswordEnv is unavailable in Windows User environment." }
$env:PGPASSWORD = $password
try {
  $projectId = (& $PsqlPath -h $HostName -p $Port -U $UserName -d $Database -t -A -v ON_ERROR_STOP=1 -c "SELECT id FROM agentcore.projects WHERE project_key = '$($ProjectKey.Replace("'", "''"))';" 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($projectId)) { throw 'Current AgentCore project row was not found.' }
  $revisionLines = @(& $PsqlPath -h $HostName -p $Port -U $UserName -d $Database -t -A -F "`t" -v ON_ERROR_STOP=1 -c "SELECT kind,target_path,content_sha256,source_revision FROM agentcore.projection_revisions WHERE is_current AND (project_id = '$projectId' OR (project_id IS NULL AND kind = 'global_state')) ORDER BY kind;" 2>&1)
  if ($LASTEXITCODE -ne 0) { throw ($revisionLines -join "`n") }
} finally {
  Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

$revisions = @{}
foreach ($line in $revisionLines) {
  $parts = ([string]$line) -split "`t", 4
  if ($parts.Count -eq 4) { $revisions[$parts[0]] = [pscustomobject]@{ target = $parts[1]; hash = $parts[2]; source = $parts[3] } }
}

$expected = [ordered]@{
  global_state = $GlobalStatePath
  project_state = (Join-Path $ProjectRoot '.agentcore\STATE.md')
  decisions = (Join-Path $ProjectRoot '.agentcore\DECISIONS.md')
  context_index = (Join-Path $ProjectRoot '.agentcore\CONTEXT_INDEX.md')
}
$results = [System.Collections.Generic.List[object]]::new()
foreach ($kind in $expected.Keys) {
  $path = [IO.Path]::GetFullPath($expected[$kind])
  $exists = Test-Path -LiteralPath $path -PathType Leaf
  Add-Result $results "$kind exists" $exists $path
  if (-not $exists) { continue }
  $item = Get-Item -LiteralPath $path -Force
  Add-Result $results "$kind read-only" $item.IsReadOnly "read_only=$($item.IsReadOnly)"
  $content = Get-ProjectionContentStatus -Path $path
  Add-Result $results "$kind content" $content.valid $content.detail
  $revision = $revisions[$kind]
  $revisionOk = $null -ne $revision -and
    [string]::Equals([IO.Path]::GetFullPath($revision.target), $path, [StringComparison]::OrdinalIgnoreCase) -and
    $revision.hash -eq $content.content_hash -and
    $content.text.Contains([string]$revision.source)
  Add-Result $results "$kind revision" $revisionOk $(if ($revision) { "source_revision=$($revision.source)" } else { 'missing current revision' })
}

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 6
if (-not $allPassed) { exit 1 }
