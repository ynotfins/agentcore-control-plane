# Proposal: Trust Class A for Zoo Code (VSCodium), Cline and Continue

**Date:** 2026-11-15
**Status:** proposal only. This file does not edit any governed_mutable or operator_locked file.
**Operator request (Tony, 2026-11-15, in chat):** "add continue as a first class app in agentcore-control-plane first and give both zoocode, cline and continue the highest trust."
**Why a proposal:** the highest trust tier is Trust Class A, defined in `contracts/global-agent-policy.yaml` rule `client-trust-classes`. That file is `governed_mutable` in `contracts/authority-lock.yaml` (authority_maintainer, AUTH id, validators, independent review). The per-client gateway hints live in `contracts/agentcore-gateway-client.json`, which is also `governed_mutable`. This PR lands the normal-workstream profiles, renderers, matrix rows, tests and audit, and leaves these two edits for formal admission.

## 1. `contracts/global-agent-policy.yaml` - rule `client-trust-classes`

Replace the first sentence of the rule:

```diff
-      Trust Class A consists exactly of Cursor, Codex, Devin, Antigravity, ZCode,
-      MiniMax coding clients, and Open Interpreter. For these clients, every technically
+      Trust Class A consists exactly of Cursor, Codex, Devin, Antigravity, ZCode,
+      MiniMax coding clients, Open Interpreter, and the VSCodium-hosted Zoo Code, Cline,
+      and Continue extensions. For these clients, every technically
```

Keep the existing sentence "Zoo-Code is a separate extension and is not ZCode." Recommended addition after it: "The Cursor-hosted zoo-code profile remains Trust Class B until separately admitted." (Tony may instead ask for both Zoo Code hosts; this proposal admits only the VSCodium host he uses.)

All other restrictions in the rule (authority locks, secret handling, database ownership, external-action intent, Swarm boundary, no shared implicit-project servers, no whole-drive filesystem MCP roots) stay unchanged.

## 2. `contracts/agentcore-gateway-client.json` - `client_render_hints`

Add (and correct the VSCodium path proposed in `2026-11-15-vscodium-gateway-client-hint.md`; the live VSCodium profile is `I:\LocalApps\VSCodium\user-data`, not `%APPDATA%\VSCodium`):

```json
"vscodium": {
  "enabled": true,
  "config_path": "I:\\LocalApps\\VSCodium\\user-data\\User\\mcp.json",
  "syntax": "vscodium_mcp_json",
  "supports_env_headers": true,
  "gateway_url": "http://127.0.0.1:8080/mcp",
  "gateway_auth_mode": "bearer_env",
  "notes": ["VSCodium launches via I:\\LocalApps\\VSCodium\\Launch-VSCodium.cmd with --user-data-dir I:\\LocalApps\\VSCodium\\user-data. Built-in chat only; hosted extensions have their own hints."]
},
"zoo-code-vscodium": {
  "enabled": true,
  "config_path": "I:\\LocalApps\\VSCodium\\user-data\\User\\globalStorage\\zoocodeorganization.zoo-code\\settings\\mcp_settings.json",
  "syntax": "zoo_code_mcp_json",
  "supports_env_headers": true,
  "gateway_url": "http://127.0.0.1:8080/mcp",
  "gateway_auth_mode": "bearer_env",
  "notes": ["type streamable-http; Authorization Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}. Distinct from the Cursor-hosted zoo-code hint, which is unchanged."]
},
"cline": {
  "enabled": true,
  "config_path": "C:\\Users\\ynotf\\.cline\\data\\settings\\cline_mcp_settings.json",
  "syntax": "cline_mcp_json",
  "supports_env_headers": true,
  "gateway_url": "http://127.0.0.1:8080/mcp",
  "gateway_auth_mode": "bearer_env",
  "notes": ["Cline 4.x path (CLINE_DIR/CLINE_DATA_DIR/CLINE_MCP_SETTINGS_PATH unset). type streamableHttp; Authorization Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}. UI toggles can rewrite env references with resolved values (cline/cline#9065); edit the file instead."]
},
"continue": {
  "enabled": true,
  "config_path": "C:\\Users\\ynotf\\.continue\\config.yaml",
  "syntax": "continue_config_yaml",
  "supports_env_headers": true,
  "gateway_url": "http://127.0.0.1:8080/mcp",
  "gateway_auth_mode": "bearer_env",
  "notes": ["mcpServers list entry: type streamable-http, requestOptions.headers.Authorization Bearer ${{ secrets.BIFROST_MCP_VIRTUAL_KEY }} (Continue resolves secrets from .env files, then the editor process environment). MCP is agent-mode only."]
}
```

## Required follow-through when admitted

- Record an `AUTH-2026-11-15-...` approval identifier.
- Timestamped rollback copies of both contracts.
- Re-render: `python scripts/render_ide_rules.py` (GLOBAL_RULES embed the trust-class rule).
- `python scripts/validate_authority_lock.py`, `python scripts/bifrost/validate_contracts.py`, `python scripts/bifrost/test_contracts.py`.
- Flip `effective_trust_class` to `A` in `ide-profiles/{continue,cline,zoo-code-vscodium}/IDE_PROFILE.yaml` and the matrix rows.
- Independent review of the Bifrost MCP contract plane (Cursor-owned).

## Gateway credential note

Trust Class A clients use the builder virtual key by environment reference (`BIFROST_MCP_VIRTUAL_KEY`, per `docs/bifrost/UNIFIED_GATEWAY_SETUP.md`). On 2026-11-15 both `BIFROST_MCP_VIRTUAL_KEY` and `BIFROST_MCP_VK_IDE` returned the same 168-tool surface, so the key choice does not yet change what these clients see; the admission above is what changes their authority.