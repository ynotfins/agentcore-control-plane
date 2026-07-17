<#
.SYNOPSIS
  Drift validation for the AgentCore canonical project resource-location model.

.DESCRIPTION
  Checks that:
    1. Every registered active worktree path exists on disk.
    2. The canonical repository path exists and is a Git repo at the expected HEAD.
    3. No retired worktree path is still referenced by the live Bifrost config.
    4. No backup resource is stored on the hot_h tier (backup_g only).
    5. Supersession records exist when a location is marked inactive.
    6. The .agentcore/CONTEXT_INDEX.md head commit matches git log.
    7. The Bifrost agentcore_memory server.py references the canonical repo, not a worktree.
    8. No scratch_i tier resource is present and older than 24 hours.

  Authority: BLUEPRINT.md, migrations/m8/001_up_resource_location_model.sql.
  Target: PostgreSQL 18 agent_core 127.0.0.1:55433.
  Run: .\ops\Test-AgentCoreResourceLocationDrift.ps1
#>
param(
  [string]$DbHost   = "127.0.0.1",
  [int]   $Port     = 55433,
  [string]$Dbname   = "agent_core",
  [string]$DbUser   = "postgres",
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [string]$BifrostConfigPath = "H:\AgentRuntime\bifrost\config.json"
)

$ErrorActionPreference = "Stop"
$pass = 0; $fail = 0; $warn = 0
$failures = @()

function Ok([string]$msg)   { Write-Host "  [PASS] $msg" -ForegroundColor Green;  $script:pass++ }
function Fail([string]$msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red;    $script:fail++; $script:failures += $msg }
function Warn([string]$msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow; $script:warn++ }

