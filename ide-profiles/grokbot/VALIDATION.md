# Validation — Grok Bot

Mark `live_validated` only when all pass:

1. Bifrost `GET /health` returns 200 on ChaosCentral.
2. Custom connector name is exactly `agentcore-gateway`.
3. Cloud connector URL is Tailscale MagicDNS or an approved private tunnel — not unprotected public marketing DNS.
4. Tools visible through the gateway include the ten `agentcore_memory-*` tools for the grokbot profile.
5. No Swarm, project-router, Bifrost admin, or raw OpenRouter tools appear.
6. Primary Bot can `session_open` / `retrieve_context` on an enrolled project (`agentcore-control-plane` or `postgresql18-control-plane`).
7. Specialist Bots that must not use AgentCore have the server disabled.
