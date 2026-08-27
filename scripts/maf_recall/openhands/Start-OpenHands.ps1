param(
  [string]$ComposeFile = (Join-Path $PSScriptRoot 'docker-compose.yml')
)

$ErrorActionPreference = 'Stop'

$stateRoot = 'I:\LocalApps\OpenHands\state'
$projectsRoot = 'D:\OpenHandsProjects'

New-Item -ItemType Directory -Force -Path $stateRoot, $projectsRoot | Out-Null

if (-not $env:OPENROUTER_API_KEY) {
  Write-Warning 'OPENROUTER_API_KEY is not visible in this process. OpenHands may prompt for provider settings.'
}

$existing = docker ps -a --filter name=openhands-local-8003 --format '{{.Names}}'
if ($existing -contains 'openhands-local-8003') {
  docker start openhands-local-8003 | Out-Null
} else {
  docker compose -f $ComposeFile up -d
}

Write-Output 'OpenHands target: http://127.0.0.1:8003/canvas/'
Write-Output 'Readiness target: http://127.0.0.1:8003/ready'
