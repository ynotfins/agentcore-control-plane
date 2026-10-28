# ChatGPT Secure MCP Tunnel

**Authority:** `contracts/bifrost-upstream-mcp-registry.json` (profile detail in `renderers/bifrost/config.json` → `vk-agentcore-chatgpt`)  
**Updated:** 2026-10-19  

## Architecture

```
ChatGPT → OpenAI tunnel control plane (api.openai.com)
       → tunnel-client admin :18080
       → compat proxy :18081
       → Bifrost :8080
       → narrow ChatGPT VK tools
```

## Components

### 1. Bifrost Gateway

- Endpoint: `http://127.0.0.1:8080`
- Scheduled task: `\AgentCore\AgentCore-Bifrost-Gateway`

### 2. Compatibility proxy

- **Live path:** `C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs`
- **Ops mirror:** `F:\AgentCore\runtime\bifrost\wrappers\agentcore-mcp-compat-proxy.cjs`
- **Repo updater:** `scripts/bifrost/update_compat_proxy.py` (writes the live `.config` file)
- Listens: `127.0.0.1:18081`
- Upstream: `http://127.0.0.1:8080` (injects ChatGPT VK via `env:BIFROST_MCP_VK_CHATGPT`; bearer not exposed to ChatGPT)
- Path allowlist: `/mcp`, `/.well-known/oauth-protected-resource*`, `/healthz`, `/readyz`
- Denied prefixes: `/api/*`, `/workspace/*`, `/logs*`, `/admin*`, `/dashboard*`, `/v1/*`, `/ui/*`, `/internal/*`
- Start: `node C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs`

**2026-10-19 repair:** upstream socket errors can no longer call `writeHead` after headers are sent or crash the process (`failUpstream` + `headersSent` / `writableEnded` guards).

**Rollback copies:**

- `C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs.bak-20261019-163200`
- `.agentcore/rollback/20261019-163200-chatgpt-compat-proxy/agentcore-mcp-compat-proxy.cjs.before`

### 3. Tunnel client

- Config: `C:\Users\ynotf\.config\tunnel-client\agentcore-gateway.yaml`
- Run: `C:\Users\ynotf\AppData\Local\OpenAI\tunnel-client\tunnel-client.exe run --config C:\Users\ynotf\.config\tunnel-client\agentcore-gateway.yaml`
- Uses `env:BIFROST_MCP_AUTHORIZATION` for MCP auth header and `env:CONTROL_PLANE_API_KEY` for tunnel auth (Windows User scope; do not commit values)
- Admin: `http://127.0.0.1:18080` (`/healthz`, `/readyz`)

## ChatGPT VK profile (runtime projection)

Narrow read-focused surface per `renderers/bifrost/config.json` (`vk-agentcore-chatgpt`):

| Upstream | Tools |
| --- | --- |
| `agentcore_memory` | `memory_status`, `startup_context`, `retrieve_context`, `expand_source`, `docs_search`, `session_open`, `append_event`, `build_handoff`, `session_close` |
| `arabold_docs` | `search_docs`, `fetch_url`, `list_libraries`, `find_version`, `get_job_info` |
| `sequential_thinking` | `sequentialthinking` |
| `skills_hub` | `search_skills`, `get_skill_detail`, `list_installed_skills` |

**Excluded:** machine-global project-router mutation, filesystem, shell, database admin, Bifrost admin, Firebase, Sheets, Swarm, LLM inference (`provider_configs` / `/v1/*`).

**Known surface drift (not fixed by 2026-10-19 proxy repair):** live `tools/list` through the tunnel may show Bifrost Code Mode meta-tools (`listToolFiles`, `readToolFile`, `getToolDocs`, `executeToolCode`) while `skills_hub` tools may be absent. Treat renderer VK config as authority; investigate Bifrost exposure separately if ChatGPT missing expected tools.

## Start order

1. Bifrost listening on `:8080` (gateway task or equivalent).
2. Compat proxy on `:18081`.
3. Tunnel client **once** (admin `:18080`).

## Operator checks

Apply/render VK if contracts changed: `scripts/bifrost/render_bifrost_config.py`, then restart Bifrost. Refresh proxy from repo if needed: `python scripts/bifrost/update_compat_proxy.py`.

**Verified local (2026-10-19):**

- `:18081/healthz` OK
- ChatGPT-profile `tools/list` via `:18081` includes `arabold_docs` (`list_libraries`, `search_docs`) and `sequentialthinking`
- `list_libraries` through `:18081` returned entries including `bifrost`, `openai`, `sequential-thinking`
- Tunnel admin `:18080` `/healthz` and `/readyz` → 200
- Tunnel client started with MCP session initialized
- No real HTTP 429 in local tunnel start log (hex/request IDs may contain substring `429` — not a rate limit by itself)

## Residual / governance

- Compat proxy and tunnel client still lack a **governed scheduled-task lifecycle owner** (same open item as CONTEXT_BLOCK residual 4). Do not edit `CONTEXT_BLOCK.md` without operator `UNLOCK`.
- Independent verification backlog (`audits/bifrost/BIFROST_INDEPENDENT_VERIFICATION_REMEDIATION_2026-07-25.md`) may still apply to claims beyond this tunnel path; this runbook records only the 2026-10-19 local tunnel/proxy repair evidence above.

## Security notes

- Compat proxy forwards only allowlisted paths to Bifrost; dashboard and inference paths are denied.
- ChatGPT profile has no LLM `provider_configs`; inference is not exposed through this tunnel.
