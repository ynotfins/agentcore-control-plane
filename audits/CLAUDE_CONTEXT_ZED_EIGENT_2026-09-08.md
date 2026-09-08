# Claude Context MCP — Zed + Eigent intake — 2026-09-08

## Summary
Integrated `@zilliz/claude-context-mcp` (not `@zilliztech/claude-context`) into Zed and Eigent on Windows using User-scope environment variables only.

## Verified
- Node/npm present; global install `@zilliz/claude-context-mcp@0.1.15`
- User EVs present (values not recorded): OPENAI_API_KEY, MILVUS_TOKEN, MILVUS_ADDRESS, OPENAI_BASE_URL
- Live paths: `AppData\Roaming\Zed\settings.json`, `.eigent\mcp.json`
- Launcher: `C:\Users\ynotf\.agentcore\claude-context-mcp-launch.cmd` (EV pull at runtime)

## Repo artifacts
- `scripts/claude-context/*`

## Security
No API keys written into IDE JSON. Existing AgentCore gateway Authorization bearer in live Zed/Eigent configs remains legacy drift for a separate cleanup.

## Indexing attempt
- MCP server process started and loaded User EVs (OPENAI_API_KEY/MILVUS present).
- Launcher CALL-label defect fixed (inline EV load).
- `index_codebase` blocked: DNS NXDOMAIN for the current `MILVUS_ADDRESS` User EV host (Zilliz Cloud endpoint not resolvable on this LAN DNS).
- Operator action: correct `MILVUS_ADDRESS` (or rely on token auto-resolve), then re-run `node scripts/claude-context/index-codebase.mjs D:\github\agentcore-control-plane`.
