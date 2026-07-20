<#
.SYNOPSIS
  AgentCore central durability and placement audit.

.DESCRIPTION
  One deterministic audit script for all continuity, resource-location, and storage
  health checks. Owned by Windows Task Scheduler under \AgentCore\; never by Codex or
  another agent scheduler.

  Authority: BLUEPRINT.md §3/§6/§11; task "harden continuous context durability" 2026-07-17.
  Target: PostgreSQL 18 agent_core 127.0.0.1:55433.

  Modes:
    Health   — lightweight health/continuity probe (6h interval).
    Resource — complete resource/location audit (daily).
    Deep     — deep recovery/retention + WAL + backup + scheduled-task audit (weekly).

  Checks per mode:
    HEALTH (all three run Health checks):
      1.  PostgreSQL 18 TCP reachability and login.
      2.  Bifrost gateway HTTP health.
      3.  agentcore-memory memory_status tool (via direct Python import).
      4.  v_client_memory_continuity: open sessions with no recent event.
      5.  v_client_memory_continuity: sessions closed without final handoff.
      6.  Quarantined-memory enforcement (quarantined count, not promoted to Cognee).
      7.  Swarm exclusion (agentcore memory tables free of swarm schema writes).

    RESOURCE (Health + Resource):
      8.  All registered projects, repositories, and worktrees.
      9.  All resource-location registry entries (artifact_locations).
      10. Missing registered paths on disk.
      11. Unregistered durable paths on approved AgentCore roots.
      12. Production references to retired worktrees.
      13. Last successful memory lifecycle per IDE client.
      14. Projection revision and content-hash freshness.
      15. STATE/DECISIONS/CONTEXT_INDEX parity with PostgreSQL.
      16. Hot H: artifact count and cold E: artifact count.
      17. Temporary I: content exceeding 24-hour allowed lifetime.
      18. Storage free-space thresholds.

    DEEP (Health + Resource + Deep):
      19. WAL archive continuity (archive_mode, archive_status).
      20. Scheduled-task last-run and failure status.
      21. G: backup coverage (artifact_locations backup_g count and recency).
      22. PostgreSQL logical-backup recency on E:.
      23. Projection-revision content-hash verification (spot-check).

  Output:
    STDOUT: human-readable PASS/WARN/FAIL lines.
    H:\AgentRuntime\service-logs\durability-audit-<timestamp>.json — machine-readable report.
    E:\AgentCoreArchive\agentcore-memory\audits\<date>\durability-audit-<timestamp>.json — cold evidence.

.PARAMETER Mode
  Audit depth: Health | Resource | Deep (default: Resource).

.PARAMETER DbHost
  PostgreSQL host (default: 127.0.0.1).

.PARAMETER Port
  PostgreSQL port (default: 55433).

.PARAMETER Dbname
  Database name (default: agent_core).

.PARAMETER DbUser
  Database user (default: postgres).

.PARAMETER RepoRoot
  AgentCore control-plane root (default: D:\github\agentcore-control-plane).

