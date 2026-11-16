# Grok Bot — MCP enrollment UI

Authority: `contracts/agentcore-gateway-client.json` → `client_render_hints.grokbot`.

## Before you connect

1. Confirm Bifrost health: `GET http://127.0.0.1:8080/health` → 200 on ChaosCentral.
2. Confirm Windows User env `BIFROST_MCP_VK_GROKBOT` exists (dedicated key; do not reuse the Cursor builder key casually).
3. Bifrost stays on loopback (`127.0.0.1:8080`). ChaosCentral publishes it on the **tailnet** via Tailscale Serve: `https://chaoscentral.tailb71e7e.ts.net/mcp` → `http://127.0.0.1:8080/mcp`.
4. Grok Bot’s **cloud computer is not on your tailnet**. The **live approved cloud path** is the dedicated Cloudflare Tunnel hostname below (task `\AgentCore-Grokbot-Cloudflare-Tunnel`, Hidden). Do **not** put Bifrost on an unprotected marketing domain without Access.
5. Enable the connector for the **primary Bot / Chief of Staff** only when possible; specialist Bots share the account-wide computer.

## Custom connector fields (canonical cloud)

| Field | Value |
| --- | --- |
| Name | `agentcore-gateway` |
| Type | Remote HTTPS |
| Server URL (Grok cloud computer — live) | `https://agentcore-grokbot.4axe.com/mcp` |
| HTTP header Key | `x-bf-vk` |
| HTTP header Value | raw Windows User value of `BIFROST_MCP_VK_GROKBOT` (`sk-bf-…`) — **no** `Bearer ` prefix in this UI field |
| Client ID | leave empty |
| OAuth | Do **NOT** click Connect |

Proof: `F:\AgentCore\runtime\bifrost\logs\bifrost-gateway.stdout.log` shows `Cursor/1.0.0` POST `/mcp` → 200 (Cloudflare `http.forwarded_for`).

## Alternate reachability (same connector name)

| Scenario | Server URL | Header |
| --- | --- | --- |
| Same PC / local process | `http://127.0.0.1:8080/mcp` | `Authorization` = `Bearer ` + env `BIFROST_MCP_VK_GROKBOT` |
| Tailnet devices (phone/PC on Tailscale) | `https://chaoscentral.tailb71e7e.ts.net/mcp` | `Authorization` = `Bearer ` + env (or `x-bf-vk` raw — Bifrost accepts both) |

## Forbidden

- Pasting a resolved Bifrost virtual key into ordinary chat
- Adding Swarm MCP, raw OpenRouter MCP, or a second AgentCore front door
- Enrolling `C:\Users\ynotf\.grokbot` as a project root
- Treating Funnel as the primary cloud recipe when the 4axe Cloudflare path is live
