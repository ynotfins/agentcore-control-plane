# Grok Bot — AgentCore global rules (derived summary)

Canonical semantics live in `contracts/global-agent-policy.yaml`. Grok Bot is **Trust Class A** with dedicated key `BIFROST_MCP_VK_GROKBOT`.

Hard rules for every Bot on this account:

1. One MCP front door: `agentcore-gateway` only.
2. Prefer local ChaosCentral storage, database, and memory. Use cloud or Docker only when local cannot meet the need and benefits clearly outweigh cost/risk.
3. AgentCore architecture authority: `D:\github\agentcore-control-plane`. Database control plane: `D:\postgreSQL18-control-plane` (enrolled; not merged).
4. Swarm / `H:` remains foreign. Neutral SwarmRecall only via server-side `agentcore-memory`.
5. Secrets stay in Windows User env / Vault / secure secret cards — never ordinary chat.
6. Cursor owns Bifrost MCP contract edits when available; temporary delegation requires operator declaration.
7. Automations that open visible consoles must be fixed to Hidden; keep Bifrost and required NFA health watchdogs running.
8. Primary Bot (Chief of Staff) coordinates specialists and enforces these rules.
