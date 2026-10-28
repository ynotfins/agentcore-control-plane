# Cursor Open Design MCP exception

Date: 2026-10-26
Approval: AUTH-2026-10-26-OPEN-DESIGN-ENROLLMENT

## Exception

Cursor may run one host-native companion named `open-design` beside `agentcore-gateway`.

## Parity gap

Open Design product MCP exposes the live desktop project. Official docs require the in-app generated absolute launcher. Bifrost cannot host that session-bound stdio server without making the desktop a gateway upstream.

## Scope

- Cursor only
- stdio via generated `Open Design.exe` + `ELECTRON_RUN_AS_NODE` + `daemon-cli.mjs mcp`
- Design-project tools only
- Not AgentCore memory, PG18, Swarm, OpenRouter MCP, or filesystem roots

## Rollback

Restore `C:\Users\ynotf\.cursor\mcp.json` from `C:\Users\ynotf\.cursor\mcp.json.bak-opend-design-20261026` or remove the `open-design` key only.

## Live attach

Attached 2026-10-26. `agentcore-gateway` left unchanged (`http://127.0.0.1:8080/mcp`, env bearer). Desktop must stay running for the companion to work.
