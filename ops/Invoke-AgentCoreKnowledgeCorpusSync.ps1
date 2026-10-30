param(
  [switch]$Apply,
  [string]$Rollback,
  [string]$CatalogPath = (Join-Path $PSScriptRoot "..\contracts\knowledge-corpus-catalog.json")
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
$candidates = @(
  (Join-Path $repoRoot "scripts\.venv\Scripts\python.exe"),
  "D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe",
  "F:\AgentCore\runtime\knowledge-corpus\Scripts\python.exe"
)
$python = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) {
  throw "Runtime python missing. Install the knowledge-sync pins into scripts\.venv."
}

$logRoot = "E:\AgentCoreArchive\agentcore-memory\service-logs\knowledge-sync"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $logRoot "sync-$stamp.log"

$workerArgs = @(
  "-m", "scripts.engineering.knowledge_sync.sync_worker",
  "--catalog", $CatalogPath
)
if ($Apply) { $workerArgs += "--apply" }
if ($Rollback) { $workerArgs += @("--rollback", $Rollback) }

$psi = @{
  FilePath = $python
  ArgumentList = $workerArgs
  WorkingDirectory = $repoRoot
  RedirectStandardOutput = $log
  RedirectStandardError = ($log + ".err")
  PassThru = $true
  WindowStyle = "Hidden"
  Wait = $true
}
$proc = Start-Process @psi
if ($proc.ExitCode -ne 0) {
  throw "KnowledgeCorpusSync failed with exit $($proc.ExitCode). See $log"
}

[pscustomobject]@{
  ok = $true
  apply = [bool]$Apply
  rollback = $Rollback
  log = $log
  python = $python
  note = "Nightly registration uses -Apply at 03:00."
} | ConvertTo-Json
