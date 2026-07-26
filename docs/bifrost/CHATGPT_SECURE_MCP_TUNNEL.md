# ChatGPT Secure MCP Tunnel

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`  
**Updated:** 2026-07-25  

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

## ChatGPT VK Profile and Environment Status

- **Environment Variable:** `BIFROST_MCP_VK_CHATGPT` is set in Windows User scope (operator confirmed 2026-07-25).
- **Targeted Profile Scope:** Narrow read-focused surface:
  - `agentcore_memory`: memory_status, startup_context, retrieve_context, expand_source, docs_search, build_handoff, session_open, append_event, session_close
  - `agentcore_project_router`: project_list, project_status, project_activate
  - `arabold_docs`: search_docs, fetch_url, list_libraries, find_version, get_job_info
  - `skills_hub`: search_skills, get_skill_detail
- **Excluded:** project_clear, filesystem, shell, database admin, Bifrost admin, Firebase, Sheets, Swarm
- **Status Notice:** Full source/runtime/DB/dashboard parity and narrow-profile enforcement remain subject to targeted independent verification remediation (`audits/bifrost/BIFROST_INDEPENDENT_VERIFICATION_REMEDIATION_2026-07-25.md` pending execution). Do not claim independent verification or narrow profile parity is complete until the remediation audit passes and is committed.

## Operator Runbook

1. User env var `BIFROST_MCP_VK_CHATGPT`: created (verified present).
2. Apply narrow VK profile to `renderers/bifrost/config.json` and runtime `H:\AgentRuntime\bifrost\config.json`.
3. Restart Bifrost.
4. Start compat proxy (18081).
5. Verify tunnel client connects.
6. Refresh ChatGPT custom-app action snapshot only after remediation audit passes.

## Security Notes

- The compat proxy only forwards `/mcp` and well-known paths to Bifrost.
- Dashboard paths (`/api/*`, `/ui/*`, `/dashboard*`) are DENIED.
- LLM inference endpoints (`/v1/*`) are DENIED.
- The Bifrost bearer token is injected by the compat proxy and is NOT exposed to ChatGPT.
- ChatGPT profile has no LLM provider_configs (inference is not exposed).
