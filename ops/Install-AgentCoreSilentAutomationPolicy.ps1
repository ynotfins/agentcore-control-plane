#Requires -Version 5.1
<#
.SYNOPSIS
  One-shot operator hardening: backup task XML, force Hidden pwsh, disable legacy flashers.

.DESCRIPTION
  Run this from Windows PowerShell / Terminal **outside Cursor** when Stage B blocks
  scheduled-task mutations from the IDE agent. Keeps NFA/OmniRoute watchdogs enabled but silent.
  Also patches the NFA public-edge installer so reinstall cannot recreate a visible console.
#>
[CmdletBinding()]
param(
  [string]$BackupRoot = '',
  # Optional: Tailscale Funnel for /mcp only (fallback if Cloudflare unavailable). Canonical Grok cloud is Cloudflare https://agentcore-grokbot.4axe.com/mcp with x-bf-vk.
  [switch]$EnableGrokFunnel,
  # Start dedicated Cloudflare connector for agentcore-grokbot tunnel (does not touch cloud-mia).
  [switch]$EnableGrokbotCloudflareTunnel
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AgentCoreSilentAutomation.Common.ps1')
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (-not $BackupRoot) {
  $BackupRoot = "E:\AgentCore-Backups\silent-automation-$stamp"
}
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

function Backup-TaskXml {
  param(
    [Parameter(Mandatory)][string]$TaskName,
    [string]$TaskPath = '\'
  )
  $xml = Export-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
  if ($xml) {
    $safe = (($TaskPath.Trim('\') + '-' + $TaskName) -replace '[\\/:*?]', '-')
    $xml | Out-File -FilePath (Join-Path $BackupRoot "$safe.xml") -Encoding utf8
  }
}

function Set-SilentPwshTask {
  param(
    [string]$TaskName,
    [string]$FilePath,
    [string]$ExtraArgs = '',
    [string]$TaskPath = '',
    [switch]$PreserveFileArgs
  )
  $t = $null
  if (-not [string]::IsNullOrWhiteSpace($TaskPath)) {
    $t = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
  } else {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  }
  if (-not $t) {
    Write-Host "MISSING $TaskName"
    return
  }
  if (-not $PreserveFileArgs -and -not (Test-Path -LiteralPath $FilePath)) {
    Write-Host "SKIP_NO_SCRIPT $TaskName -> $FilePath"
    return
  }
  $resolvedPath = if ([string]::IsNullOrWhiteSpace($t.TaskPath)) { '\' } else { $t.TaskPath }
  Backup-TaskXml -TaskName $TaskName -TaskPath $resolvedPath
  try {
    if ($PreserveFileArgs) {
      Set-AgentCoreSilentConhostTask -TaskName $TaskName -TaskPath $resolvedPath -PreserveFileArgs
    } else {
      Set-AgentCoreSilentConhostTask -TaskName $TaskName -TaskPath $resolvedPath -FilePath $FilePath -ExtraArgs $ExtraArgs
    }
    Write-Host "SILENT $TaskName ($resolvedPath)"
  } catch {
    Write-Host "ACCESS_DENIED_OR_FAIL $TaskName ($resolvedPath): $($_.Exception.Message)" -ForegroundColor Yellow
  }
}

function Set-SilentOpenClawTask {
  param([Parameter(Mandatory)][string]$TaskName)
  $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if (-not $t) { Write-Host "MISSING $TaskName"; return }
  $tp = if ([string]::IsNullOrWhiteSpace($t.TaskPath)) { '\' } else { $t.TaskPath }
  Backup-TaskXml -TaskName $TaskName -TaskPath $tp
  try {
    Set-AgentCoreSilentConhostTask -TaskName $TaskName -TaskPath $tp -PreserveFileArgs
    Write-Host "SILENT $TaskName ($tp)"
  } catch {
    Write-Host "ACCESS_DENIED_OR_FAIL $TaskName ($tp): $($_.Exception.Message)" -ForegroundColor Yellow
  }
}

function Invoke-GrokbotCloudflareTunnel {
  Write-Host 'Activating Codex-provisioned Cloudflare tunnel agentcore-grokbot (separate from cloud-mia)...'
  $cf = 'C:\Tools\cloudflared\cloudflared.exe'
  if (-not (Test-Path -LiteralPath $cf)) { throw "cloudflared missing: $cf" }

  $existing = [Environment]::GetEnvironmentVariable('AGENTCORE_GROKBOT_CLOUDFLARE_TUNNEL_TOKEN', 'User')
  if ([string]::IsNullOrWhiteSpace($existing)) {
    Write-Host 'Fetching tunnel token into User env (value not printed)...'
    $token = (& $cf tunnel token agentcore-grokbot 2>$null | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($token) -or $token.Length -lt 20) {
      throw 'cloudflared tunnel token agentcore-grokbot returned empty/short token. Confirm cloudflared is logged in (cert.pem) and tunnel exists.'
    }
    [Environment]::SetEnvironmentVariable('AGENTCORE_GROKBOT_CLOUDFLARE_TUNNEL_TOKEN', $token, 'User')
    Write-Host ("TOKEN_STORED len={0}" -f $token.Length)
    $token = $null
  } else {
    Write-Host ("TOKEN_ALREADY_PRESENT len={0}" -f $existing.Length)
  }
  $existing = $null

  $launcherDir = 'I:\LocalApps\AgentCore\cloudflared-grokbot'
  New-Item -ItemType Directory -Force -Path $launcherDir | Out-Null
  $launcher = Join-Path $launcherDir 'Start-AgentCoreGrokbotTunnel.ps1'
  @'
#Requires -Version 5.1
# Starts the dedicated agentcore-grokbot Cloudflare connector.
# Token comes from User env only — never pass token on the command line.
$ErrorActionPreference = 'Stop'
$cf = 'C:\Tools\cloudflared\cloudflared.exe'
$token = [Environment]::GetEnvironmentVariable('AGENTCORE_GROKBOT_CLOUDFLARE_TUNNEL_TOKEN', 'User')
if ([string]::IsNullOrWhiteSpace($token)) { throw 'Missing User env AGENTCORE_GROKBOT_CLOUDFLARE_TUNNEL_TOKEN' }
$env:TUNNEL_TOKEN = $token
$token = $null
& $cf tunnel --no-autoupdate run
'@ | Set-Content -LiteralPath $launcher -Encoding UTF8
  Write-Host "LAUNCHER $launcher"

  # Register under \ (not \AgentCore\) so a normal user can own it without Admin.
  $taskName = 'AgentCore-Grokbot-Cloudflare-Tunnel'
  $taskPath = '\'
  $pwsh = 'C:\Program Files\PowerShell\7\pwsh.exe'
  if (-not (Test-Path -LiteralPath $pwsh)) { $pwsh = (Get-Command pwsh).Source }
  $arg = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$launcher`""
  $action = New-ScheduledTaskAction -Execute (Get-AgentCoreConhostPath) -Argument (New-AgentCoreSilentConhostArgument -PwshPath (Get-AgentCorePwshPath) -PwshArgumentTail (New-AgentCoreSilentPwshFileArguments -FilePath $launcher))
  $settings = New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

  $taskOk = $false
  try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    $taskOk = $true
    Write-Host "TASK_REGISTERED $taskName"
  } catch {
    Write-Host "TASK_REGISTER_FAIL: $($_.Exception.Message)" -ForegroundColor Yellow
  }

  # Always start the connector process now (even if task registration failed).
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.Name -eq 'cloudflared.exe' -and $_.CommandLine -match 'TUNNEL_TOKEN|no-autoupdate run' } |
    ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }

  if ($taskOk) {
    try { Start-ScheduledTask -TaskName $taskName } catch { Write-Host "TASK_START_FAIL: $($_.Exception.Message)" -ForegroundColor Yellow }
  }

  # Direct start fallback (Hidden window) — ensures connector comes up this session.
  $startInfo = @{
    FilePath = $pwsh
    ArgumentList = @('-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass', '-File', $launcher)
    WindowStyle = 'Hidden'
    PassThru = $true
  }
  $proc = Start-Process @startInfo
  Write-Host "CONNECTOR_PID $($proc.Id)"

  Start-Sleep -Seconds 5
  & $cf tunnel info agentcore-grokbot 2>&1 | Select-Object -First 25 | ForEach-Object { Write-Host $_ }

  Write-Host 'Probing public URL (expect 401 without Bearer)...'
  try {
    $resp = Invoke-WebRequest -Uri 'https://agentcore-grokbot.4axe.com/mcp' -Method GET -UseBasicParsing -TimeoutSec 20
    Write-Host ("PROBE status={0} (unexpected success without auth)" -f [int]$resp.StatusCode)
  } catch {
    $code = $null
    try { $code = [int]$_.Exception.Response.StatusCode } catch {}
    if ($code -eq 401 -or $code -eq 403) {
      Write-Host "PROBE OK status=$code (connector up; auth required)"
    } elseif ($code) {
      Write-Host "PROBE status=$code msg=$($_.Exception.Message)"
    } else {
      Write-Host "PROBE FAIL $($_.Exception.Message)"
    }
  }

  Write-Host ''
  Write-Host 'Grok Bot connector settings:'
  Write-Host '  Name: agentcore-gateway'
  Write-Host '  Type: Remote HTTPS'
  Write-Host '  Server URL: https://agentcore-grokbot.4axe.com/mcp'
  Write-Host '  Header Key: x-bf-vk'
  Write-Host '  Header Value: <paste raw BIFROST_MCP_VK_GROKBOT sk-bf- value — no Bearer prefix>'
  Write-Host '  Client ID: leave empty'
  Write-Host '  Do NOT click Connect (OAuth).'
  Write-Host '  Task: \AgentCore-Grokbot-Cloudflare-Tunnel (Hidden; do not recreate routinely)'
  Write-Host '  Proof log: F:\AgentCore\runtime\bifrost\logs\bifrost-gateway.stdout.log'
}

# Cloudflare first when requested — do not block on AgentCore task Access Denied.
if ($EnableGrokbotCloudflareTunnel) {
  Invoke-GrokbotCloudflareTunnel
}

$policy = Get-AgentCoreSilentPolicyContract
$map = [ordered]@{}
foreach ($entry in @($policy.tasks)) {
  if ($entry.file) {
    $map[$entry.task_name] = @{ File = ([string]$entry.file) -replace '/', '\'; Extra = [string]$entry.extra_args; TaskPath = [string]$entry.task_path; Preserve = [bool]$entry.repair.preserve_file_args }
  }
}

# When only activating the Grokbot tunnel, skip AgentCore task hardening (often Access Denied without Admin).
$cloudflareOnly = $EnableGrokbotCloudflareTunnel -and -not $EnableGrokFunnel
if (-not $cloudflareOnly) {
  foreach ($name in $map.Keys) {
    $row = $map[$name]
    if ($row.Preserve) {
      Set-SilentPwshTask -TaskName $name -TaskPath $row.TaskPath -PreserveFileArgs
    } else {
      Set-SilentPwshTask -TaskName $name -FilePath $row.File -ExtraArgs $row.Extra -TaskPath $row.TaskPath
    }
  }

  foreach ($ocName in @('OpenClaw Gateway', 'OpenClaw Voice Assistant')) {
    Set-SilentOpenClawTask -TaskName $ocName
  }

  $dd = Get-ScheduledTask -TaskName 'DailyDriftCheck' -ErrorAction SilentlyContinue
  if ($dd) {
    $ddPath = if ([string]::IsNullOrWhiteSpace($dd.TaskPath)) { '\' } else { $dd.TaskPath }
    Backup-TaskXml -TaskName 'DailyDriftCheck' -TaskPath $ddPath
    try {
      Disable-ScheduledTask -TaskName 'DailyDriftCheck' -TaskPath $ddPath | Out-Null
      Write-Host "DISABLED DailyDriftCheck ($ddPath)"
    } catch {
      Write-Host "ACCESS_DENIED_OR_FAIL DailyDriftCheck: $($_.Exception.Message)" -ForegroundColor Yellow
    }
  }
} else {
  Write-Host 'SKIP silent hardening (Cloudflare-tunnel-only run). Re-run without -EnableGrokbotCloudflareTunnel, elevated, to harden AgentCore tasks.'
}

$swarm = 'C:\Users\ynotf\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Swarm Stack.cmd'
$swarmDisabled = $swarm + '.disabled-silent-automation'
if (Test-Path -LiteralPath $swarmDisabled) {
  Rename-Item -LiteralPath $swarmDisabled -NewName 'Swarm Stack.cmd' -Force
  Write-Host 'RESTORED Swarm Startup (required for SwarmClaw; do not disable)'
} elseif (Test-Path -LiteralPath $swarm) {
  Write-Host 'KEEP Swarm Startup (required for SwarmClaw; do not disable)'
} else {
  Write-Host 'Swarm Startup absent — leave for Swarm ecosystem owner; do not invent a replacement here'
}

# Anti-regression: NFA installer must recreate Hidden, not visible powershell.exe
$nfaInstaller = 'D:\agentcore-worktrees\nfa-platform\goal-public-edge-watchdog\scripts\windows-service\install_public_edge_watchdog.ps1'
if (Test-Path -LiteralPath $nfaInstaller) {
  Copy-Item -LiteralPath $nfaInstaller -Destination (Join-Path $BackupRoot 'install_public_edge_watchdog.ps1.bak') -Force
  $lines = Get-Content -LiteralPath $nfaInstaller
  $joined = $lines -join "`n"
  if ($joined -match 'WindowStyle Hidden' -and $joined -match 'New-ScheduledTaskSettingsSet -Hidden') {
    Write-Host 'NFA installer already Hidden'
  } else {
    $out = New-Object System.Collections.Generic.List[string]
    $actionReplaced = $false
    foreach ($line in $lines) {
      if (-not $actionReplaced -and $line -match "New-ScheduledTaskAction -Execute 'powershell\.exe'") {
        $out.Add('$pwsh = Join-Path $env:ProgramFiles ''PowerShell\7\pwsh.exe''')
        $out.Add('if (-not (Test-Path -LiteralPath $pwsh)) { $pwsh = ''powershell.exe'' }')
        $out.Add('$action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`" -Once"')
        $actionReplaced = $true
        continue
      }
      if ($line -match 'New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries' -and $line -notmatch '-Hidden') {
        $out.Add(($line -replace 'New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries', 'New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries'))
        continue
      }
      $out.Add($line)
    }
    Set-Content -LiteralPath $nfaInstaller -Value $out -Encoding UTF8
    Write-Host 'PATCHED NFA install_public_edge_watchdog.ps1'
  }
} else {
  Write-Host "SKIP NFA installer missing: $nfaInstaller"
}

# Dual Multi-Workspaces shortcut
$wsDir = 'D:\agentcore-worktrees\workspaces'
New-Item -ItemType Directory -Force -Path $wsDir | Out-Null
$wsPath = Join-Path $wsDir 'agentcore-dual-control-planes.code-workspace'
@'
{
  "folders": [
    { "path": "D:/github/agentcore-control-plane", "name": "agentcore-control-plane" },
    { "path": "D:/postgreSQL18-control-plane", "name": "postgreSQL18-control-plane" }
  ],
  "settings": {}
}
'@ | Set-Content -Path $wsPath -Encoding UTF8
$lnkDir = 'D:\Multi-Workspaces'
New-Item -ItemType Directory -Force -Path $lnkDir | Out-Null
$lnkPath = Join-Path $lnkDir 'AgentCore Dual Control Planes (2 projects).lnk'
$sh = New-Object -ComObject WScript.Shell
$lnk = $sh.CreateShortcut($lnkPath)
$lnk.TargetPath = 'C:\Users\ynotf\AppData\Local\Programs\cursor\Cursor.exe'
$lnk.Arguments = "`"$wsPath`""
$lnk.WorkingDirectory = $wsDir
$lnk.Save()
Write-Host "WS=$wsPath"
Write-Host "LNK=$lnkPath"

Write-Host "BACKUP $BackupRoot"

if ($EnableGrokFunnel) {
  Write-Host 'Enabling Tailscale Funnel for /mcp only (not / or /v1/ingest)...'
  & tailscale funnel --bg /mcp http://127.0.0.1:8080/mcp
  if ($LASTEXITCODE -ne 0) {
    Write-Host 'Funnel enable failed. Enable Funnel for this node in Tailscale admin, then retry.' -ForegroundColor Red
  } else {
    Write-Host 'Funnel OK (FALLBACK ONLY). Canonical Grok cloud remains https://agentcore-grokbot.4axe.com/mcp with x-bf-vk. Funnel alternate URL if needed: https://chaoscentral.tailb71e7e.ts.net/mcp'
    & tailscale funnel status
  }
}

# Cloudflare tunnel already ran at top when -EnableGrokbotCloudflareTunnel was set.

if (-not $cloudflareOnly) {
  $validator = Join-Path $PSScriptRoot 'bifrost\Test-AgentCoreSilentAutomationTasks.ps1'
  if (-not (Test-Path -LiteralPath $validator)) {
    $validator = Join-Path $PSScriptRoot 'Test-AgentCoreSilentAutomationTasks.ps1'
  }
  & $validator
  exit $LASTEXITCODE
}

Write-Host 'Cloudflare-tunnel-only run complete (validator skipped).'
exit 0
