# NEXT PHASE — Paperclip MAXIMIZER (bounded handoff)

**Do not execute Maximizer setup inside the dual-plane continuity/docs pass.** This file is the handoff only.

## Goal

Stand up Paperclip MAXIMIZER so AgentCore can inventory and maximize local automations without stealing ownership from existing owners (especially Grokbot / SwarmClaw).

## Hard boundaries

1. Inventory only first — no move/disable/reassign of scheduled tasks owned by Grokbot, SwarmClaw, or NFA product owners without a separate operator decision.
2. Paperclip local service remains `Paperclip-Local-3100` (Hidden). Do not recreate casually.
3. AgentCore owns AgentCore/NFA/OmniRoute silent-policy; Swarm startups stay.
4. Secrets stay in Windows User env only.
5. Dual control planes stay separate; Maximizer work uses `project_key=agentcore-control-plane` unless a dedicated enrolled path is created later.

## Acceptance for Maximizer phase

- [ ] Paperclip inventory lists AgentCore scheduled tasks + Startup items with owner tags
- [ ] Grokbot Cloudflare tunnel task tagged owned-by-AgentCore-ops / not Maximizer-owned
- [ ] SwarmClaw ecosystem startups tagged keep / foreign
- [ ] DailyDriftCheck tagged Disabled-legacy
- [ ] Maximizer runbook written under docs/operations (docs-guardian after)
- [ ] No tunnel recreate; no broad credential rotation

## Ready-to-paste operator prompt

```text
GOAL: Paperclip MAXIMIZER setup (inventory-first). Operator non-technical.

Context: Dual-plane continuity + Grok Cloudflare MCP docs are done. Do NOT rebuild Dual Multi-Workspaces. Do NOT recreate agentcore-grokbot tunnel. Do NOT disable Swarm startups. Do NOT take Grokbot automation ownership. DailyDriftCheck stays Disabled.

Scope: I:\LocalApps\Paperclip + AgentCore ops inventory only. Tag owners. Propose Maximizer policies; do not move tasks until operator approves a second phase.

AUTH: use documentation path for any governed docs. Never print secrets.
```
