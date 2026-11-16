# Proposal + AUTH record: Grok Bot MCP Cloudflare live alignment

Date: 2026-11-08
Status: APPLY under operator binding decisions
AUTH id: `AUTH-2026-11-08-GROKBOT-MCP-CLOUDFLARE-LIVE`
Capability: `authority_maintainer` (Cursor sole primary for Bifrost MCP contract plane)

## Live facts

- Cloud MCP URL: `https://agentcore-grokbot.4axe.com/mcp`
- Task: `\AgentCore-Grokbot-Cloudflare-Tunnel` (Hidden)
- Header: `x-bf-vk` = raw `BIFROST_MCP_VK_GROKBOT` (no Bearer prefix in Grok UI)
- Client ID blank; no OAuth Connect
- Proof: `F:\AgentCore\runtime\bifrost\logs\bifrost-gateway.stdout.log` (`Cursor/1.0.0` POST `/mcp` → 200)

## Applied targets

Governed: MASTER_CONFIG_AND_PROMPT.md, contracts/agentcore-gateway-client.json, contracts/global-agent-policy.yaml
Profiles/ops/docs: ide-profiles/grokbot/*, Install-AgentCoreSilentAutomationPolicy.ps1, CAPABILITY_PROFILES.md, drift-ledger, drift_prevention, M8 registry, grokbot renderer, dual-plane continuity cookbook, postgresql18 AGENTS.md path fix

## Non-goals

No tunnel recreate; no Grokbot automation ownership; keep Swarm startups; DailyDriftCheck stays Disabled.
