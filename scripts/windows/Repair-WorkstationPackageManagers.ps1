#Requires -Version 5.1
param([switch]$SkipQuarantine)
$ErrorActionPreference = 'Stop'
$shimDir = Join-Path $env:LOCALAPPDATA 'Corepack\shims'
$npmGlobal = Join-Path $env:APPDATA 'npm'
$nodejs = 'C:\Program Files\nodejs'
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
$entries = @($userPath -split ';' | ForEach-Object Trim | Where-Object { $_ })
$filtered = @($entries | Where-Object { $_.TrimEnd('\') -ne $shimDir.TrimEnd('\') -and $_.TrimEnd('\') -ne $npmGlobal.TrimEnd('\') })
$rebuilt = New-Object System.Collections.Generic.List[string]
$inserted = $false
foreach ($e in $filtered) {
  [void]$rebuilt.Add($e)
  if (-not $inserted -and $e.TrimEnd('\') -eq $nodejs.TrimEnd('\')) { [void]$rebuilt.Add($npmGlobal); $inserted = $true }
}
if (-not $inserted) { $rebuilt.Insert(0, $npmGlobal) }
[Environment]::SetEnvironmentVariable('Path', ($rebuilt -join ';'), 'User')
if (-not $SkipQuarantine -and (Test-Path -LiteralPath $shimDir)) {
  $q = Join-Path $env:LOCALAPPDATA ("Corepack\shims.disabled-{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
  Move-Item -LiteralPath $shimDir -Destination $q -Force
  Write-Host "Quarantined -> $q"
}
$env:Path = ([Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine'))
where.exe pnpm; pnpm -v
