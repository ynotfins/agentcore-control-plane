<#
.SYNOPSIS
  Launch Bifrost with full Windows User environment inheritance.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

# Copy all User env vars into process (Bifrost stdio children inherit selected names).
[Environment]::GetEnvironmentVariables('User').GetEnumerator() | ForEach-Object {
  Set-Item -Path ("Env:{0}" -f $_.Key) -Value ([string]$_.Value) -Force
}
$env:CURSOR_API_URL = if ($env:CURSOR_API_URL) { $env:CURSOR_API_URL } else { 'https://api.cursor.com' }
$env:DISABLE_THOUGHT_LOGGING = 'true'
# Bifrost requires listed STDIO env vars to exist; provide HOME for Unix-oriented MCP servers.
if (-not $env:HOME) { $env:HOME = $env:USERPROFILE }
if (-not $env:OBSIDIAN_BASE_URL) { $env:OBSIDIAN_BASE_URL = 'https://127.0.0.1:27124' }
if (-not $env:OBSIDIAN_VERIFY_SSL) { $env:OBSIDIAN_VERIFY_SSL = 'false' }

$exe = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
if (-not (Test-Path -LiteralPath $exe)) {
  throw "Missing Bifrost binary: $exe"
}

# Stop prior listeners on port
Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process -Name bifrost-http -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$arg = "-app-dir `"$RuntimeRoot`" -host $HostAddress -port $Port -log-level info -log-style json"
$p = Start-Process -FilePath $exe -ArgumentList $arg -WorkingDirectory $RuntimeRoot -PassThru -WindowStyle Hidden
Write-Host "Started bifrost-http PID=$($p.Id) app-dir=$RuntimeRoot"

for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 2
  if ($p.HasExited) {
    throw "Bifrost exited early with code $($p.ExitCode)"
  }
  try {
    $h = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/health" -UseBasicParsing -TimeoutSec 2
    if ($h.StatusCode -eq 200) {
      Write-Host "Healthy after $($i * 2)s"
      exit 0
    }
  } catch {
    # keep waiting
  }
}
throw "Bifrost did not become healthy within timeout"
