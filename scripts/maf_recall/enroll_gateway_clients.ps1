#Requires -Version 5.1
# Enroll agentcore-gateway only (orchestration entrypoint).
[CmdletBinding()]
param(
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [switch]$Apply,
  [switch]$CommitPush,
  [switch]$PrepareRestart,
  [switch]$SetupDevinNfa,
  [switch]$SetupDevinNfaPlatform,
  [switch]$WireNfaPhoneIngest,
  [switch]$DumpPhoneUi,
  [switch]$FixNfaMacro
)
$ErrorActionPreference = "Stop"
if ($FixNfaMacro) {
  $src = "C:\Users\ynotf\Downloads\nfa-alerts.macro"
  $dst = "C:\Users\ynotf\Downloads\nfa-alerts.corrected.macro"
  if (-not (Test-Path -LiteralPath $src)) { throw "Missing $src" }
  $py = "D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $py)) { $py = "python" }
  $fixer = "I:\LocalApps\Devin\projects\nfa-platform\artifacts\fix_nfa_macro.py"
  $pyBody = @'
import json
from pathlib import Path
src = Path(r"C:\Users\ynotf\Downloads\nfa-alerts.macro")
dst = Path(r"C:\Users\ynotf\Downloads\nfa-alerts.corrected.macro")
data = json.loads(src.read_text(encoding="utf-8"))
macro = data["macro"]
headers = None
body = None
url = None
device_ids = []
raw_defaults = []
for var in macro.get("localVariables", []):
    if var.get("m_name") != "payload":
        continue
    entries = var.get("dictionary", {}).get("entries", [])
    for entry in entries:
        key = entry.get("key")
        inner = entry.get("variable") or {}
        if key == "deviceId":
            inner["textValue"] = "nfa-primary-phone"
            device_ids.append("localVar")
        if key == "rawText":
            inner["textValue"] = "{not_text_big}"
            raw_defaults.append("cleared_stale_sample")
for action in macro.get("m_actionList", []):
    if action.get("m_classType") == "SetVariableAction":
        keys = action.get("dictionaryKeys") or []
        if keys == ["deviceId"]:
            action["m_newStringValue"] = "nfa-primary-phone"
            device_ids.append("setVariable")
        if keys == ["rawText"]:
            action["m_newStringValue"] = "{not_text_big}"
    if action.get("m_classType") == "HttpRequestAction":
        cfg = action["requestConfig"]
        cfg["contentBodyText"] = "{lvjson=payload}"
        cfg["urlToOpen"] = "https://chaoscentral.tailb71e7e.ts.net/v1/ingest/alerts"
        cfg["basicAuthEnabled"] = False
        cfg["allowAnyCertificate"] = False
        cfg["contentType"] = "application/json"
        existing = [(h.get("paramName"), h.get("paramValue")) for h in cfg.get("headerParams", [])]
        names = {n for n, _ in existing}
        if "Content-Type" not in names:
            cfg.setdefault("headerParams", []).append(
                {"paramName": "Content-Type", "paramValue": "application/json"}
            )
        headers = [h.get("paramName") for h in cfg.get("headerParams", [])]
        body = cfg.get("contentBodyText")
        url = cfg.get("urlToOpen")
dst.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
print("wrote=" + str(dst))
print("url=" + str(url))
print("body=" + str(body))
print("header_names=" + ",".join(headers or []))
print("device_id_fixes=" + ",".join(device_ids))
print("raw_fixes=" + ",".join(raw_defaults))
'@
  New-Item -ItemType Directory -Force -Path (Split-Path $fixer) | Out-Null
  [System.IO.File]::WriteAllText($fixer, $pyBody, [System.Text.UTF8Encoding]::new($false))
  & $py $fixer
  if ($LASTEXITCODE -ne 0) { throw "macro fix failed" }
  return
}
if ($DumpPhoneUi) {
  $adb = "C:\platform-tools\adb.exe"
  if (-not (Test-Path $adb)) { throw "adb missing" }
  $outDir = "I:\LocalApps\Devin\projects\nfa-platform\artifacts"
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  & $adb devices -l
  $remote = "/sdcard/Download/ui-dump.xml"
  & $adb shell uiautomator dump $remote
  $local = Join-Path $outDir "macrodroid-ui-dump.xml"
  & $adb pull $remote $local
  $xml = Get-Content -LiteralPath $local -Raw
  $xml = [regex]::Replace($xml, 'Bearer [A-Za-z0-9_-]{20,}', 'Bearer <redacted>')
  [System.IO.File]::WriteAllText($local, $xml, [System.Text.UTF8Encoding]::new($false))
  & $adb shell rm -f $remote
  [regex]::Matches($xml, 'text="([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ } | ForEach-Object { Write-Output ("TEXT " + $_) }
  Write-Output "dumped=$local (secrets redacted)"
  return
}
if ($WireNfaPhoneIngest) {
  $artifacts = "I:\LocalApps\Devin\projects\nfa-platform\artifacts"
  $sampleDocs = Join-Path $artifacts "sample-docs"
  New-Item -ItemType Directory -Force -Path $artifacts, $sampleDocs | Out-Null

  $payloadsPath = Join-Path $artifacts "bnn-live-payloads.json"
  $payloads = @'
{
  "source": "operator-phone-screenshots-2026-08-27",
  "note": "Notification title (New Incident / Update / New Media) is Android chrome; rawText is the pipe body to POST as ingest rawText.",
  "alerts": [
    {
      "kind": "new_incident",
      "incidentId": "1900691",
      "rawText": "NY| Manhattan| Fire Department Activity| MN-0624| 134 W 24th St| BC7 using 1 and 1 for electrical condition in basement| <C> BNN | BNNDESK | #1900691"
    },
    {
      "kind": "new_media_update",
      "incidentId": "1900675",
      "rawText": "U/D NJ| Bergen| Carlstadt| Working Fire| Broad St & Madison St| New media has been posted.| <C> BNN | BNNDESK/nj137/njn074 | #1900675"
    },
    {
      "kind": "new_incident",
      "incidentId": "1900672",
      "rawText": "NJ| Bergen| Fairview| Structure Fire| 282 Madison St| PD reporting a shed fire in rear yard| <C> BNN | BNNDESK | #1900672"
    },
    {
      "kind": "new_incident",
      "incidentId": "1900669",
      "rawText": "NY| Queens| Fire Department Activity| 48th St & Broadway| E263 req Sanitation, E263 attached to hydrant they cannot shut off, have a Sanitation truck parked over water shutoff| <C> BNN | BNNDESK | #1900669"
    },
    {
      "kind": "update",
      "incidentId": "1900651",
      "rawText": "U/D NJ| Monmouth| Marlboro Township| Fire Damage| 130 S Main St- Maple Tree Plaza| Command reports negative extension. Ventilation in progress. The entire strip remains evacuated until the sprinkler system is recharged.| <C> BNN | njc691 | #1900651"
    },
    {
      "kind": "update",
      "incidentId": "1900643",
      "rawText": "U/D NY| Queens| 2nd Alarm| 99-22-5255| 109-35 110th St| DIV13 reports he had a fire in 2 private dwellings, fire placed U/C. | <C> BNN | BNNDESK | #1900643"
    },
    {
      "kind": "new_incident",
      "incidentId": "1900638",
      "rawText": "NY| Manhattan| Fire Damage| 66-1444| 80 Paladino Ave| FD on scene with an outside rubbish fire. | <C> BNN | BNNDESK | #1900638"
    },
    {
      "kind": "update",
      "incidentId": "1900634",
      "rawText": "U/D NY| Queens| All Hands| 99-75-2145| 101-28 Woodhaven Blvd| DIV13 placing the fire U/C. | <C> BNN | BNNDESK | #1900634"
    }
  ]
}
'@
  [System.IO.File]::WriteAllText($payloadsPath, $payloads.Trim() + "`n", [System.Text.UTF8Encoding]::new($false))

  Write-Output "=== sample-docs ==="
  $pdfs = Get-ChildItem -LiteralPath $sampleDocs -Force -ErrorAction SilentlyContinue | Select-Object Name, Length, LastWriteTime
  if ($pdfs) { $pdfs | Format-Table -AutoSize | Out-String | Write-Output } else { Write-Output "(empty)" }

  Write-Output "=== adb ==="
  $adb = $null
  foreach ($c in @("adb", "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe", "C:\platform-tools\adb.exe")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $adb = (Get-Command $c).Source; break }
    if (Test-Path $c) { $adb = $c; break }
  }
  if ($adb) {
    Write-Output "adb=$adb"
    & $adb devices -l
  } else {
    Write-Output "adb not on PATH"
  }

  Write-Output "=== tailscale serve before ==="
  tailscale serve status 2>&1 | Out-String | Write-Output

  Write-Output "=== enabling private Tailscale Serve to ingest gateway (not Funnel) ==="
  tailscale serve --bg http://127.0.0.1:8787 2>&1 | Out-String | Write-Output

  Write-Output "=== tailscale serve after ==="
  tailscale serve status 2>&1 | Out-String | Write-Output

  $guidePath = Join-Path $artifacts "MACRODROID_INGEST.txt"
  $guide = @"
MacroDroid permanent ingest (Tailscale private HTTPS, not Postgres, not F:\PostgreSQL18\data)

URL (exact):
https://chaoscentral.tailb71e7e.ts.net/v1/ingest/alerts

Method: POST
Follow redirects: on
Allow any certificate: off
Basic Authorization: off  (do not use that checkbox)

Header Params:
Content-Type = application/json
Authorization = Bearer <paste Windows User NFA_INGEST_DEVICE_BEARER_CURRENT>
X-NFA-Schema-Version = 1

Content Body (JSON). Put the notification body in rawText:
{"schemaVersion":1,"source":"bnn","deviceId":"nfa-primary-phone","capturedAt":null,"rawText":"<notification text>","metadata":{"channel":"macrodroid"}}

Success: HTTP 202 with accepted/ingestId/receivedAt
401 means the bearer or deviceId is wrong
Do not send to /webhooks/bnn unless you also want the Flutter app DB
Do not point MacroDroid at F:\PostgreSQL18\data
Keep the Play Store Tailscale app; remove the Chrome Tailscale shortcut
"@
  [System.IO.File]::WriteAllText($guidePath, $guide, [System.Text.UTF8Encoding]::new($false))
  Write-Output "payloads=$payloadsPath"
  Write-Output "guide=$guidePath"

  $bearer = [Environment]::GetEnvironmentVariable("NFA_INGEST_DEVICE_BEARER_CURRENT", "User")
  if (-not $bearer) {
    Write-Output "VERIFY skipped: NFA_INGEST_DEVICE_BEARER_CURRENT missing"
    return
  }
  $verifyBody = '{"schemaVersion":1,"source":"bnn","deviceId":"nfa-primary-phone","capturedAt":null,"rawText":"wire-verify Tailscale Serve path check","metadata":{"channel":"wire-verify"}}'
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Method POST -Uri "https://chaoscentral.tailb71e7e.ts.net/v1/ingest/alerts" -TimeoutSec 15 -Headers @{
      Authorization = "Bearer $bearer"
      "X-NFA-Schema-Version" = "1"
    } -ContentType "application/json" -Body $verifyBody
    Write-Output ("VERIFY https ingest status={0} body_len={1}" -f [int]$resp.StatusCode, $resp.Content.Length)
  } catch {
    $ex = $_.Exception
    $code = $null
    if ($ex.Response) { $code = [int]$ex.Response.StatusCode }
    Write-Output ("VERIFY https ingest FAILED status={0} message={1}" -f $code, $ex.Message)
  }
  return
}
if ($SetupDevinNfaPlatform) {
  $projectRoot = "D:\github\nfa-platform"
  $stagingRoot = "I:\LocalApps\Devin\projects\nfa-platform"
  $artifacts = Join-Path $stagingRoot "artifacts"
  $enrollment = Join-Path $RepoRoot "contracts\agentcore-project-enrollment.json"
  if (-not (Test-Path -LiteralPath $projectRoot)) { throw "Missing project root: $projectRoot" }
  if (-not (Test-Path -LiteralPath $enrollment)) { throw "Missing enrollment contract: $enrollment" }

  New-Item -ItemType Directory -Force -Path $stagingRoot, (Join-Path $stagingRoot "work"), $artifacts, (Join-Path $artifacts "sample-docs") | Out-Null

  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $rollbackDir = Join-Path $RepoRoot ".agentcore\rollback\nfa-platform-enroll-$stamp"
  New-Item -ItemType Directory -Force -Path $rollbackDir | Out-Null
  Copy-Item -LiteralPath $enrollment -Destination (Join-Path $rollbackDir "agentcore-project-enrollment.json")

  $envNames = @(
    "NFA_JWT_SECRET", "NFA_BNN_WEBHOOK_TOKEN", "NFA_GOOGLE_MAPS_API_KEY",
    "NFA_PUSH_PROVIDER", "NFA_FCM_SERVICE_ACCOUNT", "NFA_API_HOST", "NFA_API_PORT",
    "NFA_DEVIN_DB_HOST", "NFA_DEVIN_DB_PORT", "NFA_DEVIN_DB_NAME", "NFA_DEVIN_DB_USER",
    "NFA_DEVIN_DB_PASSWORD", "NFA_MIGRATOR_DB_PASSWORD", "NFA_FILE_STORAGE_ROOT",
    "NFA_INGEST_DEVICE_BEARER_CURRENT", "NFA_INGEST_DB_PASSWORD"
  )
  $envLines = foreach ($n in $envNames) {
    $u = [Environment]::GetEnvironmentVariable($n, "User")
    "{0}: UserPresent={1} UserLen={2}" -f $n, [bool]$u, $(if ($u) { $u.Length } else { 0 })
  }

  $listenLines = @()
  $netstat = netstat -ano | Select-String -Pattern ':(3000|8787|55433|5432|5433)\s'
  if ($netstat) {
    $listenLines += ($netstat | ForEach-Object { $_.Line.Trim() })
  } else {
    $listenLines += "no listeners on 3000/8787/55433/5432/5433"
  }
  $healthApi = "untried"
  $healthIngest = "untried"
  try { $healthApi = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri "http://127.0.0.1:3000/health").StatusCode } catch { $healthApi = "down" }
  try { $healthIngest = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri "http://127.0.0.1:8787/health").StatusCode } catch { $healthIngest = "down" }
  $listenLines += "health 127.0.0.1:3000/health=$healthApi"
  $listenLines += "health 127.0.0.1:8787/health=$healthIngest"

  $pg = Get-Service -Name "AgentCore-PostgreSQL18" -ErrorAction SilentlyContinue
  $pgLine = if ($pg) { "{0} Status={1} StartType={2}" -f $pg.Name, $pg.Status, $pg.StartType } else { "AgentCore-PostgreSQL18 missing" }

  $tsIp = ""
  $tsStatus = "tailscale command missing"
  if (Get-Command tailscale -ErrorAction SilentlyContinue) {
    $tsIp = (tailscale ip -4 2>$null | Select-Object -First 1)
    $tsStatus = ((tailscale status --self 2>$null | Select-Object -First 3) -join " | ")
  }

  $ingestExport = "E:\LocalApps\Backups\NFAAlerts\exports\raw-alerts-acceptance-20260817T071617Z.jsonl"
  $ingestExportExists = Test-Path -LiteralPath $ingestExport

  $launcher = Join-Path "I:\LocalApps\Devin" "Start-Devin-NfaPlatform.ps1"
  $launcherBody = @"
