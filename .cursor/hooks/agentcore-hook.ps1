# AgentCore Cursor hook wrapper (PowerShell) — reliable stdin forwarding on Windows.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/agentcore-hook.ps1 -Event sessionStart
param(
    [Parameter(Mandatory = $true)][string]$Event
)

$ErrorActionPreference = "Stop"
$dispatcher = Join-Path $PSScriptRoot "..\..\scripts\agentcore_cursor\hook_dispatcher.py"
if (-not (Test-Path -LiteralPath $dispatcher)) {
    [Console]::Out.Write('{"error":"missing_dispatcher"}')
    exit 2
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if (-not $python) {
        [Console]::Out.Write('{"error":"missing_python"}')
        exit 2
    }
    $exe = $python.Source
    $argList = @("-3", "-u", $dispatcher, $Event)
} else {
    $exe = $python.Source
    $argList = @("-u", $dispatcher, $Event)
}

$raw = [Console]::In.ReadToEnd()
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.Arguments = ($argList | ForEach-Object {
        if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
    }) -join ' '
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
$psi.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
$psi.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"

$proc = [System.Diagnostics.Process]::Start($psi)
$proc.StandardInput.Write($raw)
$proc.StandardInput.Close()
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
if ($stderr) { [Console]::Error.Write($stderr) }
[Console]::Out.Write($stdout)
exit $proc.ExitCode
