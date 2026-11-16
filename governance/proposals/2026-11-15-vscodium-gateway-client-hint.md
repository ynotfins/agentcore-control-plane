# Proposal: admit VSCodium to `contracts/agentcore-gateway-client.json`

**Date:** 2026-11-15  
**Status:** proposal only — this file does not edit the governed_mutable contract.  
**Approval already given for enrollment work:** Tony, 2026-11-15, "Yes add VSCodium to the control plane and installing the agentcore-gateway MCP in VSCodium".  
**Why this is a proposal:** `contracts/agentcore-gateway-client.json` is governed_mutable (authority-maintainer, AUTH id, validators, independent review). Cursor is the sole primary owner of the Bifrost MCP contract plane. This PR therefore lands the normal-workstream profile, renderer, tests, and matrix entry, and leaves the contract hint for formal admission.

## Proposed `client_render_hints.vscodium` entry

Insert alongside the existing `client_render_hints` peers (for example after `cursor` or `zoo-code`):

```json
"vscodium": {
  "enabled": true,
  "config_path": "C:\\Users\\ynotf\\AppData\\Roaming\\VSCodium\\User\\mcp.json",
  "alternate_config_paths": [
    "C:\\Users\\ynotf\\AppData\\Roaming\\VSCodium\\User\\globalStorage\\zoocodeorganization.zoo-code\\settings\\mcp_settings.json"
  ],
  "syntax": "vscodium_mcp_json",
  "supports_env_headers": true,
  "gateway_url": "http://127.0.0.1:8080/mcp",
  "gateway_auth_mode": "bearer_env",
  "notes": [
    "VSCodium 1.143+ native MCP at User/mcp.json; Zoo Code companion settings are an alternate path on this host only.",
    "Use type streamable-http + url http://127.0.0.1:8080/mcp + headers Authorization Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}.",
    "Preserve any existing non-AgentCore servers already present in the live files.",
    "Exactly one AgentCore MCP entry: agentcore-gateway. Never paste or persist a resolved virtual key.",
    "This client is distinct from the Cursor-hosted zoo-code profile."
  ]
}
```

No change is proposed to `zoo-code` (still Cursor-hosted, still `enabled: false` / `unverified` until a separate secure-route decision).

## Required follow-through when admitted

- Record an `AUTH-2026-11-15-...` approval identifier.
- Timestamped rollback copy of the contract.
- `python scripts/validate_authority_lock.py`
- `python scripts/bifrost/validate_contracts.py`
- Independent review of the Bifrost MCP contract plane (Cursor-owned).
