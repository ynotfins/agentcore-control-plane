# OpenClaw — Self-Cleanup Prompt

> Paste into OpenClaw/ClawX. Edits ONLY `~/.openclaw/openclaw.json` (`mcp.servers`) + OpenClaw skills/rules. Do not print secrets.

Reconcile to governed renderer `renderers/openclaw.openclaw.fragment.json` in `D:\github\agentcore-control-plane`. Back up `openclaw.json` first.

FIX rogue Swarm entries:
- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken `.agentcore\mcp-wrappers\swarmvault-mcp.ps1`).

KEEP the user-approved `eye2byte` exception. ENSURE baseline: arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena, swarmrecall, swarmvault (+ eye2byte). (cursor-agent-mcp/context-fabric/mcp-debugger staged.)
SECRET: `gateway.auth.token` is a literal — migrate to a Windows env var reference; do not print it. No `.env`.
REMOVE if present: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Preserve gateway/session state. Verify MCP discovery; restart; report active servers + swarmvault launch proof. Concise change summary.
