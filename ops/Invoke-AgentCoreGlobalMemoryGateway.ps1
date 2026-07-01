param(
  [ValidateSet("Mcp")]
  [string]$Mode = "Mcp",
  [string]$Platform = "agentcore",
  [string]$ProjectId = "codex-managed",
  [string]$UserId = "master_developer_profile",
  [string]$ManagedRoot = "D:\Codex_Managed",
  [string]$Python = "D:\Codex_Managed\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

# Canonical uniform launcher for the AgentCore global-memory-gateway MCP (stdio).
# Wraps the source-authority Python module launch (supervisor/servers.json + renderers) so every IDE
# uses ONE launcher and does not need to set a working directory or expand env vars in its MCP config.
# Credentials (AGENT_CORE_*, OPENAI_API_KEY) are inherited from Windows User-scope environment variables.
# Local-only. No secrets are printed or stored here.

if (-not (Test-Path -LiteralPath $Python)) { Write-Error "Gateway Python venv not found: $Python"; exit 1 }
if (-not (Test-Path -LiteralPath $ManagedRoot)) { Write-Error "Gateway managed root not found: $ManagedRoot"; exit 1 }

Set-Location -LiteralPath $ManagedRoot
& $Python -m autonomy_factory.global_memory_gateway `
  --user-id $UserId `
  --project-id $ProjectId `
  --platform $Platform
exit $LASTEXITCODE
