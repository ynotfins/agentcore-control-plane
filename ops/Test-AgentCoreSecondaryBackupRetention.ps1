param(
  [string]$RepoRoot = "D:\github\agentcore-control-plane"
)

$ErrorActionPreference = "Stop"

function Add-Result {
  param(
    [System.Collections.Generic.List[object]]$Results,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail
  )
  $Results.Add([pscustomobject]@{
    name = $Name
    passed = $Passed
    detail = $Detail
  }) | Out-Null
}

$results = [System.Collections.Generic.List[object]]::new()
$ops = Join-Path $RepoRoot "ops"
$library = Join-Path $ops "AgentCoreSecondaryBackupRetention.ps1"
$archiveScript = Join-Path $ops "Archive-AgentCoreWal.ps1"
$policy = Join-Path $RepoRoot "contracts\secondary-backup-drive-policy.json"

Add-Result $results "library exists" (Test-Path -LiteralPath $library) $library
Add-Result $results "archive script exists" (Test-Path -LiteralPath $archiveScript) $archiveScript
Add-Result $results "policy contract exists" (Test-Path -LiteralPath $policy) $policy

if (Test-Path -LiteralPath $library) {
  . $library

  $sets = @(
    [pscustomobject]@{ Name = "20260901-030001"; Stamp = [datetime]"2026-09-01 03:00:01" },
    [pscustomobject]@{ Name = "20260908-030001"; Stamp = [datetime]"2026-09-08 03:00:01" },
    [pscustomobject]@{ Name = "20260915-030001"; Stamp = [datetime]"2026-09-15 03:00:01" },
    [pscustomobject]@{ Name = "20260922-030001"; Stamp = [datetime]"2026-09-22 03:00:01" },
    [pscustomobject]@{ Name = "20260923-030001"; Stamp = [datetime]"2026-09-23 03:00:01" },
    [pscustomobject]@{ Name = "20260924-030001"; Stamp = [datetime]"2026-09-24 03:00:01" },
    [pscustomobject]@{ Name = "20260925-030001"; Stamp = [datetime]"2026-09-25 03:00:01" },
    [pscustomobject]@{ Name = "20260926-030001"; Stamp = [datetime]"2026-09-26 03:00:01" },
    [pscustomobject]@{ Name = "20260927-030001"; Stamp = [datetime]"2026-09-27 03:00:01" },
    [pscustomobject]@{ Name = "20260928-030001"; Stamp = [datetime]"2026-09-28 03:00:01" },
    [pscustomobject]@{ Name = "20260929-030001"; Stamp = [datetime]"2026-09-29 03:00:01" }
  )
  $plan = Get-SecondaryBackupRetentionPlan -BackupSets $sets -KeepDaily 7 -KeepWeekly 4 -KeepMonthly 12
  $kept = @($plan.RetainNames | Sort-Object)
  $dailyKept = @($plan.DailyNames | Sort-Object)
  Add-Result $results "keeps last 7 daily names" (
    ($dailyKept -join ",") -eq "20260923-030001,20260924-030001,20260925-030001,20260926-030001,20260927-030001,20260928-030001,20260929-030001"
  ) ($dailyKept -join ",")
  Add-Result $results "oldest daily is WAL floor source" (
    $plan.WalFloorBackupName -eq "20260923-030001"
  ) ([string]$plan.WalFloorBackupName)
  Add-Result $results "retains weekly samples from recent weeks" (
    ($kept -contains "20260908-030001") -and
    ($kept -contains "20260915-030001") -and
    -not ($kept -contains "20260901-030001")
  ) ($kept -join ",")

  $walNames = @(
    "000000010000000600000042",
    "000000010000000A00000001",
    "000000010000002100000010",
    "000000010000002100000089"
  )
  $below = @(Get-WalNamesBelowFloor -WalFileNames $walNames -FloorWalName "000000010000002100000010")
  Add-Result $results "WAL floor deletes only earlier segments" (
    ($below -contains "000000010000000600000042") -and
    ($below -contains "000000010000000A00000001") -and
    -not ($below -contains "000000010000002100000010") -and
    -not ($below -contains "000000010000002100000089")
  ) ($below -join ",")

  Add-Result $results "allowed delete roots stay on I: second copy" (
    (Test-SecondaryDeletePathAllowed -Path "I:\AgentCoreArchive\agentcore-memory\wal\pg18\000000010000000600000042") -and
    (Test-SecondaryDeletePathAllowed -Path "I:\AgentCoreArchive\agentcore-memory\backups\pg18\20260901-030001") -and
    -not (Test-SecondaryDeletePathAllowed -Path "G:\AgentCoreArchive\agentcore-memory\wal\pg18\000000010000000600000042") -and
    -not (Test-SecondaryDeletePathAllowed -Path "I:\LocalApps\ZCode\anything") -and
    -not (Test-SecondaryDeletePathAllowed -Path "E:\AgentCoreArchive\agentcore-memory\wal\pg18\000000010000000600000042") -and
    -not (Test-SecondaryDeletePathAllowed -Path "F:\PostgreSQL18\data\pg_wal\000000010000000600000042")
  ) "I: second-copy roots allowed; G:/E:/F:/other I: paths denied"

  $pol = Get-SecondaryBackupPolicy
  Add-Result $results "policy pins I: volume identity" (
    $pol.drive_letter -eq "I" -and $pol.volume_identity_required -and $pol.volume_guid -like "\\?\Volume{*}\"
  ) "drive=$($pol.drive_letter) guid=$($pol.volume_guid)"

  $realId = Test-SecondaryVolumeIdentity -DriveLetter $pol.drive_letter
  Add-Result $results "live I: volume matches pinned identity" ([bool]$realId.match) "reason=$($realId.reason) actual=$($realId.actual)"

  $fakeId = Test-SecondaryVolumeIdentity -DriveLetter $pol.drive_letter -ExpectedVolumeGuid "\\?\Volume{00000000-0000-0000-0000-000000000000}\"
  Add-Result $results "mismatched volume identity is refused" (-not $fakeId.match -and $fakeId.reason -eq "volume identity mismatch") "reason=$($fakeId.reason)"
}

