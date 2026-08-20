[CmdletBinding()]
param(
  [string]$Root = "I:\LocalApps\ZooCode\qdrant",
  [int]$StartupTimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

$exe = Join-Path $Root "current\qdrant.exe"
$config = Join-Path $Root "config\zoo-code-qdrant.yaml"
$logs = Join-Path $Root "logs"
$runtime = Join-Path $Root "runtime"
$pidFile = Join-Path $runtime "qdrant.pid"
$stdout = Join-Path $logs "qdrant.out.log"
$stderr = Join-Path $logs "qdrant.err.log"

foreach ($path in @($logs, $runtime)) {
  if (-not (Test-Path -LiteralPath $path)) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
  }
}

if (-not (Test-Path -LiteralPath $exe)) {
  throw "Missing Qdrant executable: $exe"
}
if (-not (Test-Path -LiteralPath $config)) {
  throw "Missing Qdrant config: $config"
}

try {
  $health = Invoke-RestMethod -Uri "http://127.0.0.1:6333/healthz" -TimeoutSec 2
  if ($health.title -or $health) {
    [PSCustomObject]@{ status = "already_running"; url = "http://127.0.0.1:6333" }
    return
  }
} catch {
}

$proc = Start-Process -FilePath $exe `
  -ArgumentList @("--config-path", $config) `
  -WorkingDirectory $Root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr `
  -PassThru

Set-Content -LiteralPath $pidFile -Value ([string]$proc.Id) -Encoding ascii

$deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
do {
  Start-Sleep -Milliseconds 500
  try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:6333/healthz" -TimeoutSec 2
    [PSCustomObject]@{ status = "started"; pid = $proc.Id; url = "http://127.0.0.1:6333"; health = $health.title }
    return
  } catch {
  }
} while ((Get-Date) -lt $deadline)

throw "Qdrant did not become healthy within $StartupTimeoutSeconds seconds. Check $stderr"
