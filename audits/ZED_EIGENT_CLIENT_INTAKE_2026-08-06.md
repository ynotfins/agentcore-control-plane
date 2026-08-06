# Zed and Eigent AgentCore Client Intake — 2026-08-06

**Scope:** Read-only capability and local-install verification followed by source-controlled profile enrollment. No live IDE MCP configuration was changed.

## Verified facts

| Client | Installed evidence | Rules / skills | MCP persistence | Current AgentCore status |
| --- | --- | --- | --- | --- |
| Zed | `Zed.exe` 1.13.2 under the user-local Programs root; process live | Windows personal `AGENTS.md`; global skills from `C:\Users\ynotf\.agents\skills` | `C:\Users\ynotf\AppData\Roaming\Zed\settings.json`, remote servers under `context_servers` | `awaiting_operator_import` |
| Eigent | `Eigent.exe` 1.0.2 under the user-local Programs root; process live | Native skills under `C:\Users\ynotf\.eigent\skills`; no always-on global rule file verified | `C:\Users\ynotf\.eigent\mcp.json`; standard `mcpServers` through CAMEL MCPToolkit | `awaiting_operator_import` |

Zed's live settings contained no `context_servers` entry during intake. Eigent's canonical `mcp.json` did not yet exist. Neither client is claimed as gateway-enrolled or native-memory validated.

## Primary documentation

- Zed MCP: <https://zed.dev/docs/ai/mcp>
- Zed Instructions: <https://zed.dev/docs/ai/instructions>
- Zed Skills: <https://zed.dev/docs/ai/skills>
- Eigent upstream: <https://github.com/eigent-ai/eigent>
- Eigent installed-source evidence: `resources/backend/app/service/mcp_config.py`, `resources/backend/app/service/skill_service.py`, and the bundled CAMEL `mcp_toolkit.py` under the installed application.

## Security and acceptance boundary

Both committed templates contain only a symbolic Windows environment-variable reference. Neither installed client has documented support for expanding that token in remote MCP headers. Any later live enrollment must take the value from the Windows User environment, materialize it only in the protected live client configuration, avoid printing it, create rollback evidence, restart or reload the client, and run the full native validation contract.

Configuration presence is not certification. Promotion beyond `awaiting_operator_import` requires client-native gateway discovery, exactly ten `agentcore-memory` tools in the ordinary profile, project isolation, signed lifecycle evidence where supported, fresh-task recovery, and persistence-after-restart proof.
