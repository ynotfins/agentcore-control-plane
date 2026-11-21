#Requires -Version 5.1
[CmdletBinding()]
param(
  [switch]$SkipInstall,
  [switch]$SkipBuild,
  [string]$PaperclipHome = 'I:\LocalApps\Paperclip'
)
$ErrorActionPreference = 'Stop'

$RepoRoot = 'D:\github\agentcore-control-plane'
$Ops = Join-Path $RepoRoot 'ops'
$RepoPluginRoot = Join-Path $RepoRoot 'plugins\paperclip-automation-board'
$InstallRoot = Join-Path $PaperclipHome 'plugins\agentcore-automation-board'

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Copy-EmbedFile([string]$EmbedName, [string]$DestPath) {
  $src = Join-Path $Ops $EmbedName
  if (-not (Test-Path -LiteralPath $src)) { throw "Missing embed source: $src" }
  Ensure-Dir (Split-Path -Parent $DestPath)
  Copy-Item -LiteralPath $src -Destination $DestPath -Force
}

$map = @(
  @{ embed = 'pcab-package.json'; dest = 'package.json' },
  @{ embed = 'pcab-tsconfig.json'; dest = 'tsconfig.json' },
  @{ embed = 'pcab-build-ui.mjs'; dest = 'scripts/build-ui.mjs' },
  @{ embed = 'pcab-src-constants.ts'; dest = 'src/constants.ts' },
  @{ embed = 'pcab-src-manifest.ts'; dest = 'src/manifest.ts' },
  @{ embed = 'pcab-src-plugin.ts'; dest = 'src/plugin.ts' },
  @{ embed = 'pcab-src-worker.ts'; dest = 'src/worker.ts' },
  @{ embed = 'pcab-src-index.ts'; dest = 'src/index.ts' },
  @{ embed = 'pcab-ui-constants.ts'; dest = 'ui/constants.ts' },
  @{ embed = 'pcab-ui-board.tsx'; dest = 'ui/AutomationBoardPage.tsx' },
  @{ embed = 'pcab-ui-sidebar.tsx'; dest = 'ui/AutomationsSidebarLink.tsx' },
  @{ embed = 'pcab-ui-index.tsx'; dest = 'ui/index.tsx' }
)

Write-Host "Materializing plugin at $RepoPluginRoot"
foreach ($item in $map) {
  Copy-EmbedFile -EmbedName $item.embed -DestPath (Join-Path $RepoPluginRoot $item.dest)
}

if (-not $SkipBuild) {
  Push-Location $RepoPluginRoot
  try {
    if (-not (Test-Path -LiteralPath 'node_modules')) {
      npm install --no-fund --no-audit
    }
    npm run build
  } finally {
    Pop-Location
  }
}

Write-Host "Syncing install copy to $InstallRoot"
if (Test-Path -LiteralPath $InstallRoot) {
  Remove-Item -LiteralPath $InstallRoot -Recurse -Force
}
Ensure-Dir (Split-Path -Parent $InstallRoot)
Copy-Item -LiteralPath $RepoPluginRoot -Destination $InstallRoot -Recurse -Force

if (-not $SkipInstall) {
  Push-Location $PaperclipHome
  try {
    npx --yes paperclipai plugin install $RepoPluginRoot
  } finally {
    Pop-Location
  }
}

Write-Host 'OK AgentCore Paperclip automation board plugin installed.'