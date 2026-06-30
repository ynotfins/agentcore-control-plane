param(
  [string[]]$ScanRoots = @("D:\github", "D:\Autonomy\projects", "D:\Autonomy\repos", "D:\Autonomy"),
  [string[]]$IgnoredRoots = @("D:\Autonomy\Backups"),
  [string]$InvalidAutonomyRoot = "D:\Autonomy"
)

$ErrorActionPreference = "Stop"

function Add-AgentCoreResult {
  param(
    [System.Collections.Generic.List[object]]$Results,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail
  )
  $Results.Add([pscustomobject]@{
    name = $Name
    passed = $Passed
    detail = $Detail
  }) | Out-Null
}

function Test-IsGitRepo {
  param([string]$Path)
  try {
    $output = git -C $Path rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return ([IO.Path]::GetFullPath((([string]$output).Trim()))).TrimEnd('\')
  } catch {
    return $null
  }
}

function Test-IsIgnoredPath {
  param(
    [string]$Path,
    [string[]]$Ignored
  )
  foreach ($root in $Ignored) {
    if ([string]::IsNullOrWhiteSpace($root)) { continue }
    $normalized = [IO.Path]::GetFullPath($root).TrimEnd('\')
    if ($Path.StartsWith($normalized, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }
  return $false
}

$results = [System.Collections.Generic.List[object]]::new()
$found = New-Object System.Collections.Generic.List[string]
$invalid = New-Object System.Collections.Generic.List[string]
$repoScoped = New-Object System.Collections.Generic.List[string]

foreach ($root in $ScanRoots) {
  if (-not (Test-Path -LiteralPath $root)) { continue }
  $resolvedRoot = (Resolve-Path -LiteralPath $root).Path
  $items = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Directory -Filter ".context-fabric" -ErrorAction SilentlyContinue)
  foreach ($item in $items) {
    $path = $item.FullName
    if (Test-IsIgnoredPath -Path $path -Ignored $IgnoredRoots) {
      continue
    }
    $found.Add($path) | Out-Null
    $parent = Split-Path -Parent $path
    $gitTop = Test-IsGitRepo -Path $parent
    if (-not $gitTop) {
      $invalid.Add("$path [parent is not a git repo]") | Out-Null
      continue
    }
    $parentNormalized = ([IO.Path]::GetFullPath($parent)).TrimEnd('\')
    if ($gitTop -ne $parentNormalized) {
      $invalid.Add("$path [expected at repo root $gitTop]") | Out-Null
      continue
    }
    $repoScoped.Add($parentNormalized) | Out-Null
  }
}

$invalidAutonomyPath = Join-Path $InvalidAutonomyRoot ".context-fabric"
$invalidAutonomyDetected = Test-Path -LiteralPath $invalidAutonomyPath
$autonomyDetail = if ($invalidAutonomyDetected) { $invalidAutonomyPath } else { "not present" }

Add-AgentCoreResult $results "context-fabric roots discovered" ($found.Count -gt 0) (($found -join "; ") -replace "^$", "none found")
Add-AgentCoreResult $results "invalid non-repo context-fabric roots" ($invalid.Count -eq 0) (($invalid -join "; ") -replace "^$", "none")
Add-AgentCoreResult $results "repo-scoped context-fabric roots" ($repoScoped.Count -gt 0) ((@($repoScoped | Sort-Object -Unique) -join "; ") -replace "^$", "none")
Add-AgentCoreResult $results "Autonomy global context-fabric cleared" (-not $invalidAutonomyDetected) $autonomyDetail

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 6
if (-not $allPassed) {
  exit 1
}
