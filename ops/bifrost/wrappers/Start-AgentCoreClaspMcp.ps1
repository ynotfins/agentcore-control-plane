[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ClaspCommand = "C:\Users\ynotf\AppData\Roaming\npm\clasp.cmd"
$PythonCommand = "C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe"
$GuardScript = "D:\github\agentcore-control-plane\scripts\bifrost\clasp_mcp_guard.py"
$ExpectedVersion = "3.4.1"
$AppsScriptRoot = "D:\github\apps-script"

if (-not (Test-Path -LiteralPath $ClaspCommand -PathType Leaf)) {
    [Console]::Error.WriteLine("AgentCore clasp MCP refused to start: exact clasp.cmd path is missing.")
    exit 1
}

if (-not (Test-Path -LiteralPath $AppsScriptRoot -PathType Container)) {
    [Console]::Error.WriteLine("AgentCore clasp MCP refused to start: Apps Script root is missing.")
    exit 1
}

if (-not (Test-Path -LiteralPath $PythonCommand -PathType Leaf) -or
    -not (Test-Path -LiteralPath $GuardScript -PathType Leaf)) {
    [Console]::Error.WriteLine("AgentCore clasp MCP refused to start: policy guard runtime is missing.")
    exit 1
}

$VersionOutput = (& $ClaspCommand --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $VersionOutput -ne $ExpectedVersion) {
    [Console]::Error.WriteLine("AgentCore clasp MCP refused to start: exact clasp version 3.4.1 is required.")
    exit 1
}

Set-Location -LiteralPath $AppsScriptRoot
& $PythonCommand -u $GuardScript --root $AppsScriptRoot -- $ClaspCommand mcp
exit $LASTEXITCODE