#Requires -Version 5.1
`$ErrorActionPreference = "Stop"
Set-Location -LiteralPath "D:\github\nfa-platform"
Write-Output "Devin execution cwd: D:\github\nfa-platform"
Write-Output "Devin staging: I:\LocalApps\Devin\projects\nfa-platform"
Write-Output "Native DB: 127.0.0.1:55433 / nfa_devin_dev (AgentCore-PostgreSQL18)"
Write-Output "Do not start infra/e2e docker-compose on host :5432 (Lobe uses it)."
Write-Output "MCP: agentcore-gateway only. No F: or H: mounts. No docker.sock."
"@
  [System.IO.File]::WriteAllText($launcher, $launcherBody)

  $packetPath = Join-Path $artifacts "DEVIN_PROOF_PACKET.md"
  $packet = @"
# Devin proof packet - nfa-platform on CHAOSCENTRAL

Writable repo: ``D:\github\nfa-platform``
Do not use ``D:\github\nfa-alerts-enterprise`` or ``D:\github_2\nfa-alerts-enterprise``.

Generated: $stamp
Rollback of enrollment: $rollbackDir

## 1. Staging / reachable API host

Approved native path (not Docker, not a second Postgres):

- PostgreSQL 18 Windows service ``AgentCore-PostgreSQL18``
- Host/port: ``127.0.0.1:55433``
- Database: ``nfa_devin_dev`` (PostGIS)
- App role: ``nfa_devin_app`` via User env ``NFA_DEVIN_DB_*``
- Fastify listen: User env ``NFA_API_HOST`` / ``NFA_API_PORT`` (defaults ``127.0.0.1:3000``)
- Phone ingest gateway (separate process): ``http://127.0.0.1:8787/v1/ingest/alerts``
- Documented Tailscale MagicDNS: ``https://chaoscentral.tailb71e7e.ts.net/v1/ingest/alerts``

Live at packet generation:

``````
Postgres service: $pgLine
Listeners:
$($listenLines -join "`n")
Tailscale IPv4: $(if ($tsIp) { $tsIp } else { "(none)" })
Tailscale status: $tsStatus
``````

