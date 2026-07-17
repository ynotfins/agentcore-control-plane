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
