# Shared second-copy (I: AgentCore_Staging, moved from G: 2026-11-17) retention helpers. Dot-source only.
# Policy: contracts/secondary-backup-drive-policy.json

$script:SecondaryBackupPolicyPath = Join-Path (Split-Path -Parent $PSScriptRoot) "contracts\secondary-backup-drive-policy.json"

function Get-SecondaryBackupPolicy {
  $defaults = [pscustomobject]@{
    drive_letter = "I"
    volume_guid = "\\?\Volume{ac27f734-60e4-4783-a6ec-6e9f922ad9d1}\"
    volume_identity_required = $true
    max_used_percent = 75
    min_free_gb = 8
    keep_daily = 7
    keep_weekly = 4
    keep_monthly = 12
    allowed_delete_prefixes = @(
      "I:\AgentCoreArchive\agentcore-memory\backups\pg18",
      "I:\AgentCoreArchive\agentcore-memory\wal\pg18"
    )
    never_delete_prefixes = @(
      "E:\AgentCoreArchive",
      "E:\AgentCore",
      "F:\PostgreSQL18",
      "F:\AgentCore"
    )
    secondary_backup_root = "I:\AgentCoreArchive\agentcore-memory\backups\pg18"
    secondary_wal_root = "I:\AgentCoreArchive\agentcore-memory\wal\pg18"
  }
  if (-not (Test-Path -LiteralPath $script:SecondaryBackupPolicyPath)) {
    return $defaults
  }
  $raw = Get-Content -LiteralPath $script:SecondaryBackupPolicyPath -Raw | ConvertFrom-Json
  $defaults.max_used_percent = [int]$raw.max_used_percent
  $defaults.min_free_gb = [int]$raw.min_free_gb
  if ($raw.retention) {
    $defaults.keep_daily = [int]$raw.retention.keep_daily
    $defaults.keep_weekly = [int]$raw.retention.keep_weekly
    $defaults.keep_monthly = [int]$raw.retention.keep_monthly
  }
  if ($raw.allowed_delete_prefixes) { $defaults.allowed_delete_prefixes = @($raw.allowed_delete_prefixes) }
  if ($raw.never_delete_prefixes) { $defaults.never_delete_prefixes = @($raw.never_delete_prefixes) }
  if ($raw.secondary_backup_root) { $defaults.secondary_backup_root = [string]$raw.secondary_backup_root }
  if ($raw.secondary_wal_root) { $defaults.secondary_wal_root = [string]$raw.secondary_wal_root }
  if ($raw.drive_letter) { $defaults.drive_letter = [string]$raw.drive_letter }
  if ($raw.volume_identity) {
    if ($raw.volume_identity.volume_guid) { $defaults.volume_guid = [string]$raw.volume_identity.volume_guid }
    if ($null -ne $raw.volume_identity.required) { $defaults.volume_identity_required = [bool]$raw.volume_identity.required }
  }
  return $defaults
}