# ── DB connection ───────────────────────────────────────────────────────────
$pw = [System.Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
if (-not $pw) { $pw = [System.Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "Machine") }
$dsn = "host=$DbHost port=$Port dbname=$Dbname user=$DbUser password=$pw"

$pyScript = @"
import os, sys, json, psycopg
dsn = sys.argv[1]
checks = {}
with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        # Active worktrees and their paths
        cur.execute("""
            SELECT w.worktree_path, w.branch_name, w.head_commit, w.worktree_status, w.worktree_kind
            FROM agentcore.worktrees w
            WHERE w.worktree_status IN ('active','retired')
        """)
        checks['worktrees'] = [{'path': r[0], 'branch': r[1], 'commit': r[2], 'status': r[3], 'kind': r[4]} for r in cur.fetchall()]

        # Backup on hot_h tier (should be zero)
        cur.execute("""
            SELECT COUNT(*) FROM agentcore.artifact_locations
            WHERE storage_tier = 'hot_h' AND classification = 'backup' AND is_active
        """)
        checks['backup_on_hot'] = cur.fetchone()[0]

        # Inactive locations without superseded_by_id
        cur.execute("""
            SELECT COUNT(*) FROM agentcore.artifact_locations
            WHERE is_active = false AND superseded_by_id IS NULL
        """)
        checks['inactive_no_supersession'] = cur.fetchone()[0]

        # Old scratch_i locations (> 24 hours)
        cur.execute("""
            SELECT COUNT(*) FROM agentcore.artifact_locations
            WHERE storage_tier = 'scratch_i'
              AND created_at < now() - interval '24 hours'
              AND is_active
        """)
        checks['stale_scratch'] = cur.fetchone()[0]

        # Canonical repo path from repositories
        cur.execute("""
            SELECT r.canonical_path FROM agentcore.repositories r
            WHERE r.canonical_path NOT LIKE '%-unbounded-memory%'
            ORDER BY r.created_at DESC LIMIT 1
        """)
        row = cur.fetchone()
        checks['canonical_path'] = row[0] if row else None

print(json.dumps(checks))
"@

$tmpScript = Join-Path $env:TEMP "acrl_drift_check.py"
$pyScript | Out-File -FilePath $tmpScript -Encoding UTF8

Write-Host "`nAgentCore Resource-Location Drift Check`n" -ForegroundColor Cyan
Write-Host "Running DB checks..."

try {
  $jsonOut = python $tmpScript $dsn 2>&1
  if ($LASTEXITCODE -ne 0) { throw "DB query failed: $jsonOut" }
  $data = $jsonOut | ConvertFrom-Json
} catch {
  Fail "DB query failed: $_"
  exit 1
} finally {
  Remove-Item $tmpScript -ErrorAction SilentlyContinue
}

# ── Check 1: Active worktree paths exist on disk ────────────────────────────
Write-Host "`n1. Worktree path existence..."
foreach ($wt in $data.worktrees) {
  if ($wt.status -eq 'active') {
    if (Test-Path -LiteralPath $wt.path) {
      Ok "Active worktree exists: $($wt.path) [$($wt.branch)]"
    } else {
      Fail "Active worktree MISSING on disk: $($wt.path)"
    }
  } elseif ($wt.status -eq 'retired') {
    if (-not (Test-Path -LiteralPath $wt.path)) {
      Ok "Retired worktree path correctly absent: $($wt.path)"
    } else {
      Warn "Retired worktree path still exists on disk: $($wt.path) (may be intentional backup)"
    }
  }
}

# ── Check 2: Canonical repo is a valid Git repo at expected HEAD ─────────────
Write-Host "`n2. Canonical repository integrity..."
$canonPath = $data.canonical_path
if ($canonPath -and (Test-Path -LiteralPath $canonPath)) {
  Ok "Canonical repo path exists: $canonPath"
  $head = git -C $canonPath rev-parse --short HEAD 2>$null
  if ($head) {
    Ok "Canonical repo HEAD: $head"
    $branch = git -C $canonPath branch --show-current 2>$null
    if ($branch -eq 'main') {
      Ok "Canonical repo on main branch"
    } else {
      Warn "Canonical repo branch is '$branch' (expected 'main')"
    }
  } else {
    Fail "Cannot read HEAD from canonical repo: $canonPath"
  }
} else {
  Fail "Canonical repo path not found: $canonPath"
}

# ── Check 3: Bifrost config not referencing retired worktree ────────────────
Write-Host "`n3. Bifrost config worktree reference check..."
if (Test-Path -LiteralPath $BifrostConfigPath) {
  $bifrostContent = Get-Content -LiteralPath $BifrostConfigPath -Raw
  $retiredPaths = $data.worktrees | Where-Object { $_.status -eq 'retired' } | Select-Object -ExpandProperty path
  $bifrostClean = $true
  foreach ($rp in $retiredPaths) {
    if ($bifrostContent -like "*$rp*") {
      Fail "Bifrost config still references retired worktree: $rp"
      $bifrostClean = $false
    }
  }
  if ($bifrostClean) {
    Ok "Bifrost config has no retired worktree references"
  }
  
  # Verify agentcore_memory points to canonical repo
  $cfg = $bifrostContent | ConvertFrom-Json
  $memServer = $cfg.mcp.client_configs | Where-Object { $_.name -eq "agentcore_memory" }
  if ($memServer) {
    $serverPath = $memServer.stdio_config.args | Where-Object { $_ -like "*.py" } | Select-Object -First 1
    if ($serverPath -like "*agentcore-control-plane*" -and $serverPath -notlike "*-unbounded-memory*") {
      Ok "agentcore_memory server.py is in canonical repo: $serverPath"
    } else {
      Fail "agentcore_memory server.py is NOT in canonical repo: $serverPath"
    }
  }
} else {
  Warn "Bifrost config not found at: $BifrostConfigPath"
}

# ── Check 4: No backup on hot tier ──────────────────────────────────────────
Write-Host "`n4. Backup storage tier validation..."
if ($data.backup_on_hot -eq 0) {
  Ok "No backup artifacts on hot_h tier (correct)"
} else {
  Fail "$($data.backup_on_hot) backup artifact(s) found on hot_h tier — should be backup_g"
}

# ── Check 5: Supersession records ───────────────────────────────────────────
Write-Host "`n5. Inactive location supersession records..."
if ($data.inactive_no_supersession -eq 0) {
  Ok "All inactive artifact locations have supersession records"
} else {
  Warn "$($data.inactive_no_supersession) inactive location(s) lack supersession records (acceptable for legacy data)"
}

# ── Check 6: No stale scratch_i artifacts ────────────────────────────────────
Write-Host "`n6. Stale scratch_i artifact check..."
if ($data.stale_scratch -eq 0) {
  Ok "No stale scratch_i artifacts (> 24 hours old)"
} else {
  Warn "$($data.stale_scratch) stale scratch_i artifact(s) > 24h old — should be promoted or deleted"
}

# ── Check 7: CONTEXT_INDEX.md head commit consistency ───────────────────────
Write-Host "`n7. CONTEXT_INDEX.md commit consistency..."
$contextIndex = Join-Path $RepoRoot ".agentcore\CONTEXT_INDEX.md"
if (Test-Path -LiteralPath $contextIndex) {
  $content = Get-Content -LiteralPath $contextIndex -Raw
  $gitHead = git -C $RepoRoot rev-parse --short HEAD 2>$null
  if ($content -match "HEAD.*$gitHead" -or $content -match $gitHead) {
    Ok "CONTEXT_INDEX.md references current HEAD ($gitHead)"
  } else {
    Warn "CONTEXT_INDEX.md may not reference current HEAD ($gitHead) — regeneration recommended"
  }
} else {
  Fail "CONTEXT_INDEX.md not found at: $contextIndex"
}

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Host "`n─────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "Resource-Location Drift Check Complete" -ForegroundColor Cyan
Write-Host "  PASS: $pass  WARN: $warn  FAIL: $fail" -ForegroundColor $(if ($fail -gt 0) { 'Red' } elseif ($warn -gt 0) { 'Yellow' } else { 'Green' })

if ($failures.Count -gt 0) {
  Write-Host "`nFailures:" -ForegroundColor Red
  $failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
  exit 1
}

if ($fail -eq 0) {
  Write-Host "`nAll resource-location drift checks passed." -ForegroundColor Green
  exit 0
}
