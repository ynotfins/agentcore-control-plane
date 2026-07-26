# Cherry Studio + new-api Integration Index

> **HISTORICAL / TASK-SPECIFIC REFERENCE ONLY — SUPERSEDED.** Pre-alignment Cherry Studio/new-api integration notes. Current Cherry Studio authority is `docs/operations/CHERRY_STUDIO_AGENTCORE.md` and `audits/CHERRY_TARGET_AGENT_REPAIR_2026-07-24.md`. Excluded from default ChatGPT Project Sources.

> Canonical AgentCore policy for the two local AI clients at
> `D:\github\cherry-studio` and `D:\github\new-api`. This document is
> the index; per-project details live in the `AGENTCORE.md` files in
> each repo.

Last updated: 2026-07-20

---

## Topology

```
                       +-----------------------------+
                       |  AgentCore-Bifrost-Gateway  |
                       |  http://127.0.0.1:8080/mcp  |
                       |  14 upstream MCP servers    |
                       |  155 tools (8 repomix)       |
                       +--------------+--------------+
                                      | Bearer BIFROST_MCP_VIRTUAL_KEY
                                      |
+-------------------+         +-------v--------+         +-------------------+
|  Cherry Studio    |         |                |         |    new-api        |
|  v1.9.12          +-------->+   This index   <---------+  QuantumNous      |
|  LDB-injected     |         |                |         |  Docker compose   |
|  7 providers +    |         |                |         |  Postgres + Redis |
|  agentcore-gw MCP |         |                |         |  3000 + new-api   |
+-------------------+         +----------------+         +-------------------+
        |                              |                            |
        | API keys from                |                            | API keys from
        | Windows User env             |                            | admin UI -> User env
        v                              v                            v
   MINIMAX_API_KEY               BIFROST_MCP_VIRTUAL_KEY      NEWAPI_API_KEY
   DEEPSEEK_API_KEY
   OPENAI_API_KEY
   ...
```

The two clients do **not** talk to each other directly. They share
secrets through Windows User environment variables and share the
Bifrost gateway for MCP.

---

## Files in scope

| Path | Role |
| --- | --- |
| `D:\github\cherry-studio\AGENTCORE.md` | Per-project policy + setup doc for Cherry Studio. |
| `D:\github\new-api\AGENTCORE.md` | Per-project policy + setup doc for new-api. |
| `D:\github\agentcore-control-plane\registry\bifrost-upstream-mcp-registry.json` | Source of truth for the 14 MCP servers Cherry sees through Bifrost. |
| `D:\github\agentcore-control-plane\renderers\gateway-clients\cherry-studio.json` | Canonical renderer used by Bifrost when the gateway client is "cherry-studio". |
| `D:\github\agentcore-control-plane\scripts\cherry\setup_cherry_providers.py` | Reads env vars, generates the import JSON. |
| `D:\github\agentcore-control-plane\scripts\cherry\inject_cherry_providers.js` | Writes the llm slice into Cherry's leveldb. |
| `D:\github\agentcore-control-plane\scripts\cherry\inject_cherry_mcp.js` | Writes the mcp slice into Cherry's leveldb. |
| `D:\github\new-api\.env.template` | Secret template for new-api. |
| `D:\github\new-api\docker-compose.yml` | Compose that reads from `.env`. |
| `D:\github\new-api\ops\Start-NewAPI.ps1` | PowerShell launcher. |
| `D:\github\new-api\ops\Stop-NewAPI.ps1` | PowerShell stopper. |
| `D:\github\agentcore-control-plane\docs\MCP_SERVER_CONFIGURATION_REFERENCE.md` | Reference for the 14 MCP servers. |
| `D:\github\agentcore-control-plane\docs\bifrost\UNIFIED_GATEWAY_SETUP.md` | Reference for the Bifrost gateway. |
| `D:\github\agentcore-control-plane\docs\agent_integration_boundaries.md` | Privacy zones and integration boundaries. |

---

## Canonical env-var inventory (presence only)

