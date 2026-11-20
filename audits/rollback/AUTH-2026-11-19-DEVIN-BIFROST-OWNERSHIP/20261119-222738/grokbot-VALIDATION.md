# Validation — Grok Bot

Mark `live_validated` only when all pass:

1. Bifrost `GET /health` returns 200 on ChaosCentral.
2. Custom connector name is exactly `agentcore-gateway`.
3. Cloud connector URL is exactly `https://agentcore-grokbot.4axe.com/mcp` (approved Cloudflare private tunnel) — not unprotected public marketing DNS and not MagicDNS `:8080`.
4. Cloud header is `x-bf-vk` = raw `BIFROST_MCP_VK_GROKBOT` (no Bearer prefix in the Grok UI value). Client ID empty. OAuth Connect not used.
5. Proof log `F:\AgentCore\runtime\bifrost\logs\bifrost-gateway.stdout.log` shows `Cursor/1.0.0` POST `/mcp` → 200.
6. Tools visible through the gateway include the ten `agentcore_memory-*` tools for the grokbot profile.
7. No Swarm, project-router, Bifrost admin, or raw OpenRouter tools appear.
8. Primary Bot can `session_open` / `retrieve_context` on an enrolled project (`agentcore-control-plane` or `postgresql18-control-plane`) without cross-writing the other key.
9. Specialist Bots that must not use AgentCore have the server disabled.
10. (Standing backup 1B) With Cursor unavailable, primary Bot can follow `BIFROST_STANDING_BACKUP.md`, run `Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1 -Action Status` without errors, and still passes checks 1–7 without Grokbot MCP profile widening.
