param(
  [string]$ConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ConfigPath)) {
  throw "SwarmRecall config not found: $ConfigPath"
}

$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$targets = Get-CimInstance Win32_Process | Where-Object {
  ($_.Name -ieq "meilisearch.exe" -and $_.CommandLine -like "*$($config.search.dataPath)*") -or
  ($_.Name -match "^node(\.exe)?$" -and $_.CommandLine -like "*$($config.source.apiDist)*")
}

foreach ($target in $targets) {
  Write-Host "Stopping SwarmRecall process PID $($target.ProcessId): $($target.CommandLine)"
  Stop-Process -Id $target.ProcessId -Force
}

if (-not $targets) {
  Write-Host "No SwarmRecall API or Meilisearch runtime processes matched the approved config."
}
