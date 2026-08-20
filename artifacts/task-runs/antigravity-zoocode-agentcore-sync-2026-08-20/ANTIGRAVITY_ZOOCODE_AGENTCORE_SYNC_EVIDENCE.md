# Antigravity Zoo-Code AgentCore Sync Evidence

Timestamp: 2026-08-20T16:42:15-04:00

## Scope

- Register Antigravity with AgentCore gateway.
- Sync Antigravity Zoo-Code to the same saved Zoo-Code setup Cursor uses.
- Preserve the Zoo-Code side-panel workflow; do not route Zoo-Code UI through Bifrost.

## Live Files Touched

- `C:\Users\ynotf\AppData\Roaming\Antigravity\User\settings.json`
- `C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json`
- `C:\Users\ynotf\.gemini\config\mcp_config.json`
- `C:\Users\ynotf\AppData\Roaming\Antigravity\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`
- `C:\Users\ynotf\AppData\Roaming\Antigravity\User\globalStorage\zoocodeorganization.zoo-code\settings\custom_modes.yaml`

## Rollback Backups

- `C:\Users\ynotf\AppData\Roaming\Antigravity\User\settings.json.agentcore-zoo-20260820-164111.bak`
- `C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json.agentcore-zoo-20260820-164111.bak`
- `C:\Users\ynotf\.gemini\config\mcp_config.json.agentcore-zoo-20260820-164111.bak`

## Verified Configuration

- Antigravity user settings now include `zoo-code.autoImportSettingsPath` pointing to `C:\Users\ynotf\Downloads\roo-code-settings.json`.
- Cursor already had the same `zoo-code.autoImportSettingsPath`.
- Saved Zoo-Code setup file exists at `C:\Users\ynotf\Downloads\roo-code-settings.json`.
- Saved Zoo-Code setup current profile is `Zoo Gateway`.
- Saved Zoo-Code setup uses `zoo-gateway` with model `deepseek/deepseek-v4-pro-0813`.
- Saved Zoo-Code setup has `mcpEnabled: true`, checkpoints enabled, auto-condense enabled, diagnostics enabled, current time/cost display enabled, and conservative auto-approval defaults.
- Saved Zoo-Code setup has `customModes: []`; no custom skill/mode pack was present in that export.
- Antigravity general MCP configs contain exactly one active server: `agentcore-gateway` at `http://127.0.0.1:8080/mcp`.
- Antigravity Zoo-Code extension-owned MCP settings contain exactly one active server: `agentcore-gateway` at `http://127.0.0.1:8080/mcp`.
- Cursor Zoo-Code extension-owned MCP settings contain exactly one active server: `agentcore-gateway` at `http://127.0.0.1:8080/mcp`.
- `ops\bifrost\Test-AgentCoreBifrostGateway.ps1` passed: `/health` returned 200, authenticated MCP `initialize` succeeded, authenticated MCP `tools/list` returned 34 tools, and forbidden Swarm/Postgres/direct-database patterns were absent.

## Quarantine

The `.gemini\config\mcp_config.json` active surface was reduced to AgentCore-only. Prior direct entries were moved to non-secret `x_agentcore_quarantined_servers` metadata:

- `notebooks`
- `visualization`
- `data-agent-kit`
- `morph-mcp`

The prior active `morph-mcp` entry contained a raw local secret; the active config no longer stores that raw secret.

## Remaining Validation

Full M8 enrollment is not complete until a fresh Antigravity/Zoo-Code task after restart proves:

- Zoo-Code imported the saved setup in Antigravity.
- Zoo-Code account state is active in Antigravity.
- AgentCore gateway tools are discoverable from the Zoo-Code side panel.
- `agentcore-memory` native lifecycle works from that fresh task.
- Restart persistence is proven.
