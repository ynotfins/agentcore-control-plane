# Claude Context / Zilliz — Zoo Code, Devin, ZCode — 2026-09-08

## Summary
Added `@zilliz/claude-context-mcp` as a local stdio MCP named `claude-context` to:
- Zoo Code in Cursor: `%APPDATA%\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`
- Devin: `%APPDATA%\devin\mcp_config.json`
- ZCode: `%USERPROFILE%\.zcode\cli\config.json` (`mcp.servers`)

## Security
Launcher: `C:\Users\ynotf\.agentcore\claude-context-mcp-launch.cmd`
Required User EVs: `OPENAI_API_KEY`, `MILVUS_TOKEN` (optional `MILVUS_ADDRESS`)
No API keys written into IDE JSON.

## Notes
Zoo Code native Qdrant codebase indexing remains separate; Claude Context is an additional MCP tool surface.
Trust-A reconcile for ZCode updated to preserve `claude-context` when rewriting gateway enrollment.
