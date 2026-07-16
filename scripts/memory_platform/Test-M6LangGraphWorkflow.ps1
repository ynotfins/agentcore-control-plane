#Requires -Version 5.1
<#
.SYNOPSIS
    M6 Acceptance Test — Durable LangGraph Autonomous Workflow

.DESCRIPTION
    Delegates to scripts/agentcore_workflow/tests/m6_acceptance.py which runs all
    18 M6 acceptance tests and writes results to audits/M6/.

.NOTES
    Authority: BLUEPRINT.md M6 and MEMORY_PLATFORM_EXECUTION_PLAN.md M6.
    Target:    PostgreSQL 18 agent_core on 127.0.0.1:55433.
    Requires:  AGENT_CORE_POSTGRES_PASSWORD env var; Python 3.x in PATH.
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Push-Location $RepoRoot

try {
    $env:PYTHONPATH = "scripts"
    Write-Host "Running M6 acceptance tests..."
    python "scripts\agentcore_workflow\tests\m6_acceptance.py"
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
