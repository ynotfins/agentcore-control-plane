# Bifrost MCP Audit — 2026-08-05

## Goals

1. Audit every Bifrost MCP upstream and classify whether it should be active in Bifrost, dormant/project-scoped, disabled, or handled outside the shared gateway.
2. Add daily self-healing coverage for Bifrost runtime drift without silently changing IDE configs or activating dormant project-scoped servers.

## Current live result

`agentcore-gateway` remains the single normal IDE MCP entry at `http://127.0.0.1:8080/mcp`.

Live Bifrost is healthy on `127.0.0.1:8080`; authenticated MCP `initialize` and `tools/list` passed through `ops/bifrost/Test-AgentCoreBifrostGateway.ps1`.

## Active upstream classification

| Client | Status | Placement decision | Change |
| -- | -- | -- | -- |
| `agentcore_memory` | active | Bifrost STDIO, classic mode | unchanged; exact 10-tool surface |
| `agentcore_project_router` | active | Bifrost STDIO, classic mode | unchanged; operator-only profile |
| `arabold_docs` | active | Bifrost STDIO, Code Mode | wildcard replaced with 10 named tools |
| `cursor_agent_mcp` | active | Bifrost STDIO, classic mode | wildcard replaced with 9 named tools so subagent controls remain direct |
| `openrouter` | authenticated dormant/JIT | Bifrost HTTP OAuth, zero default VK exposure | live tool inventory refreshed; side-effect tools denied |
| `playwright` | active | Bifrost STDIO, Code Mode | wildcard replaced with 22 named tools; `browser_file_upload` and `browser_run_code_unsafe` denied |
| `sequential_thinking` | active | Bifrost STDIO, classic mode | wildcard replaced with exact `sequentialthinking` |
| `skills_hub` | active | Bifrost STDIO, classic mode | unchanged; `install_skill` denied |

## Dormant / disabled decisions

The following remain intentionally not active in shared Bifrost default profiles:

- `serena`, `depwire`, `tentra`, `context-fabric`, `filesystem`, `firebase-mcp`: project-scoped; require trustworthy per-session project identity or host-local explicit-project execution.
- `artiforge`, `depwire-cloud`, `github-mcp`, `google-sheets-mcp`, `mcp-debugger`, `obsidian-vault`: disabled/deferred until service health, auth, named tool inventory, and activation rollback are proven.

## Runtime changes

- Rendered runtime config to `F:\AgentCore\runtime\bifrost\config.json`.
- Restarted `\AgentCore\AgentCore-Bifrost-Gateway`.
- Preserved OpenRouter OAuth runtime state during render.
- Removed unmanaged `morph-mcp` from `C:\Users\ynotf\.cursor\mcp.json`; backup: `F:\AgentCore\runtime\bifrost\backups\cursor-mcp-20260805-052615\mcp.json`.
- Runtime config backup before first render: `F:\AgentCore\runtime\bifrost\backups\20260805-052440`.

## Self-healing automation

Added `ops/bifrost/Invoke-AgentCoreBifrostDailyAudit.ps1`.

Registered Windows scheduled task:

- Task: `\AgentCore\AgentCore-Bifrost-Daily-Audit`
- Schedule: daily at 03:45 local time
- Behavior: validate contracts, run live Bifrost postflight, and if `-Repair` is enabled, backup → render → restart → re-test Bifrost runtime only.
- Boundary: does not mutate IDE configs, does not activate dormant servers, does not handle secrets.

## Verification

Commands passed:

```powershell
python scripts\bifrost\validate_contracts.py
python -m unittest scripts.bifrost.test_openrouter_classification scripts.bifrost.test_contracts
.\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
.\ops\bifrost\Invoke-AgentCoreBifrostDailyAudit.ps1
```

Final postflight result: `RESULT: PASSED`.

## Residuals

- OpenRouter live management API currently reports 22 discovered tools while the visible name inventory includes the newly classified side-effect surfaces. Normal IDE exposure remains zero without JIT lease.
- Code Mode should be monitored in daily use; rollback is to remove `is_code_mode_client` from `arabold_docs` or `playwright`, render, restart, and re-run postflight.
