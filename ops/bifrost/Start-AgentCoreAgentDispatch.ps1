# Direct-launch only. Do not register or start a Windows scheduled task or service.
# Authority: governance/proposals/2026-11-19-agent-dispatch.md
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'I:\LocalApps\AgentDispatch',
  [int]$Port = 18092,
  [string]$PythonExe = 'D:\github\agentcore-control-plane\scripts\.venv\Scripts\pythonw.exe',
  [switch]$ProbeOnly,
  [switch]$Stop
)
$ErrorActionPreference = 'Stop'
$HostAddress = '127.0.0.1'
$pidFile = Join-Path $RuntimeRoot 'agent-dispatch.pid'

function Test-DispatchReady {
  try {
    $body = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
    $r = Invoke-RestMethod -Uri ("http://{0}:{1}/mcp" -f $HostAddress, $Port) -Method POST -ContentType 'application/json' -Body $body -TimeoutSec 10
    return ($r.result.tools.Count -eq 6)
  } catch { return $false }
}

if ($Stop) {
  if (Test-Path $pidFile) {
    $procId = [int](Get-Content $pidFile -Raw)
    $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($p -and $p.Path -eq $PythonExe) { Stop-Process -Id $procId -Force; Write-Host "[Stop] agent-dispatch pid $procId stopped" }
    Remove-Item $pidFile -Force
  } else { Write-Host '[Stop] no pid file; nothing to stop' }
  exit 0
}
if ($ProbeOnly) {
  if (-not (Test-DispatchReady)) { throw "agent-dispatch not ready on ${HostAddress}:$Port" }
  Write-Host "[Probe] agent-dispatch ready on ${HostAddress}:$Port (6 tools)"; exit 0
}
if (Test-DispatchReady) { Write-Host "[Start] agent-dispatch already ready on ${HostAddress}:$Port"; exit 0 }

New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot 'logs'), (Join-Path $RuntimeRoot 'jobs') | Out-Null
$server = Join-Path $RepoRoot 'scripts\agent_dispatch\server.py'
if (-not (Test-Path $server)) { throw "server not found: $server" }
$env:AGENTCORE_DISPATCH_ROOT = $RuntimeRoot

# Model credentials come from the User environment. The watchdog/scheduled launch
# does not inherit them, so pass them explicitly or every backend returns 401.
foreach ($name in @('OMNIROUTE_API_KEY','OPENROUTER_API_KEY')) {
  if (-not [Environment]::GetEnvironmentVariable($name, 'Process')) {
    $value = [Environment]::GetEnvironmentVariable($name, 'User')
    if ($value) { Set-Item -Path ("env:{0}" -f $name) -Value $value }
  }
}
$p = Start-Process -FilePath $PythonExe -ArgumentList @('-u', $server, '--host', $HostAddress, '--port', [string]$Port) `
  -WorkingDirectory $RuntimeRoot -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput (Join-Path $RuntimeRoot 'logs\agent-dispatch.stdout.log') `
  -RedirectStandardError (Join-Path $RuntimeRoot 'logs\agent-dispatch.stderr.log')
Set-Content -Path $pidFile -Value $p.Id -Encoding ascii
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 1
  if (Test-DispatchReady) { Write-Host "[Start] agent-dispatch ready on ${HostAddress}:$Port (pid $($p.Id)); no scheduled task created"; exit 0 }
}
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
throw "agent-dispatch did not become ready on ${HostAddress}:$Port"