| Env var | Required by | Status |
| --- | --- | --- |
| `MINIMAX_API_KEY` | Cherry (PRIMARY) | **Present** |
| `DEEPSEEK_API_KEY` | Cherry (SECONDARY) | **Present** |
| `OPENAI_API_KEY` | Cherry (optional) | **Present** |
| `OPENROUTER_API_KEY` | Cherry (optional) | **Present** |
| `GEMINI_API_KEY` | Cherry (optional) | **Present** |
| `XAI_API_KEY` | Cherry (grok, optional) | **Present** |
| `GITHUB_TOKEN` | Cherry (GitHub Models, optional) | **Present** |
| `BIFROST_MCP_VIRTUAL_KEY` | Bifrost gateway MCP | **Present** |
| `NEWAPI_API_KEY` | new-api (set after admin user is created) | **Missing (set after Start-NewAPI.ps1 + admin bootstrap)** |
| `ANTHROPIC_API_KEY` | Cherry (optional) | Missing |
| `GOOGLE_API_KEY` | Cherry (optional) | Missing |
| `GROQ_API_KEY` | Cherry (optional) | Missing |
| `PERPLEXITY_API_KEY` | Cherry (optional) | Missing |
| `MISTRAL_API_KEY` | Cherry (optional) | Missing |
| `TOGETHER_API_KEY` | Cherry (optional) | Missing |
| `FIREWORKS_API_KEY` | Cherry (optional) | Missing |
| `NVIDIA_API_KEY` | Cherry (optional) | Missing |
| `JINA_API_KEY` | Cherry (optional) | Missing |
| `FAL_KEY` / `REPLICATE_API_TOKEN` | Cherry (optional) | Missing |
| `SUPABASE_*` | Not in this integration | Missing |
| `TWILIO_AUTH_TOKEN` | Not in this integration | Missing |
| `VERCEL_TOKEN` | Not in this integration | Missing |
| `FALCON_API_KEY` | Not in this integration | Missing |

The injector silently skips providers whose env var is missing; the
import JSON is always built from the set that is present.

---

## Default model routing (agentcore policy)

| Slot | Provider:Model | Why |
| --- | --- | --- |
| `defaultModel` | `minimax:MiniMax-M3` | Primary chat. |
| `topicNamingModel` | `minimax:MiniMax-M2.7-highspeed` | Cheap, fast naming. |
| `translateModel` | `minimax:MiniMax-M3` | Primary, accurate. |
| `quickModel` | `deepseek:deepseek-v4-flash` | Cheap, fast. |
| Secondary (dropdown) | `deepseek:deepseek-v4-pro` | User-requested V4 Pro. |
| (Optional aggregator) | `new-api:<any-channel-model>` | Once new-api is up. |

The script writes these defaults to the `llm` slice in
`persist:cherry-studio`. The user can change any of them in the UI
afterwards; the next injector run preserves UI changes for
non-catalog providers and rewrites catalog provider defaults to match.

---

## MCP server policy (agentcore policy)

| Decision | Rationale |
| --- | --- |
| All MCP traffic goes through `agentcore-gateway` | One place to audit, rate-limit, log, and rotate keys. |
| User does not add direct MCP servers in Cherry | Avoids the 14+ duplicate connections Cherry would otherwise show. |
| Bifrost holds the `BIFROST_MCP_VIRTUAL_KEY` bearer | Cherry never sees upstream keys. |
| Cherry's MCP slice is LDB-injected, not UI-clicked | The Cherry UI does not support adding an `agentcore-gateway`-shaped streamableHttp server in a single click. |

The 14 enabled upstream MCP servers and the capability profile that
gates them are documented in
`docs/MCP_SERVER_CONFIGURATION_REFERENCE.md` and
`docs/bifrost/CAPABILITY_PROFILES.md`.

---

## RAG and memory policy

| Concern | Decision |
| --- | --- |
| Knowledge base / RAG | **Native Cherry RAG enabled.** `agents.db` lives under `%APPDATA%\CherryStudio\Data`. |
| Long-term memory | **Native Cherry memory disabled.** Memory is delegated to the AgentCore context fabric (see `.context-fabric` in the control plane). |
| KB sync from new-api | **Not in scope.** new-api is a chat gateway, not a vector store. RAG corpora stay in Cherry's `agents.db`. |

---

## End-to-end setup order (single user, single host)

