# Bifrost Operator Runbook

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`  
**Runtime:** `F:\AgentCore\runtime\bifrost`
**Scheduled Task:** `\AgentCore\AgentCore-Bifrost-Gateway`  
**Updated:** 2026-09-08

## Quick Health Check

```powershell
# Check health
Invoke-WebRequest "http://127.0.0.1:8080/health" -UseBasicParsing

# Check MCP tools
$vk = [System.Environment]::GetEnvironmentVariable("BIFROST_MCP_VIRTUAL_KEY", "User")
$headers = @{ "Authorization" = "Bearer $vk" }
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

### Availability and supervision contract

- Core Bifrost listens on `127.0.0.1:8080`. The scheduled task is expected to
  remain running after the owning user logs on.
- The current task is `AtLogOn` with an `Interactive`, `Limited` principal.
  Required credentials are Windows User environment variables, so this design
  does not guarantee gateway availability before that user logs on.
- The watchdog gives startup 120 seconds, requires two consecutive failed probes,
  and starts a `Ready` or other non-`Running` task idempotently. A `Running` task
  is recycled with a controlled stop followed by start.
- A failed stop/start attempt is retried only after the bounded 60-second
  backoff. A current maintenance marker suppresses automatic launch and recycle.
- The process-attested compatibility proxy listens on `127.0.0.1:18082`. Proxy
  startup failure logs `BUILDER_COMPAT_PROXY_DEGRADED` and is nonfatal to core
  `:8080`; clients assigned to `:18082` remain degraded until it recovers.

Do not describe this task topology as true pre-login always-on service hosting.

## Config Change Workflow

1. Edit the owning contracts and `scripts/bifrost/render_bifrost_config.py`; never hand-edit generated renderer output.
2. Validate with the repository runtime: `scripts\.venv\Scripts\python.exe scripts/bifrost/validate_contracts.py` and `scripts\.venv\Scripts\python.exe scripts/bifrost/test_contracts.py`.
3. Preview with `scripts\.venv\Scripts\python.exe scripts/bifrost/render_bifrost_config.py --stdout --skip-renderer`, then render/apply through the governed installer or rollout operation.
4. Prefer the documented upstream-client reconnect API for a connection-only recycle. Use the scheduled-task stop/start owner when launch-command/config persistence requires a full recycle.
5. Verify: health check, authenticated tools/list, and a representative safe tool call from each changed upstream.

## Virtual Key Management

Virtual-key profiles derive from the capability-profile contracts and
`scripts/bifrost/render_bifrost_config.py`. `renderers/bifrost/config.json` is a
generated projection and must not be edited directly. Rendered VK values reference
Windows User environment names such as `env.BIFROST_MCP_VK_NAME`.

To add or rotate a VK:

1. Confirm the profile and authority boundary in the contracts.
2. Generate and store the value directly in the approved Windows User environment
   variable without printing or logging it.
3. Update the owning contract or renderer logic; never patch generated config only.
4. Run contract, renderer, secret, and profile-isolation tests.
5. Apply through the governed runtime workflow and verify authenticated MCP access.

Resolve the current VK/profile set from the registry, renderer, and live status;
do not use a copied list from this runbook.

## Provider Management

See `docs/bifrost/BIFROST_PROVIDER_RUNBOOK.md` for provider details.

## Dashboard

URL: `http://127.0.0.1:8080`  
Auth and exposure: verify against current `PROJECT_ANCHOR.md`, rendered configuration, and live status; never infer safety from loopback binding alone.
Do NOT expose dashboard through the ChatGPT compat proxy.
