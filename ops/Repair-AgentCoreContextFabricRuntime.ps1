param(
  [string]$ProjectRoot = "D:\github\agentcore-control-plane",
  [int]$MaxBufferBytes = 134217728,
  [string]$BackupRoot = "E:\AgentCoreArchive\backups_cold\context-fabric-runtime"
)

$ErrorActionPreference = "Stop"

$runtimeRoot = Join-Path $ProjectRoot ".context-fabric\runtime"
$watcher = Join-Path $runtimeRoot "dist\engines\watcher.js"
if (-not (Test-Path -LiteralPath $watcher)) {
  throw "Context Fabric runtime watcher not found. Run context-fabric bootstrap/repair first: $watcher"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item -LiteralPath $watcher -Destination (Join-Path $backupDir "watcher.js") -Force

$text = Get-Content -LiteralPath $watcher -Raw
if ($text -match "maxBuffer\s*:") {
  [pscustomobject]@{
    ok = $true
    changed = $false
    detail = "maxBuffer already present"
    watcher = $watcher
    backup = $backupDir
  } | ConvertTo-Json -Depth 5
  exit 0
}

$patched = $text -replace "spawnSync\(([^;]+?),\s*\{\s*encoding:\s*['""]utf8['""]\s*\}\)", "spawnSync(`$1, { encoding: 'utf8', maxBuffer: $MaxBufferBytes })"
if ($patched -eq $text) {
  throw "Unable to find supported context-fabric spawnSync pattern in $watcher"
}

Set-Content -LiteralPath $watcher -Value $patched -Encoding utf8

[pscustomobject]@{
  ok = $true
  changed = $true
  watcher = $watcher
  max_buffer_bytes = $MaxBufferBytes
  backup = $backupDir
} | ConvertTo-Json -Depth 5
