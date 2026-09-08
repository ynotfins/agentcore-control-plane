# Claude Context MCP — Zed + Eigent (Windows)

## Correct package
`@zilliz/claude-context-mcp` (npm). `@zilliztech/claude-context` does **not** exist on the registry.

## Required Windows User EVs
- `OPENAI_API_KEY` (required)
- `MILVUS_TOKEN` (required)
- `MILVUS_ADDRESS` (optional when Zilliz personal key auto-resolves)
- `OPENAI_BASE_URL` / `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` (optional)

Do **not** put secret values in IDE JSON. Prefer the EV-pulling launcher.

## Live paths
- Zed: `C:\Users\ynotf\AppData\Roaming\Zed\settings.json` → `context_servers`
- Eigent: `C:\Users\ynotf\.eigent\mcp.json` → `mcpServers`
- Launcher: `C:\Users\ynotf\.agentcore\claude-context-mcp-launch.cmd`

## Apply
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\scripts\claude-context\apply-live-configs.ps1
```

## Index
```powershell
node D:\github\agentcore-control-plane\scripts\claude-context\index-codebase.mjs D:\github\agentcore-control-plane
```
