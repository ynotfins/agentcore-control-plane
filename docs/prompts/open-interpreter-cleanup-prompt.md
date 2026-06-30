# Open Interpreter — Self-Cleanup Prompt

> Paste into Open Interpreter. Edits ONLY `AppData\Roaming\interpreter\config.json` (`mcpServers`). Do not print secrets. Open Interpreter is a deliberately minimal, high-risk surface — keep it tight.

Reconcile to governed renderer `renderers/open-interpreter.config.fragment.json` in `D:\github\agentcore-control-plane`. **Preserve all unrelated top-level config keys and profile/auth state.** Back up `config.json` first.

FIX rogue Swarm entries (the live config got them; normalize to governed launch):
- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken wrapper path).

ENSURE the governed OI set: arabold-docs, artiforge, global-memory-gateway, swarmrecall, swarmvault.
SECRET: `authToken` / `refreshToken` are live profile/auth literals — PRESERVE them (do not delete) but, if your tooling supports it, migrate to Windows env var references; never print values. No `.env`.
REMOVE if present: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Verify MCP discovery; restart; report active servers + swarmvault launch proof; confirm auth/profile preserved. Concise change summary.
