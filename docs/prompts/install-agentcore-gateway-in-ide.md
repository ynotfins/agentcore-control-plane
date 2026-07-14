# Install AgentCore Gateway in an IDE

Reusable operator/agent prompt for **any** supported non-Swarm IDE on this PC.

**Authority:** `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `contracts/agentcore-gateway-client.json`, `docs/bifrost/UNIFIED_GATEWAY_SETUP.md`, `renderers/gateway-clients/<ide>.json`
**Endpoint:** `http://127.0.0.1:8080/mcp`
**Auth env:** `BIFROST_MCP_VIRTUAL_KEY` (never print the value)
**Display name in IDEs:** `agentcore-gateway` (not `bifrost`)

---

## Prompt (copy into an IDE agent)

You are installing and validating the AgentCore Bifrost MCP gateway client for this IDE. Follow these steps exactly. Do not invent alternate architectures. Do not modify Swarm product installs. Do not modify OpenClaw/ClawX. Do not print secrets.

### Goal

Unify this non-Swarm IDE onto a **single** MCP entry `agentcore-gateway` → `http://127.0.0.1:8080/mcp` authenticated with `BIFROST_MCP_VIRTUAL_KEY`. All AgentCore tools (Depwire, Serena, Arabold, Tentra, etc.) must come through Bifrost upstreams — not as direct IDE MCP blocks.

For Cursor specifically, the canonical live file is `C:\Users\ynotf\.cursor\mcp.json`.
Do not create or keep project-level duplicate gateway entries in `<repo>\.cursor\mcp.json`
or `<repo>\.mcp.json`; project identity is selected through `agentcore_project_router`.

### Steps

1. **Read AgentCore authority.** Open and follow `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `contracts/agentcore-gateway-client.json`, `docs/bifrost/UNIFIED_GATEWAY_SETUP.md`, and `MASTER_CONFIG_AND_PROMPT.md` (gateway sections). Confirm the Bifrost Gateway Override applies to this non-Swarm IDE.

2. **Identify the actual active config file and schema.** Resolve the live path for this IDE from `contracts/agentcore-gateway-client.json` → `client_render_hints`. Confirm JSON vs TOML and the MCP key (`mcpServers`, `mcp_servers`, etc.).

3. **Back up the config.** Timestamped `.bak` beside the live file and/or under `E:\AgentCore-Backups\...`. Record SHA256. Do not skip backup.

4. **Preserve unrelated settings.** Keep model, auth, sandbox, context-window, profile, theme, and non-MCP application settings untouched.

5. **Remove old direct baseline MCP entries after backup.** Remove direct entries for servers that now live behind Bifrost. Remove SwarmRecall/SwarmVault from this non-Swarm IDE. Keep only explicitly allowed side entries (e.g. Cursor may keep `MCP_DOCKER`).

6. **Add only `agentcore-gateway`.** Use the schema-correct block from `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` or `renderers/gateway-clients/<ide>.json`.

   For Cursor, ensure this entry is in the global file `C:\Users\ynotf\.cursor\mcp.json`.
   If a project-level duplicate points to `http://127.0.0.1:8080/mcp`, back it up and remove it
   unless it is explicitly labeled rollback-only.

7. **Use the current canonical endpoint.** URL must be `http://127.0.0.1:8080/mcp`.

8. **Use `BIFROST_MCP_VIRTUAL_KEY` without printing it.** Prefer `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`. If this client cannot expand env headers, materialize the User-env value into the **live** config only — never commit it, never echo it. For a narrower surface, use a profile VK (`BIFROST_MCP_VK_REVIEWER`, `BIFROST_MCP_VK_DOCS_KNOWLEDGE`, etc.) per `docs/bifrost/CAPABILITY_PROFILES.md`.

9. **Validate syntax.** Parse JSON/TOML successfully before restart.

10. **Ensure Bifrost is running.** `GET http://127.0.0.1:8080/health` → 200. If down, start via `ops/bifrost` / Scheduled Task `\AgentCore\AgentCore-Bifrost-Gateway`. Do not fall back to pasting full server blocks into the IDE.

11. **Fully quit and relaunch this IDE.** User env vars are not visible to processes started before the VK existed. Partial reload is not enough if discovery returns 401 / failed tools.

12. **Run gateway discovery.** Confirm `agentcore-gateway` connects and tools appear (often prefixed `arabold_docs-*`, `depwire-*`, `tentra-*`, …). Report tool count / connected upstreams if available.

13. **Verify project identity.** Use `agentcore_project_router` (`project_activate`) for a registered `D:\github\...` worktree before project-scoped tools.

14. **Report unsupported client capabilities.** If the IDE cannot do HTTP MCP, headers auth, or env expansion, document the limitation and safe workaround (no secrets).

15. **Preserve rollback.** Leave backup path + SHA256 in evidence. Point to `docs/bifrost/ROLLBACK_RUNBOOK.md` if revert is needed.

### Hard forbids

- `:65432` / whole-drive filesystem roots
- Direct PostgreSQL credentials in IDE configs
- Requiring Swarm MCP for this non-Swarm IDE
- Treating `experiments/bifrost-go-sdk-smoke` as the gateway
- Adding new AgentCore MCPs only in the IDE config (must go through Bifrost registry)

### Adding a new MCP later (instruct the operator)

1. Edit `contracts/bifrost-upstream-mcp-registry.json` (server + capability profile membership).
2. Render Bifrost config; validate; restart Bifrost.
3. Leave IDE configs on single `agentcore-gateway` — do not add a second direct server for AgentCore tools.

### Preventing unwanted tools from loading

- Disable upstream: `"enabled": false` in registry → re-render → restart Bifrost.
- Per-profile deny: omit client from VK `mcp_configs`, or set `"tools_to_execute": []` (Bifrost v2 deny).
- Allowlist tools: put only named tool names in `tools_to_execute`.
- Narrow IDE: point Bearer at a profile VK (`reviewer`, `docs-knowledge`, etc.).
- Do not treat IDE UI toggles as the multi-IDE source of truth.

### Evidence

Write a sanitized note under `artifacts/` or `ops/bifrost/evidence/` listing: IDE name, config path, backup path, SHA256, env-header vs materialized, discovery result, blockers — **no secret values**.
