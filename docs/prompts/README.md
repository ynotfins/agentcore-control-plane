# AgentCore IDE Setup Prompts

Current non-Swarm IDE baseline is the native Bifrost gateway:

```text
agentcore-gateway -> http://127.0.0.1:8080/mcp
Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
```

Use the gateway install prompt for all current Cursor, Codex, Claude, MiniMax, Mavis,
Antigravity, and Open Interpreter setup:

- `install-agentcore-gateway-in-ide.md`

The same prompt is embedded in `MASTER_CONFIG_AND_PROMPT.md` so new agents can configure an IDE from one root guide.

## Current Rules

1. Back up the live IDE config before any change.
2. Preserve model, auth, sandbox, context, profile, theme, and unrelated app settings.
3. Add only `agentcore-gateway` as the AgentCore non-Swarm MCP baseline.
4. Do not paste direct `depwire`, `serena`, `arabold-docs`, `tentra`, `filesystem`, or other upstream blocks into each IDE.
5. For Cursor, do not keep `MCP_DOCKER` unless the operator explicitly approves a documented unique-capability exception.
6. For Codex, use `bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"`; `http_headers` is static, and the 300-second timeout maps to `startup_timeout_sec` plus `tool_timeout_sec`.
7. Keep SwarmRecall, SwarmVault, and SwarmClaw separate from non-Swarm IDE baselines.
8. Never print secrets, create `.env` files, or commit live secret-bearing configs.
9. Validate Bifrost runtime first with `ops\bifrost\Test-AgentCoreBifrostGateway.ps1`, then validate IDE discovery.

## Historical Cleanup Prompts

The `*-cleanup-prompt.md` files were written for older direct-server or Swarm rollout remediation.
They are rollback/remediation references only unless updated by current authority. For normal setup,
use `install-agentcore-gateway-in-ide.md`.
