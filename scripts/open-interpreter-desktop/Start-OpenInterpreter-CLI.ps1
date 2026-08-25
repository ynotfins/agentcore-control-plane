# Open Interpreter CLI (sandboxed) — AgentCore control-plane workspace
$ErrorActionPreference = 'Stop'
$env:CODEX_HOME = Join-Path $env:USERPROFILE '.openinterpreter-cli'
Set-Location 'D:\github\agentcore-control-plane'
& interpreter -p coding