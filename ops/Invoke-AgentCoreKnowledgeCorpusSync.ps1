param(
  [switch]$Apply,
  [string]$Rollback,
  [string]$CatalogPath = (Join-Path $PSScriptRoot "..\contracts\knowledge-corpus-catalog.json")
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
$python = Join-Path $repoRoot "scripts\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
  throw "Runtime python missing: $python"
}

$logRoot = "E:\AgentCoreArchive\agentcore-memory\service-logs\knowledge-sync"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $logRoot "sync-$stamp.log"

$args = @(
  "-m", "scripts.engineering.knowledge_sync.sync_worker",
  "--catalog", $CatalogPath
)
if ($Apply) { $args += "--apply" }
if ($Rollback) { $args += @("--rollback", $Rollback) }

$psi = @{
  FilePath = $python
  ArgumentList = $args
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
  note = "Dry-run unless -Apply. Scheduled registration is operator-only."
} | ConvertTo-Json
