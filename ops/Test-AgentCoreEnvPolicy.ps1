param(
  [string]$Root = "D:\github\agentcore-control-plane",
  [switch]$WriteReport
)

$ErrorActionPreference = "Stop"

function Add-Result {
  param(
    [System.Collections.Generic.List[object]]$Results,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail
  )

  $Results.Add([pscustomobject]@{
    name   = $Name
    passed = $Passed
    detail = $Detail
  }) | Out-Null
}

function Get-RelativePath {
  param(
    [string]$RootPath,
    [string]$FullPath
  )

  if ($FullPath.StartsWith($RootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $FullPath.Substring($RootPath.Length).TrimStart("\")
  }

  return $FullPath
}

function Read-TextIfSafe {
  param([string]$Path)

  $extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
  if ($extension -in @(".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".7z", ".pyc", ".pyo", ".db", ".sqlite", ".sqlite3")) {
    return $null
  }

  return Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
}

$results = [System.Collections.Generic.List[object]]::new()
$rootPath = (Resolve-Path -LiteralPath $Root).Path

$trackedRelative = @(& git -C $rootPath ls-files)
if ($LASTEXITCODE -ne 0) {
  throw "git ls-files failed for $rootPath"
}

$trackedPaths = @(
  foreach ($rel in $trackedRelative) {
    Join-Path $rootPath $rel
  }
)
$scanExclusions = @(
  "ops\Test-AgentCoreEnvPolicy.ps1"
)

$envFiles = @(
  Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File |
    Where-Object {
      $_.FullName -notmatch "\\.git\\" -and
      $_.Name -match "^\.env(\..+)?$"
    } |
    ForEach-Object { Get-RelativePath -RootPath $rootPath -FullPath $_.FullName }
)
$envFilesDetail = if ($envFiles.Count) { $envFiles -join ", " } else { "no .env files found inside repo" }
Add-Result $results ".env files absent" ($envFiles.Count -eq 0) $envFilesDetail

$secretPatterns = @(
  @{
    Name = "password assignment"
    Regex = '(?im)\b(?:password|passwd|pwd)\b\s*[:=]\s*["'']?(?!\$\{(?:env|ENV):)(?!\$env:)(?!process\.env\.)(?!AGENT_CORE_[A-Z0-9_]+)(?!<[^>]+>)[A-Za-z0-9!@#\$%\^&\*\(\)_\+\-=\{\}\[\]:;,.?/\\|]{6,}'
  },
  @{
    Name = "postgres credential URI"
    Regex = '(?i)postgres(?:ql)?://[^/\s:@]+:[^@\s]+@'
  },
  @{
    Name = "PGPASSWORD literal"
    Regex = '(?im)(?:\$env:)?PGPASSWORD\b\s*[:=]\s*["'']?(?!\$\{\{(?:env|ENV):)(?!\$\{(?:env|ENV):)(?!\$env:)(?!process\.env\.)(?!AGENT_CORE_[A-Z0-9_]+)(?!\[Environment\]::GetEnvironmentVariable)(?!GetEnvironmentVariable\()[^\s"'']{4,}'
  },
  @{
    Name = "AgentCore password literal"
    Regex = '(?im)AGENT_CORE_[A-Z0-9_]*PASSWORD["'']?\s*[:=]\s*["''](?!\$\{\{(?:env|ENV):)(?!\$\{(?:env|ENV):)(?!\$env:)(?!process\.env\.)(?!AGENT_CORE_[A-Z0-9_]+)(?!\[Environment\]::GetEnvironmentVariable)(?!GetEnvironmentVariable\()[^"'']+["'']'
  }
)

$secretFindings = [System.Collections.Generic.List[string]]::new()
foreach ($path in $trackedPaths) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    continue
  }
  $relativePath = Get-RelativePath -RootPath $rootPath -FullPath $path
  if ($scanExclusions -contains $relativePath) {
    continue
  }

  $text = Read-TextIfSafe -Path $path
  if ([string]::IsNullOrEmpty($text)) {
    continue
  }

  foreach ($pattern in $secretPatterns) {
    if ($text -match $pattern.Regex) {
      $secretFindings.Add("$relativePath [$($pattern.Name)]") | Out-Null
      break
    }
  }
}
$secretDetail = if ($secretFindings.Count) { ($secretFindings | Sort-Object -Unique) -join ", " } else { "no raw password-like literals detected" }
Add-Result $results "no password-like literals in tracked files" ($secretFindings.Count -eq 0) $secretDetail

$dotenvExtensions = @(".ps1", ".py", ".json", ".yaml", ".yml", ".toml", ".js", ".cjs", ".mjs", ".ts", ".tsx", ".sh")
$dotenvRegexes = @(
  '(?im)^\s*import\s+dotenv\b',
  '(?im)^\s*from\s+dotenv\s+import\b',
  '(?im)\bdotenv\.config\s*\(',
  '(?im)\bload_dotenv\s*\(',
  '(?im)\brequire\s*\(\s*["'']dotenv["'']\s*\)',
  '(?im)["'']dotenv["'']\s*:'
)
$dotenvFindings = [System.Collections.Generic.List[string]]::new()
foreach ($path in $trackedPaths) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    continue
  }
  $relativePath = Get-RelativePath -RootPath $rootPath -FullPath $path
  if ($scanExclusions -contains $relativePath) {
    continue
  }

  $extension = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
  if ($dotenvExtensions -notcontains $extension) {
    continue
  }

  $text = Read-TextIfSafe -Path $path
  if ([string]::IsNullOrEmpty($text)) {
    continue
  }

  foreach ($regex in $dotenvRegexes) {
    if ($text -match $regex) {
      $dotenvFindings.Add($relativePath) | Out-Null
      break
    }
  }
}
$dotenvDetail = if ($dotenvFindings.Count) { ($dotenvFindings | Sort-Object -Unique) -join ", " } else { "no dotenv imports/usages detected in tracked code/config files" }
Add-Result $results "no dotenv usage for AgentCore" ($dotenvFindings.Count -eq 0) $dotenvDetail