```powershell
# 0. Make sure Windows User env has:
#    MINIMAX_API_KEY, DEEPSEEK_API_KEY, BIFROST_MCP_VIRTUAL_KEY
#    (and any of OPENAI_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY,
#     XAI_API_KEY, GITHUB_TOKEN you want enabled).
#    Run `restart_after_env_changes.md` to refresh shells.

# 1. Bring up the Bifrost gateway (it is the MCP server for Cherry).
#    (Use the ops script the control plane already has, or start
#    AgentCore-Bifrost-Gateway in Docker / as a service.)
curl -sS http://127.0.0.1:8080/healthz
# expected: {"status":"ok",...}

# 2. Generate + inject Cherry providers and the agentcore-gateway MCP.
#    Cherry Studio MUST be fully quit before this.
Get-Process | Where-Object { $_.ProcessName -eq 'Cherry Studio' } | Stop-Process -Force
Set-Location D:\github\agentcore-control-plane\scripts\cherry
uv run setup_cherry_providers.py --print-models
Set-Location D:\github\agentcore-control-plane\scripts\cherry\_node_workspace
node ..\inject_cherry_providers.js --confirm
node ..\inject_cherry_mcp.js --confirm

# 3. Bring up new-api.
Set-Location D:\github\new-api
pwsh -NoProfile -File ops\Start-NewAPI.ps1
# Open http://127.0.0.1:3000 and register the first admin user.

# 4. In the new-api admin UI, add upstream channels (minimax,
#    deepseek, etc.) using the same keys you have in Windows User
#    env. Create a new-api token. Copy it.

# 5. Put the new-api token in Windows User env.
[System.Environment]::SetEnvironmentVariable(
    'NEWAPI_API_KEY', '<token-from-new-api-admin>', 'User')

# 6. Re-run the Cherry provider generator + injector to add the
#    new-api provider. Then restart Cherry Studio.
Set-Location D:\github\agentcore-control-plane\scripts\cherry
uv run setup_cherry_providers.py --print-models
Set-Location D:\github\agentcore-control-plane\scripts\cherry\_node_workspace
node ..\inject_cherry_providers.js --confirm
```

After step 6, both clients are fully integrated with the AgentCore
gateway topology and each other (via shared env-var keys).

---

## Verification matrix

| What | Where to check | Expected |
| --- | --- | --- |
| Bifrost gateway health | `curl http://127.0.0.1:8080/healthz` | `{"status":"ok",...}` |
| Bifrost tools count | `curl -X POST http://127.0.0.1:8080/mcp -H "Authorization: Bearer $env:BIFROST_MCP_VIRTUAL_KEY" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'` | 155+ tools, 8 from `repomix` |
| Cherry providers | Settings -> Providers | 7+ providers, minimax enabled with key, default `minimax:MiniMax-M3` |
| Cherry MCP | Settings -> MCP Servers | `agentcore-gateway` listed, `streamableHttp`, `connected` |
| new-api status | `curl http://127.0.0.1:3000/api/status` | `{"success":true,...}` |
| new-api channels | Admin UI -> Channels | At least one upstream enabled |
| Cherry -> new-api | Settings -> Providers -> New API | Listed, disabled, models pulled at runtime |

---

## Rollback

| Component | Rollback command |
| --- | --- |
| Cherry providers | `node ..\inject_cherry_providers.js --rollback` (uses most recent `E:\AgentCore-Backups\cherry-providers-*`) |
| Cherry MCP | `node ..\inject_cherry_mcp.js --rollback` (uses most recent `E:\AgentCore-Backups\cherry-mcp-*`) |
| new-api | `pwsh -NoProfile -File D:\github\new-api\ops\Stop-NewAPI.ps1` (-RemoveVolumes for a full reset) |
| Bifrost | `pwsh -NoProfile -File <path-to-bifrost-ops>\Stop-Bifrost.ps1` (see `docs/bifrost/UNIFIED_GATEWAY_SETUP.md`) |

---

## Future work (not in this iteration)

- Add an automatic pre-flight check (Bifrost up? Cherry quit?
  new-api up?) that refuses the injector if any of the three is in
  the wrong state.
- Wire `new-api`'s `error_log` into the AgentCore audit pipeline
  (`D:\github\agentcore-control-plane\audits\`).
- Add a `validate_end_to_end.py` that runs after every injector run
  and writes a report to
  `D:\github\agentcore-control-plane\reports\cherry-newapi-e2e-<ts>.json`.
- Add a one-click "rotate all secrets" pass that:
  1. Re-generates `BIFROST_MCP_VIRTUAL_KEY`.
  2. Re-runs `Start-NewAPI.ps1 -RegenerateSecrets`.
  3. Re-enrolls Cherry with both new values.
