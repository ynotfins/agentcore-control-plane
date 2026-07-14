# Open Interpreter — Self-Cleanup Prompt

**Superseded for normal non-Swarm IDE setup (2026-07-14):** Use install-agentcore-gateway-in-ide.md or the embedded prompt in MASTER_CONFIG_AND_PROMPT.md. This file is retained only as historical/remediation reference for older direct-server or Swarm rollout cleanup. Do not use it to create a normal IDE baseline.

> Paste into Open Interpreter. Edits ONLY `AppData\Roaming\interpreter\config.json` (`mcpServers`). Do not print secrets. Open Interpreter is a deliberately minimal, high-risk surface — keep it tight.

Reconcile to governed renderer `renderers/open-interpreter.config.fragment.json` in `D:\github\agentcore-control-plane`. **Preserve all unrelated top-level config keys and profile/auth state.** Back up `config.json` first.

FIX rogue Swarm entries (the live config got them; normalize to governed launch):

- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken wrapper path).

ENSURE the governed OI set: arabold-docs, artiforge, serena, swarmrecall, swarmvault. Serena must use the installed `serena.exe` launcher with `start-mcp-server --transport stdio --context ide`; do not use git `uvx` or `--context ide-assistant`. Do not add `global-memory-gateway` unless the current source renderer explicitly contains it.
SECRET: `authToken` / `refreshToken` are live profile/auth literals — PRESERVE them (do not delete) but, if your tooling supports it, migrate to Windows env var references; never print values. No `.env`.
REMOVE if present: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Verify MCP discovery; restart; report active servers + swarmvault launch proof; confirm auth/profile preserved. Concise change summary.
