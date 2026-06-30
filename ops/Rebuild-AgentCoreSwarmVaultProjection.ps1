param(
  [string]$VaultRoot = "F:\AgentCore\agentmemory\swarmvault",
  [string]$StateRoot = "F:\AgentCore\agentmemory\projection-state",
  [string]$BackupRoot = "E:\AgentCoreArchive\backups_cold\swarmvault-projection-rebuild",
  [string]$ProjectorScript = "D:\github\agentcore-control-plane\ops\Invoke-AgentCoreMemoryProjector.ps1",
  [int]$Limit = 500
)

$ErrorActionPreference = "Stop"

function Copy-FileIntoBackup {
  param(
    [string]$SourcePath,
    [string]$BackupBase,
    [string]$RootPath
  )

  $resolvedRoot = (Resolve-Path -LiteralPath $RootPath).Path
  $resolvedSource = (Resolve-Path -LiteralPath $SourcePath).Path
  $relative = $resolvedSource.Substring($resolvedRoot.Length).TrimStart('\')
  $targetPath = Join-Path $BackupBase $relative
  $targetParent = Split-Path -Parent $targetPath
  if (-not (Test-Path -LiteralPath $targetParent)) {
    New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
  }
  Copy-Item -LiteralPath $resolvedSource -Destination $targetPath -Force
}

function Get-TargetProjectionFiles {
  param([string]$Root)

  $targets = New-Object System.Collections.Generic.List[string]
  $searchRoots = @(
    (Join-Path $Root "raw\sources"),
    (Join-Path $Root "state\analyses"),
    (Join-Path $Root "state\extracts"),
    (Join-Path $Root "state\manifests"),
    (Join-Path $Root "state\sessions"),
    (Join-Path $Root "wiki\outputs"),
    (Join-Path $Root "wiki\sources")
  )

  foreach ($searchRoot in $searchRoots) {
    if (-not (Test-Path -LiteralPath $searchRoot)) {
      continue
    }

    $files = Get-ChildItem -LiteralPath $searchRoot -File -Recurse
    foreach ($file in $files) {
      $matchesProjection = $file.Name -like "agentcore-memory-projection-*"
      $matchesQueryOutput = $file.Name -like "what-is-stored-in-the-shared-agentcore-vault*" -or
        $file.Name -like "what-is-the-current-agentcore-swarmvault-status*" -or
        $file.Name -like "what-is-the-vault-workspace-root*"

      if ($matchesProjection -or $matchesQueryOutput) {
        if (-not $targets.Contains($file.FullName)) {
          $targets.Add($file.FullName) | Out-Null
        }
      }
    }
  }

  return @($targets)
}

if (-not (Test-Path -LiteralPath $VaultRoot)) {
  throw "Vault root not found: $VaultRoot"
}
if (-not (Test-Path -LiteralPath $StateRoot)) {
  throw "Projection state root not found: $StateRoot"
}
if (-not (Test-Path -LiteralPath $ProjectorScript)) {
  throw "Projector script not found: $ProjectorScript"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupBase = Join-Path $BackupRoot $stamp
$vaultBackup = Join-Path $backupBase "swarmvault"
$stateBackup = Join-Path $backupBase "projection-state"
New-Item -ItemType Directory -Force -Path $vaultBackup, $stateBackup | Out-Null

$targetFiles = Get-TargetProjectionFiles -Root $VaultRoot
foreach ($target in $targetFiles) {
  Copy-FileIntoBackup -SourcePath $target -BackupBase $vaultBackup -RootPath $VaultRoot
}

$entryRoot = Join-Path $StateRoot "entries"
$summaryPath = Join-Path $StateRoot "summary.json"
$stagingRoot = Join-Path $StateRoot "swarmvault-staging"

if (Test-Path -LiteralPath $summaryPath) {
  Copy-FileIntoBackup -SourcePath $summaryPath -BackupBase $stateBackup -RootPath $StateRoot
}

$entryFiles = @(Get-ChildItem -LiteralPath $entryRoot -Filter *.json -ErrorAction Stop)
foreach ($entryFile in $entryFiles) {
  Copy-FileIntoBackup -SourcePath $entryFile.FullName -BackupBase $stateBackup -RootPath $StateRoot
}

if (Test-Path -LiteralPath $stagingRoot) {
  $stagingBackup = Join-Path $stateBackup "swarmvault-staging"
  Copy-Item -LiteralPath $stagingRoot -Destination $stagingBackup -Recurse -Force
}

foreach ($target in $targetFiles) {
  Remove-Item -LiteralPath $target -Force
}

foreach ($entryFile in $entryFiles) {
  $entry = Get-Content -LiteralPath $entryFile.FullName -Raw | ConvertFrom-Json
  $entry.swarmvault.status = "pending"
  $entry.swarmvault.projected_at = $null
  $entry.swarmvault.artifact_path = $null
  $entry.swarmvault.detail = $null
  $entry.updated_at = (Get-Date).ToUniversalTime().ToString("o")
  $entry | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $entryFile.FullName -Encoding utf8
}

$summary = if (Test-Path -LiteralPath $summaryPath) {
  Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
} else {
  [pscustomobject]@{
    version = 1
    updated_at = $null
    checkpoint = [pscustomobject]@{
      created_at = "1970-01-01T00:00:00Z"
      id = "00000000-0000-0000-0000-000000000000"
    }
    totals = [pscustomobject]@{
      projected_rows = 0
      swarmrecall_success = 0
      swarmvault_success = 0
      swarmvault_skipped = 0
      failures = 0
    }
  }
}

$summary.checkpoint.created_at = "1970-01-01T00:00:00Z"
$summary.checkpoint.id = "00000000-0000-0000-0000-000000000000"
$summary.totals.projected_rows = 0
$summary.totals.swarmvault_success = 0
$summary.totals.failures = 0
$summaryTotalsProps = @($summary.totals.PSObject.Properties.Name)
if ($summaryTotalsProps -contains "swarmvault_skipped") {
  $summary.totals.swarmvault_skipped = 0
} else {
  Add-Member -InputObject $summary.totals -NotePropertyName "swarmvault_skipped" -NotePropertyValue 0
}
$summary.updated_at = (Get-Date).ToUniversalTime().ToString("o")
$summary | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $summaryPath -Encoding utf8

if (Test-Path -LiteralPath $stagingRoot) {
  Remove-Item -LiteralPath $stagingRoot -Recurse -Force
}

$projectorOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ProjectorScript -Mode Project -Limit $Limit 2>&1
if ($LASTEXITCODE -ne 0) {
  throw "Projector rebuild failed: $($projectorOutput -join "`n")"
}

[pscustomobject]@{
  ok = $true
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  backup_root = $backupBase
  removed_file_count = $targetFiles.Count
  reset_entry_count = $entryFiles.Count
  projector = ($projectorOutput -join "`n").Trim()
} | ConvertTo-Json -Depth 8
