param(
  [string]$TaskPath = "\AgentCore\",
  [string]$ConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json",
  [switch]$StartAfterInstall
)

$ErrorActionPreference = "Stop"

$repoOps = Split-Path -Parent $PSCommandPath
$starter = Join-Path $repoOps "Start-AgentCoreSwarmRecallComponent.ps1"
$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $starter)) {
  throw "SwarmRecall component starter not found: $starter"
}

function Register-AgentCoreComponentTask {
  param(
    [string]$Name,
    [string]$Component
  )

  $argument = @(
    "-NoProfile",
    "-ExecutionPolicy Bypass",
    "-File `"$starter`"",
    "-Component $Component",
    "-ConfigPath `"$ConfigPath`""
  ) -join " "

  $workingDirectory = if ($Component -eq "Meilisearch") {
    Split-Path -Parent $config.search.binaryPath
  } else {
    $config.source.repoRoot
  }

  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument -WorkingDirectory $workingDirectory
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal

  Register-ScheduledTask -TaskPath $TaskPath -TaskName $Name -InputObject $task -Force | Out-Null
  Write-Host "Registered $TaskPath$Name for $Component."

  if ($StartAfterInstall) {
    Start-ScheduledTask -TaskPath $TaskPath -TaskName $Name
  }
}

Register-AgentCoreComponentTask -Name "SwarmRecallMeilisearch" -Component "Meilisearch"
Register-AgentCoreComponentTask -Name "SwarmRecallApi" -Component "Api"

Get-ScheduledTask -TaskPath $TaskPath |
  Where-Object { $_.TaskName -in @("SwarmRecallMeilisearch", "SwarmRecallApi") } |
  Select-Object TaskPath, TaskName, State
