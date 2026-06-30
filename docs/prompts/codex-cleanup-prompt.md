# Codex — Self-Cleanup Prompt

> Paste into Codex. Edits ONLY Codex's own `~/.codex/config.toml` + AGENTS.md/hooks/skills. Do not print secrets.

Reconcile Codex MCP config to the AgentCore governed baseline. Source authority: `D:\github\agentcore-control-plane`.

Inspect: `C:\Users\ynotf\.codex\config.toml`, `C:\Users\ynotf\.codex\AGENTS.md`, hooks/skills. Back up `config.toml` first.

FIX the rogue Swarm entries to the governed launch:
- `[mcp_servers.swarmrecall]` → `command = "pwsh"`, `args = ["-NoProfile","-ExecutionPolicy","Bypass","-File","D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreSwarmRecall.ps1","-Mode","Mcp"]` (remove the raw node CLI form).
- `[mcp_servers.swarmvault]` → `command = "pwsh"`, `args = ["-NoProfile","-ExecutionPolicy","Bypass","-File","D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreSwarmVault.ps1","-Mode","Mcp"]` (replace the non-existent `.agentcore\mcp-wrappers\swarmvault-mcp.ps1`).

KEEP Codex extras (allowed): node_repl, codex-security, github, filesystem, playwright. ENSURE baseline: arabold-docs, serena, sequential-thinking, artiforge, global-memory-gateway, obsidian-vault, swarmrecall, swarmvault. (cursor-agent-mcp/context-fabric/mcp-debugger staged for next expansion.) Codex can enable/disable tools, so the server budget is allowed to exceed the bounded JSON-IDE surface.
SECRET: `experimental_bearer_token` is a literal — migrate to a Windows env var (`env_vars = [...]`); do not print the value. No `.env` files.
REMOVE if present: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). After editing: verify `codex mcp list --json` discovery; restart; report active servers + that swarmvault launches; confirm no secret printed. Concise change summary.