if (Test-Path -LiteralPath $archiveScript) {
  $fixture = Join-Path $env:TEMP ("ac-wal-secondary-" + [guid]::NewGuid().ToString("N"))
  $primary = Join-Path $fixture "primary"
  $secondary = Join-Path $fixture "secondary"
  $sourceDir = Join-Path $fixture "source"
  New-Item -ItemType Directory -Path $primary, $sourceDir -Force | Out-Null
  Set-Content -LiteralPath $secondary -Value "not-a-directory" -Encoding utf8
  $walName = "00000001000000210000008A"
  $source = Join-Path $sourceDir $walName
  Set-Content -LiteralPath $source -Value "wal-bytes" -Encoding utf8
  $logRoot = Join-Path $fixture "logs"
  $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $archiveScript `
    -SourcePath $source `
    -WalFileName $walName `
    -ArchiveRoot $primary `
    -SecondaryArchiveRoot $secondary `
    -LogRoot $logRoot 2>&1
  $code = $LASTEXITCODE
  $primaryCopy = Test-Path -LiteralPath (Join-Path $primary $walName)
  Add-Result $results "archive_command survives broken secondary copy" (
    $code -eq 0 -and $primaryCopy
  ) "exit=$code primary=$primaryCopy output=$($output -join ' | ')"

  # Guard tests run entirely inside the TEMP fixture; never the real archive roots.
  $fixtureRoot = [System.IO.Path]::GetPathRoot($fixture)
  $fixtureGuid = Get-VolumeGuidForDriveLetter -DriveLetter $fixtureRoot.Substring(0, 1)
  $secondaryOk = Join-Path $fixture "secondary-match"
  $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $archiveScript `
    -SourcePath $source -WalFileName $walName -ArchiveRoot $primary `
    -SecondaryArchiveRoot $secondaryOk -SecondaryVolumeGuid $fixtureGuid -LogRoot $logRoot 2>&1
  $code = $LASTEXITCODE
  Add-Result $results "secondary copy written when volume identity matches" (
    $code -eq 0 -and (Test-Path -LiteralPath (Join-Path $secondaryOk $walName))
  ) "exit=$code guid=$fixtureGuid"

  $secondaryBad = Join-Path $fixture "secondary-mismatch"
  $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $archiveScript `
    -SourcePath $source -WalFileName $walName -ArchiveRoot $primary `
    -SecondaryArchiveRoot $secondaryBad -SecondaryVolumeGuid "\\?\Volume{00000000-0000-0000-0000-000000000000}\" -LogRoot $logRoot 2>&1
  $code = $LASTEXITCODE
  $logTail = @(Get-Content -LiteralPath (Join-Path $logRoot "archive.log") -ErrorAction SilentlyContinue | Select-Object -Last 2) -join " | "
  Add-Result $results "mismatched volume skips copy, creates no folder, exit 0" (
    $code -eq 0 -and -not (Test-Path -LiteralPath $secondaryBad) -and $logTail -match "identity mismatch"
  ) "exit=$code folder=$(Test-Path -LiteralPath $secondaryBad) log=$logTail"

  Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue
}

$failed = @($results | Where-Object { -not $_.passed })
$results | ForEach-Object {
  $mark = if ($_.passed) { "PASS" } else { "FAIL" }
  Write-Host ("[{0}] {1} - {2}" -f $mark, $_.name, $_.detail)
}
if ($failed.Count -gt 0) {
  Write-Host ("FAILED {0}/{1}" -f $failed.Count, $results.Count)
  exit 1
}
Write-Host ("PASSED {0}/{1}" -f $results.Count, $results.Count)
exit 0
