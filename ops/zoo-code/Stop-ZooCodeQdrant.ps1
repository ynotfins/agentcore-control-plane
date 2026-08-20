[CmdletBinding()]
param(
  [string]$Root = "I:\LocalApps\ZooCode\qdrant"
)

$ErrorActionPreference = "Stop"

$exe = (Join-Path $Root "current\qdrant.exe").ToLowerInvariant()
$pidFile = Join-Path $Root "runtime\qdrant.pid"
$stopped = @()

if (Test-Path -LiteralPath $pidFile) {
  $pidText = (Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($pidText -match '^\d+$') {
    $process = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
    if ($process) {
      $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($process.Id)" -ErrorAction SilentlyContinue).ExecutablePath
      if ($cmd -and $cmd.ToLowerInvariant() -eq $exe) {
        Stop-Process -Id $process.Id -Force
        $stopped += $process.Id
      }
    }
  }
}

$owned = Get-CimInstance Win32_Process -Filter "Name = 'qdrant.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.ExecutablePath -and $_.ExecutablePath.ToLowerInvariant() -eq $exe }
foreach ($proc in $owned) {
  Stop-Process -Id $proc.ProcessId -Force
  $stopped += $proc.ProcessId
}

if (Test-Path -LiteralPath $pidFile) {
  Remove-Item -LiteralPath $pidFile -Force
}

[PSCustomObject]@{
  status = "stopped"
  stopped_pids = @($stopped | Sort-Object -Unique)
}