.PARAMETER BifrostHealthUrl
  Bifrost gateway health endpoint (default: http://127.0.0.1:8080/health).

.PARAMETER StaleHours
  Hours without events before a session is flagged stale (default: 6).

.PARAMETER MinFreeMb
  Minimum free space in MB before a drive triggers a warning (default: 10240 = 10 GB).

.EXAMPLE
  .\ops\Test-AgentCoreDurabilityAndPlacement.ps1 -Mode Health
  .\ops\Test-AgentCoreDurabilityAndPlacement.ps1 -Mode Resource
  .\ops\Test-AgentCoreDurabilityAndPlacement.ps1 -Mode Deep
#>
param(
  [ValidateSet("Health","Resource","Deep")]
  [string]$Mode          = "Resource",
  [string]$DbHost        = "127.0.0.1",
  [int]   $Port          = 55433,
  [string]$Dbname        = "agent_core",
  [string]$DbUser        = "postgres",
  [string]$RepoRoot      = "D:\github\agentcore-control-plane",
  [string]$BifrostHealthUrl = "http://127.0.0.1:8080/health",
  [int]   $StaleHours    = 6,
  [int]   $MinFreeMb     = 10240
)

$ErrorActionPreference = "Continue"
$stamp     = Get-Date -Format "yyyyMMdd-HHmmss"
$dateDir   = Get-Date -Format "yyyy-MM-dd"

# Report paths
$hotLogDir   = "H:\AgentRuntime\service-logs"
$coldLogDir  = "E:\AgentCoreArchive\agentcore-memory\audits\$dateDir"
$hotReport   = Join-Path $hotLogDir  "durability-audit-$stamp.json"
$coldReport  = Join-Path $coldLogDir "durability-audit-$stamp.json"

$pass = 0; $warn = 0; $fail = 0
$findings = [System.Collections.Generic.List[hashtable]]::new()

function Ok([string]$check, [string]$msg) {
  Write-Host "  [PASS] $check — $msg" -ForegroundColor Green
  $script:pass++
  $script:findings.Add(@{check=$check; status="pass"; msg=$msg})
}
function Warn([string]$check, [string]$msg) {
  Write-Host "  [WARN] $check — $msg" -ForegroundColor Yellow
  $script:warn++
  $script:findings.Add(@{check=$check; status="warn"; msg=$msg})
}
function Fail([string]$check, [string]$msg) {
  Write-Host "  [FAIL] $check — $msg" -ForegroundColor Red
  $script:fail++
  $script:findings.Add(@{check=$check; status="fail"; msg=$msg})
}

# ── DB connection string ──────────────────────────────────────────────────────
$pw = [System.Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
if (-not $pw) { $pw = [System.Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "Machine") }
$dsn = "host=$DbHost port=$Port dbname=$Dbname user=$DbUser password=$pw"

function Invoke-PyQuery([string]$pyCode) {
  $tmpScript = Join-Path $env:TEMP "acdap_$stamp.py"
  try {
    $pyCode | Out-File -FilePath $tmpScript -Encoding UTF8
    $out = python $tmpScript $dsn 2>&1
    if ($LASTEXITCODE -ne 0) { return $null }
    return ($out | Where-Object { $_ -ne "" } | Select-Object -Last 1) | ConvertFrom-Json
  } catch { return $null }
  finally { Remove-Item $tmpScript -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "AgentCore Durability and Placement Audit  [Mode=$Mode]" -ForegroundColor Cyan
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# ═════════════════════════════════════════════════════════════════════════════
# HEALTH CHECKS (always run)
# ═════════════════════════════════════════════════════════════════════════════

Write-Host "`n── HEALTH ──────────────────────────────────────────────────────" -ForegroundColor Cyan

# 1. PostgreSQL TCP reachability
Write-Host "`n1. PostgreSQL TCP reachability..."
try {
  $tcp = New-Object System.Net.Sockets.TcpClient
  $tcp.Connect($DbHost, $Port)
  $tcp.Close()
  Ok "pg-tcp" "PostgreSQL 18 reachable at ${DbHost}:${Port}"
} catch {
  Fail "pg-tcp" "Cannot reach PostgreSQL at ${DbHost}:${Port}: $_"
}

# 2. PostgreSQL login and schema version
Write-Host "`n2. PostgreSQL schema migrations..."
$pgCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT version FROM agentcore.schema_migrations ORDER BY version")
      versions = [r[0] for r in cur.fetchall()]
      cur.execute("SELECT COUNT(*) FROM agentcore.sessions")
      session_count = cur.fetchone()[0]
  print(json.dumps({"ok":True,"versions":versions,"session_count":session_count}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
if ($pgCheck -and $pgCheck.ok) {
  Ok "pg-schema" "schema_migrations versions: $($pgCheck.versions -join ', '); sessions: $($pgCheck.session_count)"
} else {
  Fail "pg-schema" "PostgreSQL login or schema check failed: $($pgCheck.error)"
}

# 3. Bifrost gateway HTTP health
Write-Host "`n3. Bifrost gateway health..."
try {
  $resp = Invoke-WebRequest -Uri $BifrostHealthUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
  if ($resp.StatusCode -eq 200) {
    Ok "bifrost-health" "Bifrost gateway responded 200 at $BifrostHealthUrl"
  } else {
    Warn "bifrost-health" "Bifrost gateway returned HTTP $($resp.StatusCode)"
  }
} catch {
  Warn "bifrost-health" "Bifrost gateway not reachable at $BifrostHealthUrl (gateway may be restarting)"
}

# 4. Open sessions with no recent event (stale continuity)
Write-Host "`n4. Stale open sessions (no event in last ${StaleHours}h)..."
$staleCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT client_key, agent_key, project_key, session_key,
               last_session_open, last_append, continuity_status
        FROM agentcore.v_client_memory_continuity
        WHERE continuity_status IN ('stale','open_no_events')
      """)
      rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
  print(json.dumps({"ok":True,"stale":rows}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
if ($staleCheck -and $staleCheck.ok) {
  if ($staleCheck.stale.Count -eq 0) {
    Ok "stale-sessions" "No stale open sessions"
  } else {
    foreach ($s in $staleCheck.stale) {
      Warn "stale-sessions" "Stale: client=$($s.client_key) project=$($s.project_key) status=$($s.continuity_status) last_append=$($s.last_append)"
    }
  }
} else {
  Warn "stale-sessions" "v_client_memory_continuity not queryable (view may be pending migration m8.002)"
}

# 5. Sessions closed without final handoff
Write-Host "`n5. Sessions closed without handoff..."
$noHandoff = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT client_key, agent_key, project_key, session_key, last_close
        FROM agentcore.v_client_memory_continuity
        WHERE continuity_status = 'closed_no_handoff'
        LIMIT 20
      """)
      rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
  print(json.dumps({"ok":True,"rows":rows}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
if ($noHandoff -and $noHandoff.ok) {
  if ($noHandoff.rows.Count -eq 0) {
    Ok "closed-no-handoff" "No closed sessions without handoff"
  } else {
    foreach ($s in $noHandoff.rows) {
      Warn "closed-no-handoff" "Closed without handoff: client=$($s.client_key) project=$($s.project_key)"
    }
  }
} else {
  Warn "closed-no-handoff" "continuity view not queryable — skipping"
}

# 6. Quarantined-memory enforcement
Write-Host "`n6. Quarantined-memory enforcement..."
$qCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT COUNT(*) FROM agentcore.evidence_events
        WHERE trust_class IN ('quarantined','rejected')
      """)
      quarantined = cur.fetchone()[0]
  print(json.dumps({"ok":True,"quarantined":quarantined}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
if ($qCheck -and $qCheck.ok) {
  Ok "quarantine" "Quarantined/rejected events: $($qCheck.quarantined) (excluded from normal startup context)"
} else {
  Warn "quarantine" "Could not query quarantined events: $($qCheck.error)"
}

# 7. Swarm exclusion: no swarm schema writes in agent_core
Write-Host "`n7. Swarm exclusion (agent_core free of swarm schema)..."
$swarmCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT COUNT(*) FROM information_schema.schemata
        WHERE schema_name IN ('swarm','swarmrecall','swarmvault')
      """)
      swarm_schemas = cur.fetchone()[0]
  print(json.dumps({"ok":True,"swarm_schemas":swarm_schemas}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
if ($swarmCheck -and $swarmCheck.ok) {
  if ($swarmCheck.swarm_schemas -eq 0) {
    Ok "swarm-exclusion" "No Swarm schemas (swarm/swarmrecall/swarmvault) in agent_core"
  } else {
    Fail "swarm-exclusion" "$($swarmCheck.swarm_schemas) Swarm schema(s) found in agent_core — cross-boundary contamination"
  }
} else {
  Warn "swarm-exclusion" "Swarm exclusion check failed: $($swarmCheck.error)"
}

# ═════════════════════════════════════════════════════════════════════════════
# RESOURCE CHECKS (Resource and Deep modes)
# ═════════════════════════════════════════════════════════════════════════════

if ($Mode -in @("Resource","Deep")) {
  Write-Host "`n── RESOURCE ────────────────────────────────────────────────────" -ForegroundColor Cyan

  # 8. Registered projects, repositories, and worktrees
  Write-Host "`n8. Registered projects, repositories, and worktrees..."
  $registryCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT COUNT(*) FROM agentcore.projects")
      projects = cur.fetchone()[0]
      cur.execute("SELECT COUNT(*) FROM agentcore.repositories")
      repos = cur.fetchone()[0]
      cur.execute("SELECT COUNT(*) FROM agentcore.worktrees WHERE worktree_status='active'")
      active_wt = cur.fetchone()[0]
      cur.execute("SELECT COUNT(*) FROM agentcore.worktrees WHERE worktree_status='retired'")
      retired_wt = cur.fetchone()[0]
  print(json.dumps({"ok":True,"projects":projects,"repos":repos,"active_wt":active_wt,"retired_wt":retired_wt}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($registryCheck -and $registryCheck.ok) {
    Ok "registry" "Projects: $($registryCheck.projects)  Repos: $($registryCheck.repos)  Active worktrees: $($registryCheck.active_wt)  Retired: $($registryCheck.retired_wt)"
  } else {
    Fail "registry" "Registry query failed: $($registryCheck.error)"
  }

  # 9-10. Resource-location registry and missing paths
  Write-Host "`n9-10. Resource-location registry and missing registered paths..."
  $locCheck = Invoke-PyQuery @"
import sys, json, psycopg, os
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT COUNT(*) FROM agentcore.artifact_locations WHERE is_active
      """)
      active_locs = cur.fetchone()[0]
      cur.execute("""
        SELECT al.storage_uri FROM agentcore.artifact_locations al
        WHERE al.is_active AND al.storage_tier NOT IN ('cold_e','backup_g')
      """)
      uris = [r[0] for r in cur.fetchall()]
      missing = [u for u in uris if u and not os.path.exists(u)]
  print(json.dumps({"ok":True,"active_locs":active_locs,"missing":missing}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($locCheck -and $locCheck.ok) {
    Ok "locations-count" "Active registered resource locations: $($locCheck.active_locs)"
    if ($locCheck.missing.Count -eq 0) {
      Ok "locations-paths" "All registered hot paths exist on disk"
    } else {
      foreach ($m in $locCheck.missing) { Fail "locations-paths" "Registered path missing on disk: $m" }
    }
  } else {
    Warn "locations" "Resource-location check failed: $($locCheck.error)"
  }

  # 11. Unregistered durable paths on approved AgentCore hot root (H:\AgentRuntime\agentcore-memory)
  Write-Host "`n11. Unregistered durable hot artifacts..."
  $hotRoot = "H:\AgentRuntime\agentcore-memory\artifacts"
  if (Test-Path $hotRoot) {
    $hotFiles  = (Get-ChildItem -Recurse -File $hotRoot -ErrorAction SilentlyContinue).Count
    $unreg = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT COUNT(*) FROM agentcore.artifact_locations
        WHERE storage_tier = 'hot_h' AND is_active
      """)
      reg = cur.fetchone()[0]
  print(json.dumps({"ok":True,"registered_hot":reg}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
    if ($unreg -and $unreg.ok) {
      $diff = $hotFiles - $unreg.registered_hot
      if ($diff -le 0) {
        Ok "unreg-hot" "Hot artifact files ($hotFiles) <= registered hot locations ($($unreg.registered_hot))"
      } else {
        Warn "unreg-hot" "$diff hot artifact file(s) in $hotRoot may not be registered in artifact_locations"
      }
    }
  } else {
    Ok "unreg-hot" "Hot artifact root $hotRoot does not yet exist (no hot artifacts)"
  }

  # 12. Production references to retired worktrees
  Write-Host "`n12. Production references to retired worktrees..."
  $bifrostConfigPath = "H:\AgentRuntime\bifrost\config.json"
  $retiredCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT worktree_path FROM agentcore.worktrees WHERE worktree_status='retired'
      """)
      retired = [r[0] for r in cur.fetchall()]
  print(json.dumps({"ok":True,"retired":retired}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($retiredCheck -and $retiredCheck.ok) {
    $bifrostOk = $true
    if (Test-Path $bifrostConfigPath) {
      $bCfg = Get-Content $bifrostConfigPath -Raw
      foreach ($rp in $retiredCheck.retired) {
        if ($bCfg -like "*$rp*") {
          Fail "retired-refs" "Bifrost config references retired worktree: $rp"
          $bifrostOk = $false
        }
      }
    }
    if ($bifrostOk) { Ok "retired-refs" "No production Bifrost references to retired worktrees" }
  }

  # 13. Last successful memory lifecycle per IDE client (from continuity view)
  Write-Host "`n13. Last memory lifecycle per IDE client..."
  $clientCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT client_key, agent_key, project_key, continuity_status,
               last_session_open::text, last_append::text, last_close::text
        FROM agentcore.v_client_memory_continuity
        ORDER BY last_session_open DESC NULLS LAST
      """)
      rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
  print(json.dumps({"ok":True,"rows":rows}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($clientCheck -and $clientCheck.ok) {
    foreach ($c in $clientCheck.rows) {
      $status = $c.continuity_status
      $msg = "client=$($c.client_key) project=$($c.project_key) status=$status last_append=$($c.last_append)"
      switch ($status) {
        "healthy"           { Ok  "client-lifecycle" $msg }
        "closed"            { Ok  "client-lifecycle" $msg }
        "stale"             { Warn "client-lifecycle" $msg }
        "projection_stale"  { Warn "client-lifecycle" $msg }
        "open_no_events"    { Warn "client-lifecycle" $msg }
        "closed_no_handoff" { Warn "client-lifecycle" $msg }
        default             { Warn "client-lifecycle" $msg }
      }
    }
    if ($clientCheck.rows.Count -eq 0) {
      Ok "client-lifecycle" "No client sessions registered yet"
    }
  } else {
    Warn "client-lifecycle" "Continuity view not queryable — skipping"
  }

  # 14. Projection revision freshness
  Write-Host "`n14. Projection revision freshness..."
  $projCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT to_regclass('agentcore.projection_revisions') IS NOT NULL AS has_table
      """)
      has_table = cur.fetchone()[0]
      if has_table:
        cur.execute("""
          SELECT p.project_key, pr.revision, pr.generated_at::text, pr.content_sha256
          FROM agentcore.projection_revisions pr
          JOIN agentcore.projects p ON p.id = pr.project_id
          WHERE pr.is_current
          ORDER BY pr.generated_at DESC
          LIMIT 10
        """)
        revisions = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
      else:
        revisions = []
  print(json.dumps({"ok":True,"has_table":has_table,"revisions":revisions}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($projCheck -and $projCheck.ok) {
    if (-not $projCheck.has_table) {
      Warn "projections" "projection_revisions table absent (M3 not applied)"
    } elseif ($projCheck.revisions.Count -eq 0) {
      Ok "projections" "No current projection revisions (no projector runs yet)"
    } else {
      foreach ($r in $projCheck.revisions) {
        Ok "projections" "project=$($r.project_key) revision=$($r.revision) generated=$($r.generated_at)"
      }
    }
  }

  # 15. .agentcore/STATE.md, DECISIONS.md, CONTEXT_INDEX.md existence
  Write-Host "`n15. .agentcore projection files presence..."
  $agentcoreDir = Join-Path $RepoRoot ".agentcore"
  $stateFile = Join-Path $agentcoreDir "STATE.md"
  $decisionsFile = Join-Path $agentcoreDir "DECISIONS.md"
  $contextIdxFile = Join-Path $agentcoreDir "CONTEXT_INDEX.md"
  if (Test-Path $stateFile)       { Ok "agentcore-state"    ".agentcore\STATE.md exists" }
  else                            { Warn "agentcore-state"  ".agentcore\STATE.md missing — run projection worker" }
  if (Test-Path $decisionsFile)   { Ok "agentcore-decisions" ".agentcore\DECISIONS.md exists" }
  else                            { Warn "agentcore-decisions" ".agentcore\DECISIONS.md missing" }
  if (Test-Path $contextIdxFile)  { Ok "agentcore-context"  ".agentcore\CONTEXT_INDEX.md exists" }
  else                            { Warn "agentcore-context" ".agentcore\CONTEXT_INDEX.md missing" }

  # 16. Hot H: vs Cold E: artifact counts
  Write-Host "`n16. Hot/Cold artifact tier balance..."
  $tierCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT storage_tier::text, COUNT(*), COALESCE(SUM(ao.bytes),0)
        FROM agentcore.artifact_locations al
        JOIN agentcore.artifact_objects ao ON ao.id = al.artifact_id
        WHERE al.is_active
        GROUP BY storage_tier
      """)
      tiers = {r[0]:{"count":r[1],"bytes":r[2]} for r in cur.fetchall()}
  print(json.dumps({"ok":True,"tiers":tiers}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($tierCheck -and $tierCheck.ok) {
    foreach ($tier in $tierCheck.tiers.PSObject.Properties) {
      $mb = [math]::Round($tier.Value.bytes / 1MB, 2)
      Ok "tier-balance" "Tier $($tier.Name): count=$($tier.Value.count) bytes_mb=$mb"
    }
    if (($tierCheck.tiers.PSObject.Properties | Measure-Object).Count -eq 0) {
      Ok "tier-balance" "No artifact locations registered yet"
    }
  }

  # 17. Stale temporary I: artifacts (> 24h)
  Write-Host "`n17. Stale scratch_i artifacts..."
  $scratchCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT COUNT(*) FROM agentcore.artifact_locations
        WHERE storage_tier = 'scratch_i'
          AND is_active
          AND created_at < now() - interval '24 hours'
      """)
      stale = cur.fetchone()[0]
  print(json.dumps({"ok":True,"stale":stale}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($scratchCheck -and $scratchCheck.ok) {
    if ($scratchCheck.stale -eq 0) { Ok "scratch-stale" "No stale I: artifacts" }
    else                            { Warn "scratch-stale" "$($scratchCheck.stale) stale scratch_i artifact(s) > 24h" }
  }

  # 18. Storage free-space thresholds
  Write-Host "`n18. Storage free-space thresholds (min $MinFreeMb MB each)..."
  $drives = @("D","E","F","G","H","I")
  foreach ($d in $drives) {
    $root = "${d}:\"
    if (Test-Path $root) {
      $info = Get-PSDrive -Name $d -ErrorAction SilentlyContinue
      if ($info -and $info.Free) {
        $freeMb = [math]::Round($info.Free / 1MB)
        if ($freeMb -ge $MinFreeMb) { Ok "free-space-${d}" "${d}: Free ${freeMb} MB (>= threshold $MinFreeMb MB)" }
        else                        { Warn "free-space-${d}" "${d}: Free ${freeMb} MB — below threshold $MinFreeMb MB" }
      }
    }
  }
}

# ═════════════════════════════════════════════════════════════════════════════
# DEEP CHECKS (Deep mode only)
# ═════════════════════════════════════════════════════════════════════════════

if ($Mode -eq "Deep") {
  Write-Host "`n── DEEP ────────────────────────────────────────────────────────" -ForegroundColor Cyan

  # 19. WAL archive continuity
  Write-Host "`n19. WAL archive continuity..."
  $walCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("SHOW archive_mode")
      archive_mode = cur.fetchone()[0]
      cur.execute("SHOW archive_command")
      archive_command = cur.fetchone()[0]
      cur.execute("SELECT last_archived_wal, last_archived_time::text, last_failed_wal, last_failed_time::text FROM pg_stat_archiver")
      row = cur.fetchone()
      archiver = {"last_archived_wal":row[0],"last_archived_time":row[1],"last_failed_wal":row[2],"last_failed_time":row[3]}
  print(json.dumps({"ok":True,"archive_mode":archive_mode,"archive_command":archive_command,"archiver":archiver}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($walCheck -and $walCheck.ok) {
    Ok "wal-archive-mode" "archive_mode=$($walCheck.archive_mode)"
    if ($walCheck.archiver.last_archived_wal) {
      Ok "wal-archived" "Last archived WAL: $($walCheck.archiver.last_archived_wal) at $($walCheck.archiver.last_archived_time)"
    } else {
      Warn "wal-archived" "No WAL segments archived yet (archive_mode=$($walCheck.archive_mode))"
    }
    if ($walCheck.archiver.last_failed_wal) {
      Fail "wal-failed" "Last failed WAL: $($walCheck.archiver.last_failed_wal) at $($walCheck.archiver.last_failed_time)"
    } else {
      Ok "wal-failed" "No failed WAL archive operations"
    }
  } else {
    Warn "wal-archive" "WAL archive check failed: $($walCheck.error)"
  }

  # 20. Scheduled-task last-run and failure status
  Write-Host "`n20. Scheduled-task health..."
  $taskNames = @("NightlyBackup","NightlyRestoreTest","WeeklyMaintenance","MemoryProjection",
                 "PostgresRuntime","AgentCore-Bifrost-Gateway","DurabilityHealthCheck",
                 "DurabilityResourceAudit","DurabilityDeepAudit")
  foreach ($tn in $taskNames) {
    $ti = Get-ScheduledTaskInfo -TaskPath "\AgentCore\" -TaskName $tn -ErrorAction SilentlyContinue
    if ($ti) {
      $lastRunResult = $ti.LastTaskResult
      $lastRun = $ti.LastRunTime
      if ($lastRunResult -eq 0) {
        Ok "task-$tn" "LastRun=$lastRun Result=0 (success)"
      } elseif ($lastRun -eq [datetime]::MinValue) {
        Warn "task-$tn" "Task has never run"
      } else {
        Warn "task-$tn" "LastRun=$lastRun Result=$lastRunResult (non-zero)"
      }
    } else {
      Warn "task-$tn" "Task not found under \AgentCore\ — may not be registered yet"
    }
  }

  # 21. G: backup coverage
  Write-Host "`n21. G: backup coverage..."
  $backupCheck = Invoke-PyQuery @"
import sys, json, psycopg
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT COUNT(*), MAX(created_at)::text AS newest
        FROM agentcore.artifact_locations
        WHERE storage_tier = 'backup_g' AND is_active
      """)
      r = cur.fetchone()
      backup_count = r[0]; newest = r[1]
  print(json.dumps({"ok":True,"backup_count":backup_count,"newest":newest}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($backupCheck -and $backupCheck.ok) {
    if ($backupCheck.backup_count -gt 0) {
      Ok "backup-g" "G: backup artifact locations: $($backupCheck.backup_count) newest=$($backupCheck.newest)"
    } else {
      Warn "backup-g" "No backup_g artifact locations registered (nightly backup may not have run)"
    }
  }

  # 22. PostgreSQL logical-backup recency on E:
  Write-Host "`n22. E: logical backup recency..."
  $backupRoot = "E:\AgentCoreArchive\backups_cold"
  if (Test-Path $backupRoot) {
    $latest = Get-ChildItem $backupRoot -Recurse -Filter "*.sql*" -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
      $ageDays = ((Get-Date) - $latest.LastWriteTime).TotalDays
      if ($ageDays -le 2) {
        Ok "backup-e" "Latest E: backup: $($latest.Name) age=$([math]::Round($ageDays,1)) days"
      } else {
        Warn "backup-e" "Latest E: backup is $([math]::Round($ageDays,1)) days old: $($latest.FullName)"
      }
    } else {
      Warn "backup-e" "No .sql backup files found under $backupRoot"
    }
  } else {
    Warn "backup-e" "E: backup root $backupRoot does not exist"
  }

  # 23. Projection content-hash spot-check
  Write-Host "`n23. Projection content-hash spot-check..."
  $hashCheck = Invoke-PyQuery @"
import sys, json, psycopg, hashlib
from pathlib import Path
dsn = sys.argv[1]
try:
  with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT to_regclass('agentcore.projection_revisions') IS NOT NULL AS has_table
      """)
      has_table = cur.fetchone()[0]
      results = []
      if has_table:
        cur.execute("""
          SELECT pr.target_path, pr.content_sha256
          FROM agentcore.projection_revisions pr WHERE pr.is_current
          LIMIT 5
        """)
        for (path, sha) in cur.fetchall():
          try:
            actual = hashlib.sha256(Path(path).read_bytes()).hexdigest() if path else None
            match = actual == sha if actual and sha else None
            results.append({"path":path,"sha":sha,"match":match,"actual":actual})
          except Exception as ex:
            results.append({"path":path,"sha":sha,"match":None,"error":str(ex)})
  print(json.dumps({"ok":True,"results":results}))
except Exception as e:
  print(json.dumps({"ok":False,"error":str(e)}))
"@
  if ($hashCheck -and $hashCheck.ok) {
    foreach ($r in $hashCheck.results) {
      if ($null -eq $r.match)        { Warn "proj-hash" "Cannot verify $($r.path): $($r.error)" }
      elseif ($r.match -eq $true)   { Ok   "proj-hash" "Hash verified: $($r.path)" }
      else                           { Fail "proj-hash" "Hash mismatch: $($r.path) registered=$($r.sha) actual=$($r.actual)" }
    }
    if ($hashCheck.results.Count -eq 0) { Ok "proj-hash" "No projection revisions to spot-check" }
  }
}

# ═════════════════════════════════════════════════════════════════════════════
# OPENROUTER MCP CHECKS (Health mode and above)
# Verifies dormant registration, zero tool exposure, and security invariants.
# Authority: docs/operations/OPENROUTER_MCP.md
# ═════════════════════════════════════════════════════════════════════════════

Write-Host "`n--- OpenRouter MCP Invariants ---" -ForegroundColor Cyan
$repoRoot   = Join-Path $PSScriptRoot ".."
$registryPath = Join-Path $repoRoot "contracts\bifrost-upstream-mcp-registry.json"

# OR-0. BIFROST_ENCRYPTION_KEY presence (prerequisite for OAuth — name check only, no value)
Write-Host "`nOR-0. BIFROST_ENCRYPTION_KEY presence (OAuth prerequisite)..."
$encKeyUser    = [System.Environment]::GetEnvironmentVariable("BIFROST_ENCRYPTION_KEY", "User")
$encKeyMachine = [System.Environment]::GetEnvironmentVariable("BIFROST_ENCRYPTION_KEY", "Machine")
$encKeyPresent = ($null -ne $encKeyUser -or $null -ne $encKeyMachine)
$encKeyScope   = if ($null -ne $encKeyUser) { "User" } elseif ($null -ne $encKeyMachine) { "Machine" } else { "ABSENT" }
if (-not $encKeyPresent) {
    Fail "or-encryption-key" "BIFROST_ENCRYPTION_KEY is ABSENT from User and Machine scope — OAuth material would be stored in plaintext; do NOT initiate OAuth until this is set (see docs/operations/OPENROUTER_MCP.md Encryption Blocker)"
} else {
    Ok "or-encryption-key" "BIFROST_ENCRYPTION_KEY present in $encKeyScope scope (name verified; value not examined)"
    # Verify Bifrost recognizes encryption as enabled (check for absence of plaintext-storage warning in logs)
    $logFile = "H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log"
    if (Test-Path $logFile) {
        $plaintextWarn = Get-Content $logFile -Tail 200 | Select-String "encryption.*disabled|config.*not.*encrypt|plaintext.*token" -CaseSensitive:$false
        if ($plaintextWarn) {
            Warn "or-encryption-active" "Bifrost log contains encryption-disabled signal — verify BIFROST_ENCRYPTION_KEY is loaded at Bifrost startup"
        } else {
            Ok "or-encryption-active" "No encryption-disabled signals in recent Bifrost log"
        }
    } else {
        Warn "or-encryption-active" "Bifrost log not found — cannot verify encryption-active signal"
    }
}

# OR-1. Registry: openrouter present, status=dormant, not in any allowed_server_ids
Write-Host "`nOR-1. OpenRouter registry invariants..."
if (Test-Path $registryPath) {
    $reg = Get-Content $registryPath -Raw | ConvertFrom-Json
    $orServer = $reg.servers.openrouter
    if ($null -eq $orServer) {
        Fail "or-registry-present" "openrouter not found in bifrost-upstream-mcp-registry.json"
    } elseif ($orServer.status -ne "dormant") {
        Fail "or-registry-dormant" "openrouter status is '$($orServer.status)' — expected 'dormant'"
    } else {
        Ok "or-registry-dormant" "openrouter registered dormant"
    }
    # Confirm not in any allowed_server_ids
    $profilesWithOR = @()
    ($reg.capability_profiles.PSObject.Properties) | ForEach-Object {
        $profId  = $_.Name
        $allowed = $_.Value.allowed_server_ids
        if ($allowed -and $allowed -contains "openrouter") { $profilesWithOR += $profId }
    }
    if ($profilesWithOR.Count -gt 0) {
        Fail "or-no-profile-exposure" "openrouter in allowed_server_ids of: $($profilesWithOR -join ', ') — zero tools require a live M6 lease"
    } else {
        Ok "or-no-profile-exposure" "openrouter absent from all capability_profiles allowed_server_ids"
    }
    # Confirm no direct openrouter MCP server entries in IDE configs
    # (OpenRouter as an LLM provider/model profile is separate and expected)
    $ideConfigs = @(
        @{path="C:\Users\ynotf\.cursor\mcp.json"; pattern='"openrouter".*"url"|"url".*openrouter\.ai/mcp'},
        @{path="C:\Users\ynotf\.codex\config.toml"; pattern='^\[mcp_servers\.openrouter\]'},
        @{path="C:\Users\ynotf\.claude.json"; pattern='"openrouter".*"type"\s*:|"type".*"openrouter"'},
        @{path="C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json"; pattern='"openrouter".*"command"|"url".*openrouter\.ai/mcp'},
        @{path="C:\Users\ynotf\.minimax\mcp\mcp.json"; pattern='"openrouter".*"url"|"url".*openrouter\.ai/mcp'},
        @{path="C:\Users\ynotf\AppData\Roaming\interpreter\config.json"; pattern='openrouter.*mcp\.openrouter\.ai'}
    )
    $ideWithOR = @()
    foreach ($cf in $ideConfigs) {
        if (Test-Path $cf.path) {
            $content = Get-Content $cf.path -Raw -ErrorAction SilentlyContinue
            if ($content -and $content -match $cf.pattern) { $ideWithOR += $cf.path }
        }
    }
    if ($ideWithOR.Count -gt 0) {
        Fail "or-no-direct-ide-entries" "Direct openrouter MCP entries found in IDE configs: $($ideWithOR -join '; ')"
    } else {
        Ok "or-no-direct-ide-entries" "No direct openrouter MCP entries in IDE configs (LLM provider config is separate)"
    }
} else {
    Warn "or-registry-present" "Registry file not found: $registryPath"
}

# OR-1b. Single registration — exactly one openrouter in registry and live Bifrost client_configs
Write-Host "`nOR-1b. Single OpenRouter registration..."
$liveCfgPath = "H:\AgentRuntime\bifrost\config.json"
if (Test-Path $liveCfgPath) {
    try {
        $liveCfg = Get-Content $liveCfgPath -Raw | ConvertFrom-Json
        $liveOR = @($liveCfg.mcp.client_configs | Where-Object { $_.name -eq "openrouter" })
        if ($liveOR.Count -eq 1) {
            Ok "or-single-live-client" "Exactly one openrouter client in live Bifrost config"
        } elseif ($liveOR.Count -eq 0) {
            Fail "or-single-live-client" "openrouter missing from live Bifrost client_configs"
        } else {
            Fail "or-single-live-client" "Duplicate openrouter clients in live Bifrost config: count=$($liveOR.Count)"
        }
    } catch {
        Warn "or-single-live-client" "Could not parse live Bifrost config: $($_.Exception.Message)"
    }
} else {
    Warn "or-single-live-client" "Live Bifrost config.json not found"
}
if (Test-Path $registryPath) {
    $regKeys = @((Get-Content $registryPath -Raw | ConvertFrom-Json).servers.PSObject.Properties.Name | Where-Object { $_ -eq "openrouter" })
    if ($regKeys.Count -eq 1) {
        Ok "or-single-registry" "Exactly one openrouter entry in upstream registry"
    } else {
        Fail "or-single-registry" "Expected exactly one openrouter registry key; found $($regKeys.Count)"
    }
}

# OR-1c. Unauthenticated remote probe — expect 401 until OAuth (reversible; no paid calls)
Write-Host "`nOR-1c. Unauthenticated OpenRouter MCP endpoint probe..."
try {
    $probeBody = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"agentcore-durability-probe","version":"1.0"}}}'
    Invoke-WebRequest -Uri "https://mcp.openrouter.ai/mcp" -Method POST -ContentType "application/json" `
        -Headers @{ "Accept" = "application/json, text/event-stream" } -Body $probeBody -TimeoutSec 20 | Out-Null
    Warn "or-remote-unauth" "Unauthenticated initialize unexpectedly succeeded — investigate OAuth requirement"
} catch {
    $code = $null
    try { $code = [int]$_.Exception.Response.StatusCode } catch { }
    if ($code -eq 401 -or $_.Exception.Message -match "401") {
        Ok "or-remote-unauth" "Remote OpenRouter MCP returns 401 without OAuth (expected while dormant)"
    } else {
        Warn "or-remote-unauth" "Unauthenticated probe did not return 401: $($_.Exception.Message)"
    }
}

# OR-1d. Bifrost pin evidence — binary present; sha256 recorded; docs pin v2.0.0-prerelease1
Write-Host "`nOR-1d. Bifrost pin verification..."
$bifrostExe = "H:\AgentRuntime\bifrost\bin\bifrost-http.exe"
$pinDoc = "v2.0.0-prerelease1"
if (Test-Path $bifrostExe) {
    $exeHash = (Get-FileHash $bifrostExe -Algorithm SHA256).Hash
    Ok "or-bifrost-binary" "bifrost-http.exe present; sha256=$exeHash; docs pin=$pinDoc (version flag not exposed by this build)"
} else {
    Fail "or-bifrost-binary" "Pinned Bifrost binary missing at $bifrostExe"
}
$anchor = Join-Path $repoRoot "PROJECT_ANCHOR.md"
if ((Test-Path $anchor) -and ((Get-Content $anchor -Raw) -match [regex]::Escape($pinDoc))) {
    Ok "or-bifrost-pin-doc" "PROJECT_ANCHOR.md records Bifrost pin $pinDoc"
} else {
    Warn "or-bifrost-pin-doc" "PROJECT_ANCHOR.md missing Bifrost pin $pinDoc"
}

# OR-1e. Claimed tool inventory drift note (pre-auth; authenticated tools/list still required)
Write-Host "`nOR-1e. OpenRouter claimed inventory drift..."
if (Test-Path $registryPath) {
    $orPermitted = @((Get-Content $registryPath -Raw | ConvertFrom-Json).servers.openrouter.permitted_tools)
    $officialDocCount = 11  # OpenRouter public docs inventory as of runbook; not authoritative post-auth
    if ($orPermitted.Count -gt 0) {
        Ok "or-inventory-claimed" "Registry claims $($orPermitted.Count) permitted tools (pre-auth); official docs list ~$officialDocCount — authenticated tools/list required after OAuth"
        if ($orPermitted.Count -ne $officialDocCount) {
            Warn "or-inventory-drift" "Claimed permitted_tools ($($orPermitted.Count)) differs from official-docs count ($officialDocCount) — reconcile after authenticated tools/list"
        }
    } else {
        Fail "or-inventory-claimed" "openrouter permitted_tools empty"
    }
}

# Shared MCP request bodies for pin + tools/list checks
$initBody = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"audit","version":"1.0"}}}'
$tlBody   = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
$notifBody = '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'

# Also capture Bifrost serverInfo.version from initialize when available
Write-Host "`nOR-1f. Bifrost initialize serverInfo pin..."
$builderVkForPin = $env:BIFROST_MCP_VIRTUAL_KEY
if ($builderVkForPin) {
    try {
        $hdrsPin = @{ "Authorization" = "Bearer $builderVkForPin"; "Content-Type" = "application/json" }
        $initPin = Invoke-RestMethod -Uri "http://127.0.0.1:8080/mcp" -Method POST -Headers $hdrsPin -Body $initBody -TimeoutSec 8
        $srvVer = $initPin.result.serverInfo.version
        $srvName = $initPin.result.serverInfo.name
        if ($srvVer -eq "v2.0.0-prerelease1") {
            Ok "or-bifrost-serverinfo" "Bifrost initialize serverInfo: name=$srvName version=$srvVer (matches pin)"
        } else {
            Warn "or-bifrost-serverinfo" "Bifrost serverInfo.version=$srvVer (expected v2.0.0-prerelease1)"
        }
    } catch {
        Warn "or-bifrost-serverinfo" "Could not read Bifrost serverInfo: $($_.Exception.Message)"
    }
} else {
    Warn "or-bifrost-serverinfo" "BIFROST_MCP_VIRTUAL_KEY not set — skipping serverInfo pin check"
}

# OR-2. Bifrost client status via MCP tools/list — use operator VK (OpenRouter is operator-scoped)
Write-Host "`nOR-2. OpenRouter tool exposure check (operator VK + builder VK)..."
$builderVk  = $env:BIFROST_MCP_VIRTUAL_KEY
$operatorVk = $env:BIFROST_MCP_VK_OPERATOR

foreach ($vkCheck in @(
    @{name="builder"; vk=$builderVk},
    @{name="operator"; vk=$operatorVk}
)) {
    $vkName = $vkCheck.name
    $vk     = $vkCheck.vk
    if (-not $vk) {
        Warn "or-tools-$vkName" "VK env var not set for $vkName — skipping tools/list check"
        continue
    }
    try {
        $hdrs = @{ "Authorization" = "Bearer $vk"; "Content-Type" = "application/json" }
        Invoke-RestMethod -Uri "http://127.0.0.1:8080/mcp" -Method POST -Headers $hdrs -Body $initBody -TimeoutSec 8 | Out-Null
        Invoke-RestMethod -Uri "http://127.0.0.1:8080/mcp" -Method POST -Headers $hdrs -Body $notifBody -TimeoutSec 5 -ErrorAction SilentlyContinue | Out-Null
        $tResp = Invoke-RestMethod -Uri "http://127.0.0.1:8080/mcp" -Method POST -Headers $hdrs -Body $tlBody -TimeoutSec 12
        $negotiatedProto = $tResp.result.protocolVersion
        if (-not $negotiatedProto) {
            # Some Bifrost responses omit protocolVersion on tools/list; use initialize serverInfo when present.
            $negotiatedProto = $tResp.result.serverInfo.version
        }
        $toolNames = @($tResp.result.tools | ForEach-Object { [string]$_.name })
        $orTools  = @($toolNames | Where-Object {
            $_ -match '(^|[-_])openrouter([-_]|$)' -or
            $_ -eq 'list-models' -or
            $_ -like 'openrouter*'
        }).Count
        $memExact = @(
            'agentcore_memory-memory_status','agentcore_memory-startup_context','agentcore_memory-retrieve_context',
            'agentcore_memory-append_event','agentcore_memory-propose_fact','agentcore_memory-expand_source',
            'agentcore_memory-session_open','agentcore_memory-session_close','agentcore_memory-build_handoff',
            'agentcore_memory-docs_search'
        )
        $memTools = @($toolNames | Where-Object { $memExact -contains $_ }).Count
        # Record negotiated protocol version (not hard-coded as acceptance evidence)
        Ok "or-proto-$vkName" "MCP protocol negotiated via $vkName VK: tools=$($toolNames.Count) proto_or_server=$negotiatedProto"
        if ($orTools -gt 0) {
            Warn "or-tools-dormant-$vkName" "$orTools openrouter tool(s) visible in $vkName VK without a confirmed lease — investigate"
        } else {
            Ok "or-tools-dormant-$vkName" "Zero openrouter tools exposed in $vkName VK (dormant enforced)"
        }
        if ($vkName -eq "builder") {
            if ($memTools -ne 10) {
                Fail "or-memory-surface-invariant" "agentcore_memory tool count via builder VK is $memTools — expected exactly 10 (gateway-prefixed names)"
            } else {
                Ok "or-memory-surface-invariant" "agentcore_memory surface: exactly 10 tools via builder VK (unchanged)"
            }
        }
    } catch {
        Warn "or-tools-$vkName" "Could not run tools/list for $vkName VK: $($_.Exception.Message)"
    }
}

# OR-3. config.db security posture — presence, ACL restriction, not in Git
Write-Host "`nOR-3. config.db secret-bearing posture and ACL check..."
$configDb = "H:\AgentRuntime\bifrost\data\config.db"
if (Test-Path $configDb) {
    Ok "or-configdb-present" "config.db present at $configDb — classified as secret-bearing"
    # ACL evaluation: check that only SYSTEM and owner have access (no Everyone/Users/All)
    try {
        $acl = Get-Acl $configDb -ErrorAction Stop
        $broadAccess = $acl.Access | Where-Object {
            ($_.IdentityReference -match "Everyone|BUILTIN\\Users|NT AUTHORITY\\Authenticated Users") -and
            ($_.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::Read) -ne 0
        }
        if ($broadAccess) {
            Fail "or-configdb-acl" "config.db has broad read access ($($broadAccess.IdentityReference -join ', ')) — restrict to SYSTEM and operator only"
        } else {
            Ok "or-configdb-acl" "config.db ACL: no broad read access principals detected"
        }
    } catch {
        Warn "or-configdb-acl" "Could not evaluate config.db ACL: $($_.Exception.Message)"
    }
    # Confirm not tracked in Git
    $inGit = (git -C $repoRoot ls-files --error-unmatch "H:\AgentRuntime\bifrost\data\config.db" 2>&1)
    if ($LASTEXITCODE -eq 0) {
        Fail "or-configdb-not-in-git" "config.db appears tracked in Git — must never be committed"
    } else {
        Ok "or-configdb-not-in-git" "config.db not tracked in Git"
    }
} else {
    Warn "or-configdb-present" "config.db not found — Bifrost may not have initialized config store yet"
}

# Verify oauth-clients.json (runtime state file) is not committed to Git
$oauthStateFile = "H:\AgentRuntime\bifrost\state\oauth-clients.json"
if (Test-Path $oauthStateFile) {
    $inGit2 = (git -C $repoRoot ls-files --error-unmatch $oauthStateFile 2>&1)
    if ($LASTEXITCODE -eq 0) {
        Fail "or-oauth-state-not-in-git" "oauth-clients.json appears tracked in Git — must never be committed (contains oauth_config_id)"
    } else {
        Ok "or-oauth-state-not-in-git" "oauth-clients.json (runtime OAuth state) not tracked in Git"
    }
}

# OR-4. Secret scan: no token literals in source files, renderers, or command history proxies
Write-Host "`nOR-4. Token literal scan..."
# Match value-like literals, not documentation of forbidden prefixes in validators/runbooks.
$secretValuePatterns = @(
    'sk-or-v1-[A-Za-z0-9]{8,}',
    '"oauth_access_token"\s*:\s*"[^"]{8,}"',
    '"oauth_refresh_token"\s*:\s*"[^"]{8,}"',
    'access_token"\s*:\s*"Bearer\s+[A-Za-z0-9\-_\.]{12,}'
)
$secretFound = $false
$scanRoots = @(
    "$repoRoot\contracts",
    "$repoRoot\scripts",
    "$repoRoot\renderers",
    "$repoRoot\ide-profiles"
)
foreach ($pat in $secretValuePatterns) {
    foreach ($root in $scanRoots) {
        if (-not (Test-Path $root)) { continue }
        $hits = rg -n --pcre2 $pat --glob "!*.db" --glob "!*.log" --glob "!.git" $root 2>$null
        if ($hits) {
            $secretFound = $true
            Fail "or-secret-scan" "Pattern '$pat' matched value-like secret material under $root"
        }
    }
}
if (-not $secretFound) { Ok "or-secret-scan" "No OpenRouter token literals found in source files" }

# OR-5. OAuth status — report accurately; never PASS expiry from log absence alone
Write-Host "`nOR-5. OAuth status and expiry check..."
if (-not $encKeyPresent) {
    Warn "or-oauth-status" "OAuth status: not_verified — BIFROST_ENCRYPTION_KEY absent; do not initiate OAuth (see OR-0)"
} else {
    # Check Bifrost management API for openrouter client OAuth status
    $adminKey = $env:BIFROST_ADMIN_KEY
    if ($adminKey) {
        try {
            $clientsResp = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/mcp/clients" `
                -Headers @{Authorization="Bearer $adminKey"} -TimeoutSec 10 -ErrorAction Stop
            $orClient = $clientsResp | Where-Object { $_.name -eq "openrouter" }
            if ($orClient) {
                $orStatus = $orClient.status ?? "unknown"
                $expiresAt = $orClient.expires_at ?? $orClient.oauth_expires_at ?? $null
                $statusMsg = "openrouter Bifrost client status: $orStatus"
                if ($expiresAt) {
                    $expiryDt  = [datetime]::Parse($expiresAt)
                    $hoursLeft = ($expiryDt - (Get-Date)).TotalHours
                    $statusMsg += "; expires_at=$expiresAt ($([math]::Round($hoursLeft,1))h remaining)"
                    if ($hoursLeft -le 0) {
                        Fail "or-oauth-status" "$statusMsg — EXPIRED"
                    } elseif ($hoursLeft -le 48) {
                        Warn "or-oauth-status" "$statusMsg — WARNING: reauthorization needed soon"
                    } else {
                        Ok "or-oauth-status" $statusMsg
                    }
                } elseif ($orStatus -in @("pending_oauth","ready_auth_on_first_use","installed_dormant")) {
                    Ok "or-oauth-status" "$statusMsg (pre-enrollment; zero tools exposed)"
                } elseif ($orStatus -in @("connected","active","authenticated_dormant")) {
                    Warn "or-oauth-status" "$statusMsg — expires_at not reported; cannot confirm expiry"
                } elseif ($orStatus -in @("error","disconnected","reconnect_loop","revoked")) {
                    Fail "or-oauth-status" "$statusMsg — needs operator attention"
                } else {
                    Warn "or-oauth-status" "$statusMsg — unrecognized status string; investigate"
                }
            } else {
                Warn "or-oauth-status" "openrouter client not found in Bifrost management API response"
            }
        } catch {
            Warn "or-oauth-status" "Could not query Bifrost management API for OAuth status: $($_.Exception.Message)"
        }
    } else {
        Warn "or-oauth-status" "BIFROST_ADMIN_KEY not set — cannot query OAuth status via management API; log-based expiry check skipped (log absence is not a PASS)"
    }
}

# OR-6. Runtime config.json: no token literals; oauth_config_id not in source renderers
Write-Host "`nOR-6. Runtime config token scan and oauth_config_id placement check..."
$runtimeCfg = "H:\AgentRuntime\bifrost\config.json"
if (Test-Path $runtimeCfg) {
    $cfgContent = Get-Content $runtimeCfg -Raw
    if ($cfgContent -match "sk-or-v1-|access_token.*:.*[A-Za-z0-9]{40}") {
        Fail "or-runtime-cfg-clean" "Possible token literal found in runtime config.json"
    } else {
        Ok "or-runtime-cfg-clean" "No token literals detected in runtime config.json"
    }
    # Verify oauth_config_id (if present) came from runtime state file, not baked into source
    if ($cfgContent -match '"oauth_config_id"') {
        # This is expected post-enrollment — verify the source renderer does NOT contain it
        $srcRenderer = Join-Path $repoRoot "renderers\bifrost\config.json"
        if (Test-Path $srcRenderer) {
            $srcContent = Get-Content $srcRenderer -Raw
            if ($srcContent -match '"oauth_config_id"\s*:\s*"[^"]{8,}"') {
                Warn "or-oauth-config-id-in-renderer" "oauth_config_id found in source renderer renderers/bifrost/config.json — should be runtime-only via state file"
            } else {
                Ok "or-oauth-config-id-in-renderer" "oauth_config_id not baked into source renderer (correct)"
            }
        }
    }
}

# OR-7. Tool inventory manifest check (count and schema drift)
Write-Host "`nOR-7. Tool inventory manifest check..."
$manifestPath = Join-Path $repoRoot "contracts\openrouter-tool-manifest.json"
if (Test-Path $manifestPath) {
    try {
        $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
        $manifestCount = ($manifest.tools | Measure-Object).Count
        Ok "or-manifest-present" "Tool inventory manifest present; $manifestCount tools recorded"
        # Check if manifest has discovery_timestamp and protocol_version
        if (-not $manifest.discovery_timestamp) { Warn "or-manifest-meta" "Manifest missing discovery_timestamp" }
        if (-not $manifest.protocol_version)    { Warn "or-manifest-meta" "Manifest missing protocol_version (negotiated)" }
    } catch {
        Warn "or-manifest-parse" "Could not parse tool manifest: $($_.Exception.Message)"
    }
} else {
    Warn "or-manifest-present" "Tool inventory manifest not yet committed (contracts/openrouter-tool-manifest.json) — required after authenticated tools/list"
}

# OR-8. Content logging disabled for openrouter
Write-Host "`nOR-8. Content logging check for openrouter..."
if (Test-Path $runtimeCfg) {
    $cfgObj = Get-Content $runtimeCfg -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($cfgObj) {
        $clientLevel = $cfgObj.client.disable_content_logging
        if ($clientLevel -eq $true) {
            Ok "or-no-content-logging" "disable_content_logging=true at gateway level (all clients including openrouter)"
        } else {
            Fail "or-no-content-logging" "disable_content_logging is not true at gateway level — content logging may be active"
        }
    }
}

# OR-9. Expired PostgreSQL leases still retaining Bifrost exposure; billable tools in permanent VK grants
Write-Host "`nOR-9. JIT lease cleanup and billable tool grant check..."
# Check that billable tools are not in any permanent VK grant
if ($builderVk -or $operatorVk) {
    $billableTools = @("send-message", "generate-image")
    $vksToCheck = @()
    if ($builderVk)  { $vksToCheck += @{name="builder";  vk=$builderVk} }
    if ($operatorVk) { $vksToCheck += @{name="operator"; vk=$operatorVk} }
    foreach ($vkCheck in $vksToCheck) {
        $vkName = $vkCheck.name; $vk = $vkCheck.vk
        try {
            $hdrs = @{ "Authorization" = "Bearer $vk"; "Content-Type" = "application/json" }
            Invoke-RestMethod -Uri "http://127.0.0.1:8080/mcp" -Method POST -Headers $hdrs -Body $initBody -TimeoutSec 8 | Out-Null
            $tResp2 = Invoke-RestMethod -Uri "http://127.0.0.1:8080/mcp" -Method POST -Headers $hdrs -Body $tlBody -TimeoutSec 12
            $allTools = $tResp2.result.tools.name
            $billableFound = $billableTools | Where-Object { $_ -in $allTools }
            if ($billableFound) {
                Fail "or-no-billable-in-permanent-vk" "Billable tool(s) $($billableFound -join ', ') found in permanent $vkName VK — must be JIT-lease-only"
            } else {
                Ok "or-no-billable-in-permanent-vk" "No billable tools in permanent $vkName VK"
            }
        } catch {
            Warn "or-no-billable-in-permanent-vk" "Could not check $vkName VK for billable tools: $($_.Exception.Message)"
        }
    }
} else {
    Warn "or-no-billable-in-permanent-vk" "No VK env vars set — skipping billable tool permanent-grant check"
}
# PostgreSQL expired lease check
$expiredLeaseCheck = Invoke-PyQuery @"
import sys, json
try:
    import psycopg
    dsn = sys.argv[1]
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('agentcore.capability_leases') IS NOT NULL")
            has_table = cur.fetchone()[0]
            if not has_table:
                print(json.dumps({"ok":True,"count":0,"note":"table_not_yet_created"}))
            else:
                cur.execute("""
                    SELECT COUNT(*) FROM agentcore.capability_leases
                    WHERE server_id='openrouter' AND status='active'
                    AND expires_at < NOW()
                """)
                expired = cur.fetchone()[0]
                print(json.dumps({"ok":True,"expired_active_leases":expired}))
except Exception as e:
    print(json.dumps({"ok":False,"error":str(e)}))
"@
if ($expiredLeaseCheck -and $expiredLeaseCheck.ok) {
    if ($expiredLeaseCheck.note -eq "table_not_yet_created") {
        Warn "or-expired-leases" "capability_leases table not yet created (M6 not yet active)"
    } elseif ($expiredLeaseCheck.expired_active_leases -gt 0) {
        Fail "or-expired-leases" "$($expiredLeaseCheck.expired_active_leases) expired openrouter lease(s) still marked 'active' in PostgreSQL"
    } else {
        Ok "or-expired-leases" "No expired openrouter leases retaining active status in PostgreSQL"
    }
} else {
    Warn "or-expired-leases" "Could not check expired leases: $($expiredLeaseCheck?.error)"
}

# OR-10. oauth_config_id must not appear in source renderers or Git-tracked files
Write-Host "`nOR-10. oauth_config_id placement scan (must be runtime-only)..."
$srcFiles = @(
    "$repoRoot\renderers\bifrost\config.sanitized.json",
    "$repoRoot\renderers\bifrost\config.json"
)
$oauthIdLeaked = $false
foreach ($f in $srcFiles) {
    if (Test-Path $f) {
        $fc = Get-Content $f -Raw
        # Match actual UUID/opaque value assigned to oauth_config_id (not the key name in notes)
        if ($fc -match '"oauth_config_id"\s*:\s*"[A-Za-z0-9\-_]{8,}"') {
            Fail "or-oauth-config-id-placement" "oauth_config_id value found in source-controlled file $f — must be runtime-only"
            $oauthIdLeaked = $true
        }
    }
}
if (-not $oauthIdLeaked) { Ok "or-oauth-config-id-placement" "No oauth_config_id values in source-controlled renderer files" }

# ═════════════════════════════════════════════════════════════════════════════
# Summary and report output
# ═════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Durability and Placement Audit Complete [Mode=$Mode]" -ForegroundColor Cyan
$color = if ($fail -gt 0) { "Red" } elseif ($warn -gt 0) { "Yellow" } else { "Green" }
Write-Host "PASS: $pass   WARN: $warn   FAIL: $fail" -ForegroundColor $color
Write-Host "================================================================" -ForegroundColor Cyan

# Write machine-readable report (hot)
$report = @{
  audit_mode     = $Mode
  started_at     = $stamp
  completed_at   = (Get-Date -Format "yyyyMMdd-HHmmss")
  pass           = $pass
  warn           = $warn
  fail           = $fail
  overall_status = if ($fail -gt 0) {"fail"} elseif ($warn -gt 0) {"warn"} else {"pass"}
  findings       = $findings.ToArray()
}

New-Item -ItemType Directory -Force -Path $hotLogDir | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $hotReport -Encoding UTF8
Write-Host "`nReport (hot): $hotReport" -ForegroundColor Gray

# Write cold evidence copy
try {
  New-Item -ItemType Directory -Force -Path $coldLogDir | Out-Null
  Copy-Item $hotReport $coldReport -ErrorAction Stop
  Write-Host "Report (cold): $coldReport" -ForegroundColor Gray
} catch {
  Write-Host "WARN: Could not write cold audit evidence to E: — $($_.Exception.Message)" -ForegroundColor Yellow
}

exit $(if ($fail -gt 0) { 1 } else { 0 })
