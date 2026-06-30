# Test-AgentCoreProjectAnchor.ps1
# Lightweight read-only guard that the project grounding model is intact and active docs are not drifting
# back to stale authority claims. Does not overbuild. Exit 1 on any failure, else 0.
param(
  [string]$Root = "D:\github\agentcore-control-plane"
)
$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$fail = New-Object System.Collections.Generic.List[string]
$pass = New-Object System.Collections.Generic.List[string]

# 1. Required grounding docs exist.
foreach ($f in 'PROJECT_ANCHOR.md','DOC_AUTHORITY.md','database-plan.md') {
  if (Test-Path -LiteralPath (Join-Path $rootPath $f)) { $pass.Add("present: $f") | Out-Null }
  else { $fail.Add("MISSING required doc: $f") | Out-Null }
}

# 2. Historical docs carry a HISTORICAL banner near the top.
foreach ($f in 'ECOSYSTEM_ARCHITECTURE.md','CLEANUP_AUDIT.md','COMPLETION_REPORT.md') {
  $p = Join-Path $rootPath $f
  if (-not (Test-Path -LiteralPath $p)) { continue }
  $head = (Get-Content -LiteralPath $p -TotalCount 8) -join "`n"
  if ($head -match '(?i)HISTORICAL') { $pass.Add("historical banner: $f") | Out-Null }
  else { $fail.Add("missing HISTORICAL banner near top: $f") | Out-Null }
}

# 3. Active docs must not reassert the removed push-only posture.
foreach ($f in 'PROJECT_ANCHOR.md','CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md','AGENTS.md','AGENT_DATABASE_BOOTSTRAP.md') {
  $p = Join-Path $rootPath $f
  if (-not (Test-Path -LiteralPath $p)) { continue }
  $text = Get-Content -LiteralPath $p -Raw
  if ($text -match 'no_fetch://push-only') { $fail.Add("stale push-only posture in active doc: $f") | Out-Null }
}

# 4. The 'biennial memory projection' typo must not appear anywhere source-controlled.
$typoHits = @(Get-ChildItem -LiteralPath $rootPath -Recurse -File -Include *.md -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\artifacts\\backups\\' } |
  Where-Object { (Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue) -match 'biennial memory projection' })
if ($typoHits.Count -gt 0) { foreach ($h in $typoHits) { $fail.Add("typo 'biennial memory projection' in: " + $h.FullName.Substring($rootPath.Length+1)) | Out-Null } }
else { $pass.Add("no 'biennial memory projection' typo") | Out-Null }

Write-Output "== Test-AgentCoreProjectAnchor =="
$pass | ForEach-Object { Write-Output ("  PASS " + $_) }
if ($fail.Count -gt 0) {
  $fail | ForEach-Object { Write-Output ("  FAIL " + $_) }
  Write-Output "RESULT: FAIL"
  exit 1
}
Write-Output "RESULT: PASS"
exit 0
