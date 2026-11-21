param(
  [switch]$Apply,
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [string]$AuditRoot = "E:\AgentCoreArchive\agentcore-memory\audits"
)

$ErrorActionPreference = "Stop"
$library = Join-Path $RepoRoot "ops\AgentCoreSecondaryBackupRetention.ps1"
. $library
$policy = Get-SecondaryBackupPolicy

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$auditDir = Join-Path $AuditRoot (Get-Date -Format "yyyy-MM-dd")
New-Item -ItemType Directory -Path $auditDir -Force | Out-Null

$backupRoot = $policy.secondary_backup_root
$walRoot = $policy.secondary_wal_root
$deleted = New-Object System.Collections.Generic.List[object]
$keptBackups = @()
$keptWalFloor = $null
$errors = New-Object System.Collections.Generic.List[string]

# Volume identity guard: only prune when the volume at the policy drive letter is the
# approved second-copy volume (contracts/secondary-backup-drive-policy.json volume_identity).
$identity = Test-SecondaryVolumeIdentity -DriveLetter $policy.drive_letter
$identityOk = [bool]$identity.match
if (-not $identityOk) {
  Write-Warning ("secondary prune skipped: {0} ({1})" -f $identity.reason, $identity.drive)
}

function Remove-SecondaryPath {
  param([string]$Path, [string]$Kind)
  if (-not (Test-SecondaryDeletePathAllowed -Path $Path)) {
    $errors.Add("refused path outside second-copy roots: $Path") | Out-Null
    return
  }
  $item = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
  $bytes = 0
  if ($item) {
    if ($item.PSIsContainer) {
      $bytes = [int64]((Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum)
    } else {
      $bytes = [int64]$item.Length
    }
  }
  if ($Apply) {
    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
  }
  $deleted.Add([pscustomobject]@{ kind = $Kind; path = $Path; bytes = $bytes }) | Out-Null
}

if ($identityOk -and (Test-Path -LiteralPath $backupRoot)) {
  $sets = @(
    Get-ChildItem -LiteralPath $backupRoot -Directory |
      ForEach-Object { ConvertTo-BackupSetFromDirectory -Directory $_ } |
      Where-Object { $_ }
  )
  if ($sets.Count -gt 0) {
    $plan = Get-SecondaryBackupRetentionPlan -BackupSets $sets -KeepDaily $policy.keep_daily -KeepWeekly $policy.keep_weekly -KeepMonthly $policy.keep_monthly
    $keptBackups = @($plan.RetainNames)
    $keptWalFloor = $plan.WalFloorStamp
    $retainSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($name in $plan.RetainNames) { [void]$retainSet.Add($name) }
    foreach ($set in $sets) {
      if (-not $retainSet.Contains($set.Name)) {
        Remove-SecondaryPath -Path $set.Path -Kind "backup-set"
      }
    }
  }
}

$walDeleted = 0
if ($identityOk -and (Test-Path -LiteralPath $walRoot) -and $keptWalFloor) {
  $walFiles = @(Get-ChildItem -LiteralPath $walRoot -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^[0-9A-F]{24}$' })
  foreach ($wal in $walFiles) {
    if ($wal.LastWriteTime -lt $keptWalFloor.AddHours(-12)) {
      Remove-SecondaryPath -Path $wal.FullName -Kind "wal"
      $walDeleted++
    }
  }
}

$headroom = Get-SecondaryDriveHeadroom -DriveLetter $policy.drive_letter
if (-not $identityOk) {
  $headroom = [pscustomobject]@{
    available = $false
    used_percent = $null
    free_bytes = 0
    within_policy = $false
    reason = "volume identity: $($identity.reason)"
  }
}
$report = [pscustomobject]@{
  ok = ($errors.Count -eq 0)
  apply = [bool]$Apply
  drive_letter = $policy.drive_letter
  volume_identity = $identity
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  kept_backups = $keptBackups
  wal_floor_stamp = if ($keptWalFloor) { $keptWalFloor.ToString("o") } else { $null }
  deleted_count = $deleted.Count
  deleted_bytes = [int64](($deleted | Measure-Object bytes -Sum).Sum)
  wal_deleted = $walDeleted
  errors = @($errors)
  headroom = $headroom
}
$reportPath = Join-Path $auditDir "secondary-prune-$($policy.drive_letter.ToLower())-drive-$stamp.json"
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding utf8
$report | ConvertTo-Json -Depth 6
if ($errors.Count -gt 0) { exit 2 }
if ($Apply -and -not $headroom.within_policy) { exit 3 }
exit 0
