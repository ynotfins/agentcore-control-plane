# Obsidian Vault MCP Upstream Disabled — 2026-07-22

**Scope:** Disable `obsidian_vault` from Bifrost runtime and source-controlled registry only. Obsidian application, vault files, plugins, credentials, and backups are preserved unchanged.

## Rationale

Obsidian is an optional human-facing knowledge interface, not canonical AgentCore memory. The upstream was causing recurring reconnect errors (the Obsidian REST API depends on Obsidian being open with the Local REST API plugin active) and adding noise to Bifrost logs without providing tools that agents actively require.

## Changes

### Runtime (`H:\AgentRuntime\bifrost\config.json`)

- Removed `obsidian_vault` from `mcp.client_configs` (13 -> 12 entries)
- Removed `obsidian_vault` grants from VK `mcp_configs`:
  - builder: 12 -> 11
  - reviewer: 9 -> 8
  - docs-knowledge: 4 -> 3
  - operator: 5 -> 4
- Backup: `E:\AgentCore-Backups\bifrost-obsidian-disable-20260722T222237Z` (secret-bearing)

### Source-controlled registry (`contracts/bifrost-upstream-mcp-registry.json`)

- `obsidian-vault.enabled`: `true` -> `false`
- `obsidian-vault.status`: `"active"` -> `"disabled"`
- `obsidian-vault.capability_profiles`: cleared (was builder/reviewer/docs-knowledge/operator)
- Removed `"obsidian-vault"` from `allowed_server_ids` in profiles: builder, reviewer, docs-knowledge, operator

### Launcher (`ops/bifrost/Launch-AgentCoreBifrostGateway.ps1`)

- Commented out `OBSIDIAN_BASE_URL` and `OBSIDIAN_VERIFY_SSL` env defaults (no longer needed)

## Not changed

- Obsidian application install
- `D:\Obsidian\Dungeon Vault` (211 files, ~147 MB — unchanged)
- OBSIDIAN_API_KEY / OBSIDIAN_LOCAL_REST_API / OBSIDIAN_BASE_URL / OBSIDIAN_VERIFY_SSL Windows User env vars (preserved for manual Obsidian use)
- Serena, agentcore-memory, project-router, Playwright, Arabold, Depwire, Tentra, Context Fabric, filesystem, sequential-thinking, cursor-agent-mcp, OpenRouter — all untouched
- PostgreSQL schema
- Swarm
- `PROJECT_ANCHOR.md`, `BLUEPRINT.md`

## Verification (after clean Bifrost restart)

| Check | Result |
| --- | --- |
| `/health` | 200 `status=ok` |
| `tools/list` total | 135 |
| `agentcore_memory-*` | exactly 10 |
| `agentcore_project_router-*` | exactly 4 |
| `playwright-*` | 24 |
| `obsidian_vault-*` | **0 (absent)** |
| Forbidden tools (swarm/sql/admin) | absent |
| Obsidian reconnect errors in post-restart log | **0** |
| Vault on disk | 211 files, ~147 MB — intact |
| `python scripts/bifrost/validate_contracts.py` | OK (enabled 12, disabled/deferred 5) |

## Rollback

```powershell
Copy-Item -Force 'E:\AgentCore-Backups\bifrost-obsidian-disable-20260722T222237Z\config.json' 'H:\AgentRuntime\bifrost\config.json'
# Then revert registry commit and restart Bifrost
schtasks /run /tn "\AgentCore\AgentCore-Bifrost-Gateway"
```
