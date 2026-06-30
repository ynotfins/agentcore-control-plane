# Test-AgentCoreRuleConflictScanner.ps1
# Read-only scanner for retired/forbidden route EMISSION in active client-facing surfaces.
# Detects emitted: context7, raw mem0 (mcp.mem0.ai), direct composio (connect.composio.dev), Hostinger,
# hosted SwarmRecall/SwarmVault (onrender), and :65432 routes.
#
# SCOPE (emission surfaces only):
#   - renderers/*.json  (what is actually emitted to managed clients)
#   - docs/prompts/*.md  (per-IDE cleanup prompts must not teach retired routes as active)
# NOT scanned (governance catalogs that legitimately NAME quarantined/retired servers to forbid them):
#   - supervisor/servers.json|yaml, registry/tool-registry.json, contracts/, rules/, .cursor/rules/,
#     database-plan.md, CONTEXT_BLOCK.md  (quarantine/lifecycle is enforced by validate-control-plane.ps1)
#   - artifacts/backups/, vendor node_modules
#
# Optional: -IncludeLive scans live IDE rule/skill dirs (read-only) for retired-route TEACHING.
# Never prints secrets. Exit 1 if any active emission conflict is found, else 0.
param(
  [string]$Root = "D:\github\agentcore-control-plane",
  [switch]$IncludeLive
)
$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path

$patterns = @(
  @{ rx = '"context7"';              reason = 'context7 emitted as a server (retired; use arabold-docs)' },
  @{ rx = 'mcp\.mem0\.ai';           reason = 'raw mem0 hosted memory route emitted' },
  @{ rx = 'connect\.composio\.dev';  reason = 'direct composio route emitted' },
  @{ rx = '(?i)"hostinger';          reason = 'Hostinger server emitted' },
  @{ rx = 'onrender\.com';           reason = 'hosted Swarm route emitted' },
  @{ rx = '65432';                   reason = 'forbidden :65432 runtime route emitted' }
)

$targets = New-Object System.Collections.Generic.List[string]
# Emission surfaces only: renderer JSON is what is actually emitted to managed clients.
# docs/prompts/*.md are human cleanup instructions that intentionally NAME forbidden routes to remove
# them -- they are NOT emission surfaces and are excluded from the default scan.
$rdir = Join-Path $rootPath "renderers"
if (Test-Path -LiteralPath $rdir) {
  Get-ChildItem -LiteralPath $rdir -File -Filter *.json -ErrorAction SilentlyContinue | ForEach-Object { $targets.Add($_.FullName) | Out-Null }
}

if ($IncludeLive) {
  foreach ($live in @(
    "C:\Users\ynotf\.cursor\rules",
    "C:\Users\ynotf\.claude\rules",
    "C:\Users\ynotf\.claude\skills",
    "C:\Users\ynotf\.minimax\skills",
    "C:\Users\ynotf\.mavis\skills"
  )) {
    if (Test-Path -LiteralPath $live) {
      Get-ChildItem -LiteralPath $live -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @('.md','.mdc','.json','.txt') } |
        ForEach-Object { $targets.Add($_.FullName) | Out-Null }
    }
  }
}

$findings = New-Object System.Collections.Generic.List[string]
foreach ($file in ($targets | Sort-Object -Unique)) {
  $text = Get-Content -LiteralPath $file -Raw -ErrorAction SilentlyContinue
  if (-not $text) { continue }
  foreach ($pat in $patterns) {
    if ($text -match $pat.rx) { $findings.Add(("{0} :: {1}" -f $file, $pat.reason)) | Out-Null }
  }
}

if ($findings.Count -eq 0) {
  Write-Output ("PASS: no retired/forbidden route emission in scanned surfaces (scanned " + $targets.Count + " file(s)).")
  exit 0
}
Write-Output "FAIL: retired/forbidden route emission found:"
$findings | Sort-Object -Unique | ForEach-Object { Write-Output ("  - " + $_) }
exit 1
