# Bifrost Operator Runbook

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`  
**Runtime:** `H:\AgentRuntime\bifrost`  
**Scheduled Task:** `\AgentCore\AgentCore-Bifrost-Gateway`  
**Updated:** 2026-07-24  

## Quick Health Check

```powershell
# Check health
Invoke-WebRequest "http://127.0.0.1:8080/health" -UseBasicParsing

# Check MCP tools
\ = [System.Environment]::GetEnvironmentVariable("BIFROST_MCP_VIRTUAL_KEY", "User")
\ = @{ "Authorization" = "Bearer \" }
# ... (initialize, notifications/initialized, then tools/list)
```

## Start/Stop/Restart

```powershell
# Stop
& "D:\github\agentcore-control-plane\ops\bifrost\Stop-AgentCoreBifrostGateway.ps1"

# Start
& "D:\github\agentcore-control-plane\ops\bifrost\Start-AgentCoreBifrostGateway.ps1"

# Status
Get-ScheduledTask -TaskPath "\AgentCore\" -TaskName "AgentCore-Bifrost-Gateway" | Select-Object State
```

## Config Change Workflow

1. Edit source renderer: `renderers/bifrost/config.json`
2. Validate: `python scripts/bifrost/validate_contracts.py`
3. Copy to runtime: `Copy-Item renderers/bifrost/config.json H:\AgentRuntime\bifrost\config.json`
4. Restart: use stop/start scripts above
5. Verify: health check + tools/list

## Virtual Key Management

VKs are defined in `renderers/bifrost/config.json` under `governance.virtual_keys`.
Each VK references an env var via `"value": "env.BIFROST_MCP_VK_NAME"`.

To add a new VK:
1. Generate token: `python -c "import secrets; print(secrets.token_urlsafe(60))"`
2. Set User env var: `[System.Environment]::SetEnvironmentVariable("BIFROST_MCP_VK_NAME", "<token>", "User")`
3. Add VK entry to config.json
4. Restart Bifrost

Current VKs: builder, reviewer, database-validator, docs-knowledge, operator, chatgpt (pending env var)

## Provider Management

See `docs/bifrost/BIFROST_PROVIDER_RUNBOOK.md` for provider details.

## Dashboard

URL: `http://127.0.0.1:8080`  
Auth: Currently disabled (loopback-only — acceptable per PROJECT_ANCHOR.md §3.9)  
Do NOT expose dashboard through the ChatGPT compat proxy.
