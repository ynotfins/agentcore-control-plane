param(
  [string]$TaskPath = "\AgentCore\",
  [string]$TaskName = "KnowledgeCorpusSync",
  [string]$At = "4:30am",
  [string]$RepoRoot = "D:\agentcore-worktrees\agentcore-control-plane\main"
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $RepoRoot "ops\Invoke-AgentCoreKnowledgeCorpusSync.ps1"
if (-not (Test-Path -LiteralPath $scriptPath)) {
  throw "Sync script missing: $scriptPath"
}

$backupRoot = "E:\AgentCoreArchive\backups_cold\scheduled-tasks"
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
try {
  $xml = Export-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName
  $xml | Set-Content -LiteralPath (Join-Path $backupRoot "$TaskName-$(Get-Date -Format yyyyMMdd-HHmmss).xml") -Encoding utf8
} catch {
}

$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`" -Apply" `
  -WorkingDirectory $RepoRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -Hidden `
  -MultipleInstances IgnoreNew `
  -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
Register-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -InputObject $task -Force | Out-Null

$info = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName
[pscustomobject]@{
  ok = $true
  task = "$TaskPath$TaskName"
  state = [string]$info.State
  hidden = [bool]$info.Settings.Hidden
  at = $At
  apply = $true
  repo = $RepoRoot
} | ConvertTo-Json
