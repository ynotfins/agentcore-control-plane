# ChatGPT Secure MCP Tunnel

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`  
**Updated:** 2026-07-24  

## Architecture

```
ChatGPT → Secure MCP Tunnel → compat proxy (18081) → Bifrost (8080) → agentcore_memory, router, arabold, skills_hub
```

## Components

### 1. Bifrost Gateway
- Endpoint: `http://127.0.0.1:8080`
- Scheduled task: `\AgentCore\AgentCore-Bifrost-Gateway`

### 2. Compatibility Proxy
- Config: `C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs`
- Listens: `127.0.0.1:18081`
- Path allowlist: `/mcp`, `/.well-known/oauth-protected-resource*`, `/healthz`, `/readyz`
- Denied paths: `/api/*`, `/workspace/*`, `/logs*`, `/admin*`, `/dashboard*`, `/v1/*`
- Start: `node C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs`

### 3. Tunnel Client
- Config: `C:\Users\ynotf\.config\tunnel-client\agentcore-gateway.yaml`
- Uses: `env:BIFROST_MCP_AUTHORIZATION` for MCP auth header, `env:CONTROL_PLANE_API_KEY` for tunnel auth
- Admin: `http://127.0.0.1:18080`

## ChatGPT VK Profile

The ChatGPT VK (`vk-agentcore-chatgpt`) exposes:

**Read tools:**
- `agentcore_memory`: memory_status, startup_context, retrieve_context, expand_source, docs_search, build_handoff, session_open, append_event, session_close
- `agentcore_project_router`: project_list, project_status, project_activate
- `arabold_docs`: search_docs, fetch_url, list_libraries, find_version, get_job_info
- `skills_hub`: search_skills, get_skill_detail

**Excluded:** project_clear, filesystem, shell, database admin, Bifrost admin, Firebase, Sheets, Swarm

## Operator Actions Required

1. Generate ChatGPT VK token:
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(60))"
   ```
2. Set env var:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("BIFROST_MCP_VK_CHATGPT", "<token>", "User")
   ```
3. Add chatgpt VK to config.json (see renderers/bifrost/config.json - chatgpt VK definition is commented/removed pending env var)
4. Restart Bifrost
5. Start compat proxy (persistent lifecycle TBD)
6. Verify tunnel client connects

## Security Notes

- The compat proxy only forwards `/mcp` and well-known paths to Bifrost
- Dashboard paths (`/api/*`, `/ui/*`) are DENIED
- LLM inference endpoints (`/v1/*`) are DENIED
- The Bifrost bearer token is injected by the compat proxy and is NOT exposed to ChatGPT
- ChatGPT profile has no LLM provider_configs (inference is not exposed)
