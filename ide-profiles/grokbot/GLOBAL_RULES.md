# Grok Bot — AgentCore global rules (derived summary)

Canonical semantics live in `contracts/global-agent-policy.yaml`. Grok Bot is **Trust Class A** with dedicated key `BIFROST_MCP_VK_GROKBOT`.

Hard rules for every Bot on this account:

1. One MCP front door: `agentcore-gateway` only.
2. Prefer local ChaosCentral storage, database, and memory. Use cloud or Docker only when local cannot meet the need and benefits clearly outweigh cost/risk.
3. AgentCore architecture authority: `D:\github\agentcore-control-plane`. Database control plane: `D:\postgreSQL18-control-plane` (enrolled; not merged). Dual workspace: `D:\github\agentcore-control-plane\agentcore-and-postgresql18.code-workspace`.
4. Continuity = one gateway + `agentcore-memory` + exact enrolled `project_key` for the active write root. Never cross-write the other plane’s key.
5. Swarm / `H:` remains foreign. Neutral SwarmRecall only via server-side `agentcore-memory`.
6. Cursor is sole **primary** for the Bifrost MCP contract plane when Cursor is available. Grok Bot is **standing backup** (operator decision 1B) when the operator declares Cursor unavailable or Cursor IDE is not usable — same bounded scope as `governance/proposals/2026-11-09-grokbot-standing-bifrost-backup.md` (enrolled control-plane repos, Bifrost contracts/renderers/ops); not dual-primary; Stage B remains Cursor-only.
7. Secrets stay in Windows User env / Vault / secure secret cards — never ordinary chat.
8. Automations that open visible consoles must be fixed to Hidden for AgentCore/NFA/OmniRoute; keep required SwarmClaw ecosystem startups. Do not claim Grokbot automation ownership — Paperclip inventory recording is separate.
9. Primary Bot (Chief of Staff) coordinates specialists and enforces these rules.
10. Documentation reconciliation via docs-guardian: after any material change to SQL, API/RPC contracts, generated clients, config/env, design tokens, authority-bundle files, **`MASTER_CONFIG_AND_PROMPT.md`**, **`ide-profiles/**`**, or **`contracts/agentcore-gateway-client.json`**, invoke docs-guardian (`run_in_background:false`) before claiming the task complete. Governed/locked docs still need AUTH + documentation maintainer path. Canonical: `global-subagents/docs-guardian.md`.
