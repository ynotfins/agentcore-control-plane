param(
  [string]$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path,
  [string]$TranscriptRoot,
  [string]$OutputPath
)

$ErrorActionPreference = "Stop"

function Get-ExistingTranscriptRoot {
  param([string]$IndexPath)

  if (-not (Test-Path -LiteralPath $IndexPath)) { return $null }
  try {
    $existing = Get-Content -LiteralPath $IndexPath -Raw | ConvertFrom-Json
    if ($existing.transcriptRoot) { return [string]$existing.transcriptRoot }
  }
  catch {
    return $null
  }
  return $null
}

function Test-UnsafeTranscript {
  param([System.IO.FileInfo]$File)

  $pathPatterns = @(
    "\\credentials\\",
    "\\secrets\\",
    "\\reports\\_raw\\",
    "\\raw-config\\",
    "\\config-dump\\",
    "\\backups?\\"
  )
  foreach ($pattern in $pathPatterns) {
    if ($File.FullName -match $pattern) { return "unsafe-path" }
  }

  try {
    $text = Get-Content -LiteralPath $File.FullName -Raw -ErrorAction Stop
  }
  catch {
    return "unreadable"
  }

  $secretPatterns = @(
    "sk-[A-Za-z0-9_-]{20,}",
    "gh[pousr]_[A-Za-z0-9_]{20,}",
    "xox[baprs]-[A-Za-z0-9-]{20,}",
    "AIza[0-9A-Za-z_-]{20,}",
    "Bearer\s+(?!\$\{)[A-Za-z0-9._~+/=-]{20,}",
    "Token\s+(?!\$\{)[A-Za-z0-9._~+/=-]{20,}",
    "pat=(?!\$\{)[A-Za-z0-9._~+/=-]{10,}",
    "(?i)(password|api[_-]?key|secret|token)\s*[:=]\s*[`"']?[A-Za-z0-9._~+/=-]{20,}",
    "-----BEGIN (?:RSA |OPENSSH |EC |DSA |)?PRIVATE KEY-----"
  )

  foreach ($pattern in $secretPatterns) {
    if ($text -match $pattern) { return "secret-scan" }
  }

  return $null
}

if (-not $OutputPath) {
  $OutputPath = Join-Path $Root ".cursor\hooks\state\continual-learning-index.json"
}

if (-not $TranscriptRoot) {
  $TranscriptRoot = Get-ExistingTranscriptRoot -IndexPath $OutputPath
}

if (-not $TranscriptRoot) {
  $projectId = ((Resolve-Path -LiteralPath $Root).Path -replace "^[A-Za-z]:\\", "") -replace "[\\/]", "-"
  $TranscriptRoot = Join-Path $env:USERPROFILE ".cursor\projects\$projectId\agent-transcripts"
}

$entries = [ordered]@{}
$counts = [ordered]@{
  active = 0
  quarantined = 0
  excluded = 0
}

if (Test-Path -LiteralPath $TranscriptRoot) {
  $rootFull = (Resolve-Path -LiteralPath $TranscriptRoot).Path
  $files = Get-ChildItem -LiteralPath $rootFull -Recurse -File -Filter "*.jsonl" | Sort-Object FullName
  foreach ($file in $files) {
    $relative = $file.FullName.Substring($rootFull.Length).TrimStart("\", "/") -replace "\\", "/"
    $unsafeReason = Test-UnsafeTranscript -File $file
    $retrievalStatus = "active"
    if ($unsafeReason -eq "unreadable") {
      $retrievalStatus = "excluded"
    }
    elseif ($unsafeReason) {
      $retrievalStatus = "quarantined"
    }

    $counts[$retrievalStatus]++
    $entry = [ordered]@{
      sourcePath = $file.FullName
      authorityClass = "evidence_only"
      mtimeUtc = $file.LastWriteTimeUtc.ToString("o")
      size = $file.Length
      sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant()
      retrievalStatus = $retrievalStatus
    }
    if ($unsafeReason) {
      $entry.quarantineReason = $unsafeReason
    }
    $entries[$relative] = $entry
  }
}

$index = [ordered]@{
  version = 2
  processedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  workspace = (Resolve-Path -LiteralPath $Root).Path
  transcriptRoot = $TranscriptRoot
  authorityClassDefault = "evidence_only"
  authorityPolicy = "Agent transcripts are evidence-only and can never override PROJECT_ANCHOR.md, DOC_AUTHORITY.md, BLUEPRINT.md, STATE.md, or another current authority source."
  retrievalOnly = $true
  startupContextEligible = $false
  normalRetrievalStatuses = @("active")
  retrievalPolicy = "Normal retrieval uses active entries only. Quarantined and excluded entries are ignored by normal retrieval and are never injected wholesale into startup context."
  counts = $counts
  transcripts = $entries
}

$outputDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$index | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
Write-Output "Wrote $OutputPath"
Write-Output ("active={0} quarantined={1} excluded={2}" -f $counts.active, $counts.quarantined, $counts.excluded)
