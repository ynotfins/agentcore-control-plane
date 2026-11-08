# Grok Bot — MCP enrollment UI

Authority: `contracts/agentcore-gateway-client.json` → `client_render_hints.grokbot`.

## Before you connect

1. Confirm Bifrost health: `GET http://127.0.0.1:8080/health` → 200 on ChaosCentral.
2. Confirm Windows User env `BIFROST_MCP_VK_GROKBOT` exists (dedicated key; do not reuse the Cursor builder key casually).
3. Bifrost stays on loopback (`127.0.0.1:8080`). ChaosCentral already publishes it on the **tailnet only** via Tailscale Serve: `https://chaoscentral.tailb71e7e.ts.net/mcp` → `http://127.0.0.1:8080/mcp`.
4. Grok Bot’s **cloud computer is not on your tailnet**. Tailnet Serve works for your phones/PCs on Tailscale. For Grok cloud MCP, enable Tailscale **Funnel** on `/mcp` only, or a Cloudflare Tunnel — still Bearer-protected; do **not** put Bifrost on a public marketing domain without Access.
5. Enable the connector for the **primary Bot / Chief of Staff** only when possible; specialist Bots share the account-wide computer.

## Custom connector fields

| Field | Value |
| --- | --- |
| Name | `agentcore-gateway` |
| Type | Remote HTTPS |
| Server URL (same PC / local process) | `http://127.0.0.1:8080/mcp` |
| Server URL (tailnet devices: phone, laptop) | `https://chaoscentral.tailb71e7e.ts.net/mcp` |
| Server URL (Grok cloud computer) | Same Funnel/Tunnel HTTPS URL after you enable one — not plain MagicDNS `:8080` |
| HTTP header Key | `Authorization` |
| HTTP header Value | `Bearer ` + the Windows User value of `BIFROST_MCP_VK_GROKBOT` via env expansion or Grok secure secret card — **never paste into chat** |
| Client ID | leave empty |

## Forbidden

- Pasting a resolved Bifrost virtual key into ordinary chat
- Adding Swarm MCP, raw OpenRouter MCP, or a second AgentCore front door
- Enrolling `C:\Users\ynotf\.grokbot` as a project root
