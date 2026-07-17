# OpenClaw — Self-Cleanup Prompt

**Superseded for normal non-Swarm IDE setup (2026-07-14):** Use install-agentcore-gateway-in-ide.md or the embedded prompt in MASTER_CONFIG_AND_PROMPT.md. This file is retained only as historical/remediation reference for older direct-server or Swarm rollout cleanup. Do not use it to create a normal IDE baseline.

> Paste into OpenClaw/ClawX. Edits ONLY `~/.openclaw/openclaw.json` (`mcp.servers`) + OpenClaw skills/rules. Do not print secrets.

Reconcile to governed renderer `renderers/openclaw.openclaw.fragment.json` in `D:\github\agentcore-control-plane`. Back up `openclaw.json` first.

FIX rogue Swarm entries:

- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken `.agentcore\mcp-wrappers\swarmvault-mcp.ps1`).

KEEP the user-approved `eye2byte` exception. ENSURE baseline from the governed renderer: arabold-docs, artiforge, eye2byte, filesystem, obsidian-vault, playwright, sequential-thinking, serena, swarmrecall, swarmvault. Serena must use the installed `serena.exe` launcher with `start-mcp-server --transport stdio --context ide`; do not use git `uvx` or `--context ide-assistant`. Do not add `global-memory-gateway` unless the current source renderer explicitly contains it.
SECRET: `gateway.auth.token` is a literal — migrate to a Windows env var reference; do not print it. No `.env`.
REMOVE if present: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Preserve gateway/session state. Verify MCP discovery; restart; report active servers + swarmvault launch proof. Concise change summary.