function Get-VolumeGuidForDriveLetter {
  param([Parameter(Mandatory = $true)][string]$DriveLetter)
  $root = $DriveLetter.TrimEnd(":", "\") + ":\"
  try {
    $out = & mountvol.exe $root /L 2>$null
    $guid = (@($out) -join "").Trim()
    if ($LASTEXITCODE -eq 0 -and $guid -like "\\?\Volume{*}\") { return $guid }
  } catch { }
  try {
    $vol = Get-CimInstance -ClassName Win32_Volume -Filter ("DriveLetter='" + $root.TrimEnd("\") + "'") -ErrorAction Stop
    if ($vol -and $vol.DeviceID) { return [string]$vol.DeviceID }
  } catch { }
  return $null
}

function Test-SecondaryVolumeIdentity {
  # Confirms the volume at the policy drive letter is the approved second-copy volume.
  param(
    [string]$DriveLetter,
    [string]$ExpectedVolumeGuid
  )
  $policy = Get-SecondaryBackupPolicy
  if ([string]::IsNullOrWhiteSpace($DriveLetter)) { $DriveLetter = $policy.drive_letter }
  if (-not $PSBoundParameters.ContainsKey("ExpectedVolumeGuid")) { $ExpectedVolumeGuid = $policy.volume_guid }
  $root = $DriveLetter.TrimEnd(":", "\") + ":\"
  if (-not (Test-Path -LiteralPath $root -ErrorAction SilentlyContinue)) {
    return [pscustomobject]@{ match = $false; drive = $root; expected = $ExpectedVolumeGuid; actual = $null; reason = "drive not available" }
  }
  if (-not $policy.volume_identity_required -or [string]::IsNullOrWhiteSpace($ExpectedVolumeGuid)) {
    return [pscustomobject]@{ match = $true; drive = $root; expected = $null; actual = $null; reason = "volume identity guard disabled" }
  }
  $actual = Get-VolumeGuidForDriveLetter -DriveLetter $DriveLetter
  if (-not $actual) {
    return [pscustomobject]@{ match = $false; drive = $root; expected = $ExpectedVolumeGuid; actual = $null; reason = "volume identity unreadable" }
  }
  $ok = [string]::Equals($actual, $ExpectedVolumeGuid, [System.StringComparison]::OrdinalIgnoreCase)
  return [pscustomobject]@{ match = $ok; drive = $root; expected = $ExpectedVolumeGuid; actual = $actual; reason = if ($ok) { "ok" } else { "volume identity mismatch" } }
}

function Get-SecondaryDriveHeadroom {
  param(
    [string]$DriveLetter = "I",
    [long]$AdditionalBytes = 0
  )
  $policy = Get-SecondaryBackupPolicy
  $drive = Get-PSDrive -Name $DriveLetter -ErrorAction SilentlyContinue
  if (-not $drive) {
    return [pscustomobject]@{
      available = $false
      used_percent = $null
      free_bytes = 0
      within_policy = $false
      reason = "drive not available"
    }
  }
  $total = [int64]$drive.Used + [int64]$drive.Free
  $projectedUsed = [int64]$drive.Used + [math]::Max(0, $AdditionalBytes)
  $projectedFree = [int64]$drive.Free - [math]::Max(0, $AdditionalBytes)
  $usedPercent = if ($total -gt 0) { [math]::Round(100.0 * $projectedUsed / $total, 2) } else { 100 }
  $minFree = [int64]$policy.min_free_gb * 1GB
  $within = ($usedPercent -lt [double]$policy.max_used_percent) -and ($projectedFree -ge $minFree)
  $reason = if ($within) { "ok" } elseif ($usedPercent -ge [double]$policy.max_used_percent) { "used percent $($usedPercent) >= $($policy.max_used_percent)" } else { "free bytes $projectedFree < $minFree" }
  return [pscustomobject]@{
    available = $true
    used_percent = $usedPercent
    free_bytes = $projectedFree
    within_policy = $within
    reason = $reason
  }
}

function Get-SecondaryBackupRetentionPlan {
  param(
    [Parameter(Mandatory = $true)]
    [object[]]$BackupSets,
    [int]$KeepDaily = 7,
    [int]$KeepWeekly = 4,
    [int]$KeepMonthly = 12
  )
  $normalized = @(
    foreach ($set in $BackupSets) {
      $name = [string]$set.Name
      $stamp = $set.Stamp
      if (-not $stamp) {
        if ($name -match '^(?<year>\d{4})(?<month>\d{2})(?<day>\d{2})-(?<hour>\d{2})(?<minute>\d{2})(?<second>\d{2})$') {
          $stamp = Get-Date -Year ([int]$Matches.year) -Month ([int]$Matches.month) -Day ([int]$Matches.day) -Hour ([int]$Matches.hour) -Minute ([int]$Matches.minute) -Second ([int]$Matches.second)
        } else {
          continue
        }
      }
      [pscustomobject]@{ Name = $name; Stamp = [datetime]$stamp }
    }
  ) | Sort-Object Stamp

  $byDay = $normalized | Group-Object { $_.Stamp.Date } | ForEach-Object { $_.Group | Sort-Object Stamp | Select-Object -Last 1 }
  $daily = @($byDay | Sort-Object Stamp -Descending | Select-Object -First $KeepDaily)

  $calendar = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
  $byWeek = $normalized | Group-Object {
    $week = $calendar.GetWeekOfYear($_.Stamp, [System.Globalization.CalendarWeekRule]::FirstFourDayWeek, [DayOfWeek]::Monday)
    '{0:D4}-W{1:D2}' -f $_.Stamp.Year, $week
  } | ForEach-Object { $_.Group | Sort-Object Stamp | Select-Object -Last 1 }
  $weekly = @($byWeek | Sort-Object Stamp -Descending | Select-Object -First $KeepWeekly)

  $byMonth = $normalized | Group-Object { '{0:yyyy-MM}' -f $_.Stamp } | ForEach-Object { $_.Group | Sort-Object Stamp | Select-Object -Last 1 }
  $monthly = @($byMonth | Sort-Object Stamp -Descending | Select-Object -First $KeepMonthly)

  $retain = @($daily + $weekly + $monthly | Sort-Object Name -Unique)
  $oldestDaily = $daily | Sort-Object Stamp | Select-Object -First 1
  return [pscustomobject]@{
    RetainNames = @($retain.Name)
    DailyNames = @($daily.Name)
    WeeklyNames = @($weekly.Name)
    MonthlyNames = @($monthly.Name)
    WalFloorBackupName = if ($oldestDaily) { [string]$oldestDaily.Name } else { $null }
    WalFloorStamp = if ($oldestDaily) { $oldestDaily.Stamp } else { $null }
  }
}

function Get-WalNamesBelowFloor {
  param(
    [string[]]$WalFileNames,
    [string]$FloorWalName
  )
  if ([string]::IsNullOrWhiteSpace($FloorWalName)) { return @() }
  return @(
    $WalFileNames |
      Where-Object { $_ -and ($_ -lt $FloorWalName) }
  )
}

function Test-SecondaryDeletePathAllowed {
  param([Parameter(Mandatory = $true)][string]$Path)
  $policy = Get-SecondaryBackupPolicy
  $full = [string]$Path
  foreach ($denied in $policy.never_delete_prefixes) {
    if ($full.StartsWith($denied, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $false
    }
  }
  foreach ($allowed in $policy.allowed_delete_prefixes) {
    if ($full.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }
  return $false
}

function ConvertTo-BackupSetFromDirectory {
  param([System.IO.DirectoryInfo]$Directory)
  if ($Directory.Name -notmatch '^(?<year>\d{4})(?<month>\d{2})(?<day>\d{2})-(?<hour>\d{2})(?<minute>\d{2})(?<second>\d{2})$') {
    return $null
  }
  $stamp = Get-Date -Year ([int]$Matches.year) -Month ([int]$Matches.month) -Day ([int]$Matches.day) -Hour ([int]$Matches.hour) -Minute ([int]$Matches.minute) -Second ([int]$Matches.second)
  return [pscustomobject]@{ Name = $Directory.Name; Stamp = $stamp; Path = $Directory.FullName }
}