$requiredEnv = @(
  [pscustomobject]@{ Name = "AGENT_CORE_AGENT_ADMIN_PASSWORD"; Expected = $null },
  [pscustomobject]@{ Name = "AGENT_CORE_AGENT_INGEST_PASSWORD"; Expected = $null },
  [pscustomobject]@{ Name = "AGENT_CORE_AGENT_READ_PASSWORD"; Expected = $null },
  [pscustomobject]@{ Name = "AGENT_CORE_POSTGRES_PASSWORD"; Expected = $null },
  [pscustomobject]@{ Name = "AGENT_CORE_PGPASSWORD"; Expected = $null },
  [pscustomobject]@{ Name = "AGENT_CORE_PGUSER"; Expected = "agent_ingest" }
)

$missingDurable = [System.Collections.Generic.List[string]]::new()
$missingProcess = [System.Collections.Generic.List[string]]::new()
$valueMismatches = [System.Collections.Generic.List[string]]::new()
foreach ($item in $requiredEnv) {
  $processValue = [Environment]::GetEnvironmentVariable($item.Name, "Process")
  $userValue = [Environment]::GetEnvironmentVariable($item.Name, "User")
  $machineValue = [Environment]::GetEnvironmentVariable($item.Name, "Machine")
  $durableValue = if (-not [string]::IsNullOrEmpty($userValue)) { $userValue } else { $machineValue }

  if ([string]::IsNullOrEmpty($durableValue)) {
    $missingDurable.Add($item.Name) | Out-Null
  }
  if ([string]::IsNullOrEmpty($processValue)) {
    $missingProcess.Add($item.Name) | Out-Null
  }
  if ($item.Expected) {
    foreach ($pair in @(
      [pscustomobject]@{ Scope = "durable"; Value = $durableValue },
      [pscustomobject]@{ Scope = "process"; Value = $processValue }
    )) {
      if (-not [string]::IsNullOrEmpty($pair.Value) -and $pair.Value -ne $item.Expected) {
        $valueMismatches.Add("$($item.Name) ($($pair.Scope))") | Out-Null
      }
    }
  }
}
$durableDetail = if ($missingDurable.Count) { "missing durable vars: " + ($missingDurable -join ", ") } else { "all required vars exist in User or Machine scope" }
$processDetail = if ($missingProcess.Count) { "missing from current process: " + ($missingProcess -join ", ") } else { "all required vars visible in current process" }
$valueDetail = if ($valueMismatches.Count) { "unexpected value in: " + ($valueMismatches -join ", ") } else { "AGENT_CORE_PGUSER resolves to agent_ingest where present" }
Add-Result $results "required Windows env vars exist" ($missingDurable.Count -eq 0) $durableDetail
Add-Result $results "current session sees required env vars" ($missingProcess.Count -eq 0) $processDetail
Add-Result $results "AGENT_CORE_PGUSER policy value" ($valueMismatches.Count -eq 0) $valueDetail

