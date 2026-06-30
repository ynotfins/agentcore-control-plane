# Test-AgentCoreOllamaReadiness.ps1
# Read-only Ollama preflight for the optional local-enhancement layer.
# Ollama is OPTIONAL and is NOT a mandatory MCP baseline server.
# Tiers (per rollout plan amendment 0.3):
#   PASS  - Ollama listening AND (no required model OR required model present)
#   WARN  - Ollama installed but not listening
#   SKIP  - Ollama not needed for this stage / not installed and not required
#   FAIL  - a configured workflow explicitly requires Ollama (-Require) and it is unavailable/model missing
# Does NOT pull models. Never prints secrets.
param(
  [string]$BaseUrl = "http://127.0.0.1:11434",
  [string[]]$RequiredModels = @(),   # e.g. @('nomic-embed-text')
  [switch]$Require                   # set when a configured workflow requires Ollama
)

$ErrorActionPreference = "Stop"
function Write-Tier($tier, $msg) { Write-Output ("[{0}] {1}" -f $tier, $msg) }

$ollamaExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
$installed = Test-Path -LiteralPath $ollamaExe

$listening = $false
$models = @()
try {
  $resp = Invoke-RestMethod -Uri "$BaseUrl/api/tags" -Method Get -TimeoutSec 4
  $listening = $true
  $models = @($resp.models | ForEach-Object { $_.name })
} catch {
  $listening = $false
}

if ($listening) {
  $missing = @($RequiredModels | Where-Object { $_ -notin ($models | ForEach-Object { ($_ -split ':')[0] }) -and $_ -notin $models })
  if ($missing.Count -gt 0) {
    if ($Require) { Write-Tier "FAIL" ("Ollama listening but required model(s) missing: " + ($missing -join ', ') + " (do not auto-pull; operator approval required)"); exit 1 }
    Write-Tier "WARN" ("Ollama listening; optional model(s) not installed: " + ($missing -join ', ') + "; installed=" + ($(if($models){$models -join ', '}else{'none'})))
    exit 0
  }
  Write-Tier "PASS" ("Ollama listening at $BaseUrl; models=" + $(if($models){$models -join ', '}else{'none installed'}))
  exit 0
}

if ($Require) { Write-Tier "FAIL" "Ollama required by configured workflow but not listening at $BaseUrl"; exit 1 }
if ($installed) { Write-Tier "WARN" "Ollama installed ($ollamaExe) but not listening at $BaseUrl. Optional layer; start it only if needed (do not auto-pull models)."; exit 0 }
Write-Tier "SKIP" "Ollama not installed and not required for this rollout stage. Optional enhancement layer only."
exit 0
