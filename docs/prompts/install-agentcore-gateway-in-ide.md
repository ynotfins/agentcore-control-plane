# Install AgentCore Gateway in an IDE

Reusable operator/agent prompt for **any** supported non-Swarm IDE on this PC.

**Authority:** `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `contracts/agentcore-gateway-client.json`, `docs/bifrost/UNIFIED_GATEWAY_SETUP.md`, `renderers/gateway-clients/<ide>.json`
**Endpoint:** `http://127.0.0.1:8080/mcp`
**Auth env:** `BIFROST_MCP_VIRTUAL_KEY` (never print the value)
**Display name in IDEs:** `agentcore-gateway` (not `bifrost`)

---

## Prompt (copy into an IDE agent)

```text
Install the AgentCore Bifrost MCP gateway for this IDE.

Authority:
D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
D:\github\agentcore-control-plane\DOC_AUTHORITY.md
D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json
D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json
D:\github\agentcore-control-plane\docs\bifrost\UNIFIED_GATEWAY_SETUP.md
D:\github\agentcore-control-plane\docs\prompts\install-agentcore-gateway-in-ide.md

Goal:
Use exactly one non-Swarm AgentCore MCP baseline entry named agentcore-gateway:
http://127.0.0.1:8080/mcp
Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}

Runtime requirement:
Before editing the IDE config, prove the native Bifrost Gateway is running persistently:
- scheduled task: \AgentCore\AgentCore-Bifrost-Gateway
- app dir: H:\AgentRuntime\bifrost
- bind: 127.0.0.1:8080 only
- health: GET http://127.0.0.1:8080/health returns 200
- direct MCP initialize, initialized notification, tools/list, and one safe read-only tool call succeed

Safety rules:
- Back up the live IDE config before any change and record SHA-256.
- Preserve model, auth, account, sandbox, context, profile, theme, and non-MCP app settings.
- Do not print or commit secret values.
- Do not create .env files.
- Do not touch SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, or ClawX.
- Do not paste the full upstream registry into the IDE.

Steps:
1. Identify the real active MCP config path and schema for this IDE from contracts\agentcore-gateway-client.json.
2. Back up the config outside Git.
3. Remove direct duplicate baseline MCP entries now served by Bifrost.
4. For Cursor, remove MCP_DOCKER unless the operator explicitly approves a documented unique-capability exception.
5. Add or merge only agentcore-gateway using the schema-correct renderer for this IDE.
6. Use Windows User env BIFROST_MCP_VIRTUAL_KEY without printing it.
   For Codex, use bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY" plus startup_timeout_sec = 300 and tool_timeout_sec = 300; do not put the env placeholder in static http_headers.
7. If env-header expansion is unsupported, materialize the secret only into the app-owned live config as a last resort; never commit or report it.
8. Validate JSON/TOML syntax.
9. Fully restart/reload the IDE so environment references are visible.
10. Confirm the IDE shows agentcore-gateway connected/ready.
11. Confirm tools/list includes expected prefixes such as arabold_docs, depwire, tentra, sequential_thinking, context_fabric, filesystem, playwright, cursor_agent_mcp, agentcore_memory, and agentcore_project_router.
12. Confirm Swarm, raw database, whole-drive filesystem, and Bifrost admin tools are absent.
13. Activate the project through agentcore_project_router before project-scoped work.
14. Self-enroll through agentcore_memory-session_open with verified client, repository/worktree/Git, selected provider/model, and named context-profile identity. Do not lower the IDE model's configured hard context window.
15. Call agentcore_memory-startup_context with that profile and confirm the reported hard limit matches the selected capability; 4096 is acceptance/legacy-only.
16. Before any tool execution, append the original visible operator prompt verbatim (after secret redaction) using a deterministic idempotency key via agentcore_memory-append_event.
17. Smoke-test agentcore_memory-retrieve_context recovery pagination and agentcore_memory-expand_source before asking the operator to repeat missing history.
18. Call agentcore_memory-build_handoff and verify projection revisions are present.
19. Call agentcore_memory-session_close to confirm clean close behavior (ended_at set).
20. Verify resume: re-open with the same session_key and confirm the original session_id is returned and prior events are accessible.
21. Verify project isolation: a different project_key must not return events from the first project.
22. Verify the tool surface is exactly ten agentcore-memory tools: memory_status, startup_context, retrieve_context, append_event, propose_fact, expand_source, session_open, session_close, build_handoff, docs_search. Any deviation is a validation failure.
23. Record sanitized evidence: IDE name, config path, backup path, hashes, discovery/tool count, context profile, recovery result, resume result, isolation result, blockers, rollback.
24. Mark the IDE live_validated only after all lifecycle steps 14–22 pass with evidence. Do not claim live_validated from config inspection alone.

Canonical Cursor target:
C:\Users\ynotf\.cursor\mcp.json

Canonical Cursor JSON:
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      },
      "timeout": 300
    }
  }
}

Adding future MCP servers:
- Do not add new baseline MCP servers separately to every IDE.
- Add once to contracts\bifrost-upstream-mcp-registry.json.
- Pin version, index exact-version official docs with Arabold, classify scope, define transport/command/env/timeout/health/write risk/rollback.
- Define allowed tools, denied tools, and capability profiles.
- Render Bifrost config, validate schemas, restart Bifrost, test initialize/tools/list and one safe call.
- Update .agentcore/docs/DOCS_INDEX.md and evidence.
- Leave IDE configs unchanged unless the single gateway connection itself changes.

Tool suppression:
- Disable an upstream with enabled=false.
- Use named tools_to_execute allowlists.
- Use an empty allowlist for no tools.
- Use narrower virtual-key profiles.
- Avoid broad wildcard grants unless documented in the registry.

Do not claim completion from config files alone. Direct MCP and IDE discovery must pass.
```