$gatewayChecks = @(
  [pscustomobject]@{
    Path = "scripts\mcp_control_plane.py"
    UserPattern = 'AGENT_CORE_PGUSER": "agent_ingest"'
    PasswordPattern = 'AGENT_CORE_PGPASSWORD": "\$\{ENV:AGENT_CORE_AGENT_INGEST_PASSWORD\}"'
  },
  [pscustomobject]@{
    Path = "renderers\cursor-global.mcp.json"
    UserPattern = '"AGENT_CORE_PGUSER": "agent_ingest"'
    PasswordPattern = '"AGENT_CORE_PGPASSWORD": "\$\{env:AGENT_CORE_AGENT_INGEST_PASSWORD\}"'
  },
  [pscustomobject]@{
    Path = "renderers\open-interpreter.config.fragment.json"
    UserPattern = '"AGENT_CORE_PGUSER": "agent_ingest"'
    PasswordPattern = '"AGENT_CORE_PGPASSWORD": "\$\{env:AGENT_CORE_AGENT_INGEST_PASSWORD\}"'
  },
  [pscustomobject]@{
    Path = "renderers\openclaw.openclaw.fragment.json"
    UserPattern = '"AGENT_CORE_PGUSER": "agent_ingest"'
    PasswordPattern = '"AGENT_CORE_PGPASSWORD": "\$\{env:AGENT_CORE_AGENT_INGEST_PASSWORD\}"'
  },
  [pscustomobject]@{
    Path = "renderers\minimax.mcp.json"
    UserPattern = '"AGENT_CORE_PGUSER": "agent_ingest"'
    PasswordPattern = '"AGENT_CORE_PGPASSWORD": "\$\{env:AGENT_CORE_AGENT_INGEST_PASSWORD\}"'
  },
  [pscustomobject]@{
    Path = "supervisor\servers.json"
    UserPattern = '"AGENT_CORE_PGUSER": "agent_ingest"'
    PasswordPattern = '"AGENT_CORE_PGPASSWORD": "\$\{ENV:AGENT_CORE_AGENT_INGEST_PASSWORD\}"'
  },
  [pscustomobject]@{
    Path = "supervisor\servers.yaml"
    UserPattern = 'AGENT_CORE_PGUSER: agent_ingest'
    PasswordPattern = 'AGENT_CORE_PGPASSWORD: "\$\{ENV:AGENT_CORE_AGENT_INGEST_PASSWORD\}"'
  }
)

$gatewayFindings = [System.Collections.Generic.List[string]]::new()
foreach ($check in $gatewayChecks) {
  $path = Join-Path $rootPath $check.Path
  if (-not (Test-Path -LiteralPath $path)) {
    $gatewayFindings.Add("$($check.Path) [missing]") | Out-Null
    continue
  }

  $text = Get-Content -LiteralPath $path -Raw
  if ($text -notmatch $check.UserPattern) {
    $gatewayFindings.Add("$($check.Path) [AGENT_CORE_PGUSER]") | Out-Null
  }
  if ($text -notmatch $check.PasswordPattern) {
    $gatewayFindings.Add("$($check.Path) [AGENT_CORE_PGPASSWORD]") | Out-Null
  }
}
$gatewayDetail = if ($gatewayFindings.Count) { ($gatewayFindings | Sort-Object -Unique) -join ", " } else { "gateway source and rendered configs use env-var references only" }
Add-Result $results "gateway config uses env references" ($gatewayFindings.Count -eq 0) $gatewayDetail

$allPassed = -not ($results | Where-Object { -not $_.passed })
$report = [pscustomobject]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  root = $rootPath
  passed = [bool]$allPassed
  results = $results
}

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# AgentCore Environment Policy Report") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("Generated: $($report.generated_at)") | Out-Null
$lines.Add("Root: ``$rootPath``") | Out-Null
$lines.Add("Overall: $(if ($allPassed) { "PASS" } else { "FAIL" })") | Out-Null
$lines.Add("") | Out-Null
foreach ($result in $results) {
  $status = if ($result.passed) { "PASS" } else { "FAIL" }
  $lines.Add("- $status - $($result.name): $($result.detail)") | Out-Null
}

if ($WriteReport) {
  $artifactDir = Join-Path $rootPath "artifacts"
  New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null
  $jsonPath = Join-Path $artifactDir "env-policy-report.json"
  $mdPath = Join-Path $artifactDir "env-policy-report.md"
  $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding utf8
  $lines | Set-Content -LiteralPath $mdPath -Encoding utf8
}

$lines | ForEach-Object { Write-Output $_ }

if ($allPassed) {
  if ($WriteReport) {
    Write-Output "PASS: AgentCore env policy validation succeeded. Report written."
  } else {
    Write-Output "PASS: AgentCore env policy validation succeeded. Dry-run only; no report files written."
  }
  exit 0
}

if ($WriteReport) {
  Write-Output "FAIL: AgentCore env policy validation failed. Report written."
} else {
  Write-Output "FAIL: AgentCore env policy validation failed. Dry-run only; no report files written."
}
exit 1
