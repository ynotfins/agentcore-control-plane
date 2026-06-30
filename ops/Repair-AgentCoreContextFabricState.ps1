param(
  [string[]]$CandidateRoots = @("D:\Autonomy"),
  [string]$BackupRoot = "E:\AgentCoreArchive\backups_cold\context-fabric-invalid"
)

$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupBase = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Force -Path $backupBase | Out-Null

$moved = New-Object System.Collections.Generic.List[object]

foreach ($root in $CandidateRoots) {
  if (-not (Test-Path -LiteralPath $root)) { continue }
  $candidate = Join-Path $root ".context-fabric"
  if (-not (Test-Path -LiteralPath $candidate)) { continue }

  $isGitRepo = $false
  try {
    git -C $root rev-parse --is-inside-work-tree *> $null
    $isGitRepo = ($LASTEXITCODE -eq 0)
  } catch {
    $isGitRepo = $false
  }
  if ($isGitRepo) { continue }

  $safeName = (($root -replace '[:\\\/ ]', '_').Trim('_'))
  $target = Join-Path $backupBase $safeName
  Move-Item -LiteralPath $candidate -Destination $target
  $moved.Add([pscustomobject]@{
    root = $root
    source = $candidate
    backup = $target
  }) | Out-Null
}

$manifest = @{
  ok = $true
  moved = @($moved.ToArray())
  backup_root = $backupBase
  completed_at = (Get-Date).ToUniversalTime().ToString("o")
}

$manifestPath = Join-Path $backupBase "manifest.json"
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$manifest | ConvertTo-Json -Depth 6
