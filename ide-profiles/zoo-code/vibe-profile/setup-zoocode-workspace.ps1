#Requires -Version 7.0
<#
.SYNOPSIS
  Copy the AgentCore Zoo Code vibe profile (.roomodes, .roo/, .rooignore) into one or more workspaces.
.DESCRIPTION
  - Verifies PowerShell 7, the OmniRoute loopback (http://127.0.0.1:20128/v1), the routed model ids,
    and that required Windows User environment variables exist (names only; values are never printed).
  - Backs up any existing target files to <workspace>\.agentcore\rollback\zoo-vibe-<timestamp>\ before copying.
  - Never writes secrets. MCP is agentcore-gateway only; database access stays behind the gateway.
.EXAMPLE
  pwsh -File setup-zoocode-workspace.ps1 -Workspace D:\github\my-app, D:\github\sister-crm
.EXAMPLE
  pwsh -File setup-zoocode-workspace.ps1 -Workspace D:\github\my-app -WhatIf
#>
[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory)][string[]]$Workspace,
  [string]$OmniRouteBaseUrl = 'http://127.0.0.1:20128/v1',
  [switch]$SkipModelCheck
)
$ErrorActionPreference = 'Stop'
$source = $PSScriptRoot
$items = @('.roomodes', '.rooignore', '.roo')
$requiredModels = @('deepseek/deepseek-v4.1-flash-1017', 'sol-kie-heavy')
$requiredEnv = @('BIFROST_MCP_VK_APP_ZOO_CODE', 'OPENROUTER_API_KEY', 'DEEPINFRA_API_KEY', 'TOGETHER_API_KEY', 'KIE_API_KEY')

function Write-Step([string]$Message, [string]$Status = 'OK') {
  $color = @{ OK = 'Green'; WARN = 'Yellow'; FAIL = 'Red' }[$Status]
  Write-Host ("[{0}] {1}" -f $Status, $Message) -ForegroundColor $color
}

$missing = $requiredEnv | Where-Object { -not [Environment]::GetEnvironmentVariable($_, 'User') }
if ($missing) { Write-Step "Missing Windows User env vars: $($missing -join ', ')" 'WARN' } else { Write-Step 'Required Windows User env vars present' }

try {
  $models = (Invoke-RestMethod -Uri "$OmniRouteBaseUrl/models" -TimeoutSec 10 -Headers @{ Authorization = 'Bearer omniroute-local' }).data.id
  Write-Step "OmniRoute reachable at $OmniRouteBaseUrl ($($models.Count) models)"
  if (-not $SkipModelCheck) {
    $absent = $requiredModels | Where-Object { $_ -notin $models }
    if ($absent) { Write-Step "OmniRoute is missing routed model ids: $($absent -join ', ')" 'FAIL'; exit 2 }
    Write-Step 'All routed model ids are available'
  }
} catch {
  Write-Step "OmniRoute not reachable at $OmniRouteBaseUrl. Start scheduled task 'AgentCore-OmniRoute'." 'FAIL'
  exit 1
}

foreach ($ws in $Workspace) {
  if (-not (Test-Path -LiteralPath $ws -PathType Container)) { Write-Step "Not a folder: $ws" 'FAIL'; continue }
  $root = (Resolve-Path -LiteralPath $ws).Path
  if ($root -match '(?i)swarm(vault|claw)') { Write-Step "Refusing Swarm-owned path: $root (swarm_project_refused)" 'FAIL'; continue }
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $backup = Join-Path $root ".agentcore\rollback\zoo-vibe-$stamp"
  foreach ($name in $items) {
    $dest = Join-Path $root $name
    if ((Test-Path -LiteralPath $dest) -and $PSCmdlet.ShouldProcess($dest, 'Back up existing')) {
      New-Item -ItemType Directory -Force -Path $backup | Out-Null
      Copy-Item -LiteralPath $dest -Destination $backup -Recurse -Force
    }
    if ($PSCmdlet.ShouldProcess($dest, 'Install Zoo vibe profile')) {
      Copy-Item -LiteralPath (Join-Path $source $name) -Destination $root -Recurse -Force
    }
  }
  Write-Step "Installed into $root$(if (Test-Path $backup) { " (backup: $backup)" })"
}

Write-Host ''
Write-Host 'One-time per host (Zoo Code UI): Settings > About > Import Settings >' -ForegroundColor Cyan
Write-Host "  $(Join-Path $source 'zoo-omniroute-settings.json')" -ForegroundColor Cyan
Write-Host 'This loads the OmniRoute provider profiles, per-mode model stickiness, and auto-approve rules.' -ForegroundColor Cyan