Windows Flutter on this PC: ``APP_ENV=dev`` -> ``http://127.0.0.1:3000`` / ``ws://127.0.0.1:3000/ws``.

S26 phone cannot use 127.0.0.1 on the PC. Staging dart-defines must use the Tailscale IPv4 or MagicDNS host, and Fastify must listen on that interface (not loopback). Do not bind ``0.0.0.0`` until the operator confirms. Do not point staging/prod dart-defines at ``127.0.0.1`` (the app rejects it).

Start API locally from ``D:\github\nfa-platform`` after a new shell:

``````
. .\scripts\db_env.ps1
npm run dev -w @nfa/api
``````

Do **not** run ``infra/e2e/docker-compose.yml`` on this PC: it publishes ``127.0.0.1:5432``, which collides with live Lobe Postgres.

## 2. Real BNN / MacroDroid update payloads

Not present. ``nfa_ingest_capture`` export ``$ingestExport`` exists=$ingestExportExists and contains **acceptance-test** bodies (``Line 1 / Line 2``, ``rotation acceptance``), not live BNN originals or ``U/D`` updates.

Repo fixtures at ``packages/ts/ingestion/test/fixtures/bnn-update-fixtures.json`` are **REDACTED** grammar shapes only.

Operator must export a handful of real phone notification bodies (original + matching update for the same ``#<digits>`` id) into ``I:\LocalApps\Devin\projects\nfa-platform\artifacts\bnn-live-payloads.json``. Do not reconstruct from screenshots.

## 3. Full-stack test harness

Native Windows equivalent:

- DB: existing ``nfa_devin_dev`` on ``127.0.0.1:55433``
- API: ``npm run dev -w @nfa/api``
- Worker: ``npm run dev -w @nfa/worker``
- Tests: ``npm test -w @nfa/api`` and ``npm test -w @nfa/ingestion`` against that DB
- Flutter: ``apps/chaser`` ``flutter test`` / ``integration_test/e2e_test.dart``
- CI Docker/PostGIS harness is GitHub-only (``.github/workflows/ci.yml`` job ``e2e``)

Do not create another PostgreSQL cluster. Do not touch ``nfa_ingest_capture`` or ``nfa_codex_dev`` from this repo.

## 4. GitHub Actions

CI is **not** missing. ``.github/workflows/ci.yml`` runs authority-manifest, backend, Flutter, and Docker E2E. ``origin/master`` is ``9f9f9da``. Current local branch is ``release-pass/ci-e2e-manifest``. If GitHub still shows no runs, enable Actions on ``ynotfins/nfa-platform``; do not rewrite CI from scratch.

## 5. Sample insurance/incident PDFs

None found that are safe to use. Desktop PDFs located during search are unrelated/PII and must not be copied into this project. Operator: drop 1-2 redacted incident PDFs into ``I:\LocalApps\Devin\projects\nfa-platform\artifacts\sample-docs\``.

## 6. Firebase / push

Keep **no real push** for this pass. Code already fails closed: ``NFA_PUSH_PROVIDER`` defaults to ``none``; FCM/APNs require extra env vars. Do not provision ``NFA_FCM_SERVICE_ACCOUNT`` unless the operator explicitly asks for live push.

## Env presence (names/lengths only)

``````
$($envLines -join "`n")
``````
"@
  [System.IO.File]::WriteAllText($packetPath, $packet)

  $devinDir = Join-Path $projectRoot ".devin"
  New-Item -ItemType Directory -Force -Path $devinDir | Out-Null
  Copy-Item -LiteralPath $packetPath -Destination (Join-Path $devinDir "operator-proof-packet.md") -Force

  $py = Join-Path $RepoRoot "scripts\.venv\Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $py)) { $py = "python" }
  $enrollPy = Join-Path "I:\LocalApps\Devin" "enroll_nfa_platform.py"
  $enrollPyBody = @'
import json
from pathlib import Path
p = Path(r"D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json")
data = json.loads(p.read_text(encoding="utf-8"))
keys = [item.get("project_key") for item in data.get("projects", [])]
if "nfa-platform" in keys:
    print("enrollment already present")
else:
    entry = {
        "project_key": "nfa-platform",
        "name": "NFA Platform",
        "paths": [r"D:\github\nfa-platform"],
    }
    data["projects"].append(entry)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("enrollment added")
'@
  [System.IO.File]::WriteAllText($enrollPy, $enrollPyBody)
  & $py $enrollPy

  Write-Output "Created staging at $stagingRoot"
  Write-Output "Launcher: $launcher"
  Write-Output "Packet: $packetPath"
  Write-Output "Execution cwd: $projectRoot"
  Write-Output "Postgres: $pgLine"
  Write-Output "TailscaleIPv4: $(if ($tsIp) { $tsIp } else { '(none)' })"
  $envLines | ForEach-Object { Write-Output $_ }
  $listenLines | ForEach-Object { Write-Output ("LISTEN " + $_) }
  return
}
if ($SetupDevinNfa) {
  $projectRoot = "D:\github\nfa-alerts-enterprise"
  $stagingRoot = "I:\LocalApps\Devin\projects\nfa-alerts-enterprise"
  if (-not (Test-Path -LiteralPath $projectRoot)) { throw "Missing project root: $projectRoot" }
  New-Item -ItemType Directory -Force -Path $stagingRoot, (Join-Path $stagingRoot "work"), (Join-Path $stagingRoot "artifacts") | Out-Null
  $launcher = Join-Path "I:\LocalApps\Devin" "Start-Devin-NfaAlerts.ps1"
  $launcherBody = @"
#Requires -Version 5.1
`$ErrorActionPreference = "Stop"
Set-Location -LiteralPath "D:\github\nfa-alerts-enterprise"
Write-Output "Devin execution cwd: D:\github\nfa-alerts-enterprise"
Write-Output "Devin staging: I:\LocalApps\Devin\projects\nfa-alerts-enterprise"
Write-Output "MCP: agentcore-gateway only. No F: or H: mounts. No docker.sock."
if (Get-Command devin -ErrorAction SilentlyContinue) {
  devin --help | Out-Null
  Write-Output "Devin CLI is on PATH. Open this folder in Devin Desktop/CLI."
} else {
  Write-Output "Devin CLI not on PATH in this process. Open Devin Desktop on D:\github\nfa-alerts-enterprise."
}
"@
  [System.IO.File]::WriteAllText($launcher, $launcherBody)
  Write-Output "Created staging at $stagingRoot"
  Write-Output "Launcher: $launcher"
  Write-Output "Execution cwd: $projectRoot"
  $py = Join-Path $RepoRoot "scripts\.venv\Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $py)) { $py = "python" }
  $enrollPy = Join-Path "I:\LocalApps\Devin" "enroll_nfa_alerts_enterprise.py"
  $enrollPyBody = @'
import json
from pathlib import Path
p = Path(r"D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json")
data = json.loads(p.read_text(encoding="utf-8"))
keys = [item.get("project_key") for item in data.get("projects", [])]
if "nfa-alerts-enterprise" in keys:
    print("enrollment already present")
else:
    entry = {
        "project_key": "nfa-alerts-enterprise",
        "name": "NFA Alerts Enterprise",
        "paths": [r"D:\github\nfa-alerts-enterprise"],
    }
    data["projects"].append(entry)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("enrollment added")
'@
  [System.IO.File]::WriteAllText($enrollPy, $enrollPyBody)
  & $py $enrollPy
  return
}
if ($PrepareRestart) {
  Set-Location -LiteralPath $RepoRoot
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
  $restore = @(
    "ops/Backup-AgentCorePostgres.ps1",
    "ops/Invoke-AgentCoreMaintenance.ps1",
    "ops/Start-AgentCorePostgres.ps1",
    "ops/Test-AgentCorePostgresRestore.ps1",
    "ops/bifrost/Invoke-AgentCoreBifrostDailyAudit.ps1",
    "ops/bifrost/Invoke-AgentCoreBifrostWatchdog.ps1",
    "ops/zoo-code/Start-ZooCodeQdrant.ps1"
  )
  git restore -- $restore
  if ($LASTEXITCODE -ne 0) { throw "git restore of ops launchers failed with $LASTEXITCODE" }
  Write-Output "Restored ops launcher scripts from HEAD so logon/nightly tasks have their targets."

  $gitBranch = (git branch --show-current)
  $gitHead = (git log -1 --oneline)
  $pg = Get-Service -Name "AgentCore-PostgreSQL18" -ErrorAction SilentlyContinue
  $pgLine = if ($pg) { "{0} Status={1} StartType={2}" -f $pg.Name, $pg.Status, $pg.StartType } else { "AgentCore-PostgreSQL18 missing" }
  $bifrost = "down"
  try { $bifrost = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri "http://127.0.0.1:8080/health").Content } catch { $bifrost = "down: $($_.Exception.Message)" }
  $api3000 = "down"
  try { $api3000 = "status=" + [int](Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri "http://127.0.0.1:3000/health").StatusCode } catch { $api3000 = "down" }
  $ingest8787 = "down"
  try { $null = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri "http://127.0.0.1:8787/health"; $ingest8787 = "health-endpoint-present" } catch { $ingest8787 = "listener-or-no-/health (expected for this gateway)" }
  $tsServe = (tailscale serve status 2>&1 | Out-String).Trim()
  $taskBifrost = (Get-ScheduledTask -TaskPath "\AgentCore\" -TaskName "AgentCore-Bifrost-Gateway" -ErrorAction SilentlyContinue | Select-Object State, @{n="Enabled";e={$_.Settings.Enabled}})
  $taskWatch = (Get-ScheduledTask -TaskPath "\AgentCore\" -TaskName "AgentCore-Bifrost-Watchdog" -ErrorAction SilentlyContinue)
  $watchState = if ($taskWatch) { $taskWatch.State.ToString() } else { "missing" }
  $dockerBefore = (docker ps --format "{{.Names}}" 2>$null | Out-String).Trim()

  $containers = @(
    "openhands-local-8003",
    "nfa-rag-postgres",
    "lobehub",
    "lobe-redis",
    "lobe-postgres",
    "lobe-searxng"
  )
  docker stop @containers 2>&1 | Out-String | Write-Output
  Write-Output "Stopped Docker containers for a clean VHDX shutdown."

  $packetDir = "D:\launchers\handoffs"
  New-Item -ItemType Directory -Force -Path $packetDir | Out-Null
  $packetPath = Join-Path $packetDir "RESTART_PACKET_2026-08-29.txt"
  $packet = @"
RESTART PACKET - 2026-08-29
Prepared: $stamp local. Do not reboot until this packet is in hand.
PC: CHAOSCENTRAL. Operator: ynotf.

0. THIS REBOOT
Do not pull/fetch/merge/rebase. Do not write H: or Swarm roots. Do not print secrets.
Do not create .env files. Do not swap Bifrost for the MAF host. Watchdog stays disabled.
Do not point phones at F:\PostgreSQL18\data.

1. PRE-REBOOT STATE
Git branch: $gitBranch
HEAD: $gitHead
PG18: $pgLine  (leave running; SCM will stop/start)
Bifrost /health: $bifrost
Bifrost task: \AgentCore\AgentCore-Bifrost-Gateway starts At logon. Watchdog: $watchState (keep Disabled)
NFA Fastify :3000 /health: $api3000  (user process; will die on reboot)
NFA ingest gateway :8787: $ingest8787  (task \NFA\AlertsIngestGateway AtLogOn)
Tailscale Serve (tailnet only, not Funnel):
$tsServe
Docker running before stop:
$dockerBefore
Devin repo: D:\github\nfa-platform
Antigravity NFA copy: D:\github_2\nfa-alerts-enterprise
MacroDroid import file: C:\Users\ynotf\Downloads\nfa-alerts.corrected.macro
Ingest URL: https://chaoscentral.tailb71e7e.ts.net/v1/ingest/alerts
Proof packet: D:\github\nfa-platform\.devin\operator-proof-packet.md

2. WHAT WAS DONE TO PREPARE
Restored ops launcher scripts from git HEAD.
Stopped Docker: openhands-local-8003, nfa-rag-postgres, lobehub, lobe-redis, lobe-postgres, lobe-searxng.
Left PG18, Bifrost, Tailscale Serve config, and NFA ingest gateway for Windows/Tailscale restart.
Did not reboot.

3. AFTER REBOOT / AFTER LOGIN (order)
A. Confirm drive letters still C D E F G H I J. If F: moved, restore F: first.
B. Get-Service AgentCore-PostgreSQL18 = Running. TCP 127.0.0.1:55433. No password print.
C. Logon starts Bifrost. Confirm http://127.0.0.1:8080/health. If not:
   Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
D. Confirm ingest: listener 127.0.0.1:8787 and ``tailscale serve status`` still proxies MagicDNS to that port.
E. Start Docker Desktop. Then:
   powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\scripts\maf_recall\openhands\Start-OpenHands.ps1
   Confirm http://127.0.0.1:8003/ready = 200
F. If Devin needs the Flutter API again, from D:\github\nfa-platform:
   . .\scripts\db_env.ps1
   npm run dev -w @nfa/api
   Confirm http://127.0.0.1:3000/health = 200
G. Swarm: do not start from AgentCore. Recall only through agentcore-gateway -> agentcore-memory.
H. Zoo-Code Qdrant if 6333 down:
   powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\zoo-code\Start-ZooCodeQdrant.ps1
I. Open D:\github\agentcore-control-plane. Dirty tree is inherited; do not commit it as one blob.
J. Devin Desktop: open D:\github\nfa-platform only.

4. IDE
MCP = agentcore-gateway only at http://127.0.0.1:8080/mcp
Morph stays out of Cursor.

5. DO NOT
Do not enable AgentCore-Bifrost-Watchdog.
Do not mount F: or H: into Docker.
Do not use OneDrive Desktop as a repo root.
Do not connect IDEs to :65432.
Do not start LangGraph Studio unless needed.
Do not enable Tailscale Funnel.

6. NEXT AGENT PROMPT
PC just rebooted. Verify D:\launchers\handoffs\RESTART_PACKET_2026-08-29.txt then:
1) F: letter + PG18 :55433 + Bifrost /health
2) Docker Desktop + OpenHands :8003/ready
3) tailscale serve still on 8787; ingest MagicDNS
4) Do not pull git.
"@
  $utf8 = [System.Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllText($packetPath, $packet, $utf8)
  $desktopPacket = "C:\Users\ynotf\OneDrive\Desktop\Temp\restart.txt"
  $desktopDir = Split-Path -Parent $desktopPacket
  if (Test-Path -LiteralPath $desktopDir) {
    [System.IO.File]::WriteAllText($desktopPacket, $packet, $utf8)
    Write-Output "Wrote $desktopPacket"
  }
  Write-Output "Wrote $packetPath"
  Write-Output "SAFE TO REBOOT after you close Cursor/IDEs."
  return
}
if ($CommitPush) {
  Set-Location -LiteralPath $RepoRoot
  git add -- "scripts/maf_recall/enroll_gateway_clients.ps1"
  git commit -m "Add MAF Recall realignment package and keep the live gateway frozen."
  if ($LASTEXITCODE -ne 0) { throw "git commit failed with $LASTEXITCODE" }
  git push origin HEAD
  if ($LASTEXITCODE -ne 0) { throw "git push failed with $LASTEXITCODE" }
  git status --short --branch
  git log -1 --oneline
  return
}
$python = Join-Path $RepoRoot "scripts\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
$helper = Join-Path $RepoRoot ".agentcore\scripts\Enroll-GatewayClients.ps1"
if (Test-Path $helper) {
  Write-Host "Delegating to $helper"
  & $helper -RepoRoot $RepoRoot -Apply:$Apply
  return
}
$cherry = Join-Path $RepoRoot "scripts\cherry\enroll_agentcore_gateway.py"
$contract = Join-Path $RepoRoot "contracts\agentcore-gateway-client.json"
if (-not (Test-Path $contract)) { throw "Missing gateway contract: $contract" }
Write-Host "Gateway contract: $contract"
Write-Host "Expected single MCP: agentcore-gateway http://127.0.0.1:8080/mcp"
if (Test-Path $cherry) {
  if ($Apply) { & $python $cherry --apply } else { & $python $cherry --dry-run }
} else {
  Write-Host "Cherry enroll helper not found; contract path validated as present."
}
Write-Host "Reminder: do not add raw Recall MCP, port 65432, or OpenRouter MCP to IDE baselines."
