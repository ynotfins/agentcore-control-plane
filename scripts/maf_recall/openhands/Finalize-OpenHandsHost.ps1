param(
  [string]$SourceRoot = $PSScriptRoot,
  [string]$TargetRoot = 'I:\LocalApps\OpenHands'
)

$ErrorActionPreference = 'Stop'

$required = @(
  'docker-compose.yml',
  'START_OPENHANDS.md',
  'Start-OpenHands.ps1'
)

foreach ($name in $required) {
  $src = Join-Path $SourceRoot $name
  if (-not (Test-Path -LiteralPath $src)) {
    throw "Missing source asset: $src"
  }
}

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $TargetRoot 'state'), 'D:\OpenHandsProjects' | Out-Null

foreach ($name in $required) {
  Copy-Item -LiteralPath (Join-Path $SourceRoot $name) -Destination (Join-Path $TargetRoot $name) -Force
}

$running = docker ps --filter name=openhands-local-8003 --format '{{.Names}}'
if ($running -notcontains 'openhands-local-8003') {
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $TargetRoot 'Start-OpenHands.ps1')
}

$stale = docker ps -a --filter name=openhands-local --format '{{.Names}}' |
  Where-Object { $_ -eq 'openhands-local' }
if ($stale) {
  docker rm openhands-local | Out-Null
}

$ready = Invoke-WebRequest -Uri 'http://127.0.0.1:8003/ready' -UseBasicParsing -TimeoutSec 10
if ($ready.StatusCode -ne 200) {
  throw "OpenHands readiness failed: $($ready.StatusCode)"
}

Write-Output 'OpenHands host assets mirrored and runtime verified.'
Write-Output 'URL: http://127.0.0.1:8003/canvas/'
