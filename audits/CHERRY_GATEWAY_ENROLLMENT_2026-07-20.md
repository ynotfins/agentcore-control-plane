# Cherry Studio AgentCore Gateway Enrollment Evidence (2026-07-20)

**See also:** `BLUEPRINT.md` · `docs/operations/CHERRY_STUDIO_AGENTCORE.md` · `audits/CHERRY_RUNTIME_FAILURE_2026-07-20.md` · `audits/CHERRY_MEMORY_LIFECYCLE_2026-07-20.json` · `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` · `docs/operations/OPENROUTER_MCP.md`

**Version:** 1.9.12 (win|prod|packaged, official x64 setup)  
**AppData:** `%APPDATA%\CherryStudio`  
**Install (repaired):** `%LOCALAPPDATA%\Programs\Cherry Studio\Cherry Studio.exe`  
**Prior broken path:** `C:\Program Files\Cherry Studio` (ARM64 `registry.node` mixed into x64 host — removed)

## Status fields (do not collapse)

| Field | Status | Evidence |
| --- | --- | --- |
| configuration enrolled | PASS | LevelDB `agentcore-gateway` active @ `http://127.0.0.1:8080/mcp` timeout 300 |
| MCP protocol validated externally | PASS | Authenticated Bifrost initialize + tools/list (155 tools; Swarm=0) |
| application runtime usable | PASS | Official x64; exe+`registry.node` PE `0x8664`; window + `/health` 200 — see runtime audit |
| Home usable | PASS | Post-repair UI screenshot; assistants render; no `toLowerCase` overlay |
| Agents usable | PASS | Agents tab present; `agentcore-workspace-agent` in `agents.db` with `mcps=["agentcore-gateway"]` |
| provider/model usable | PASS | Agent model `deepseek:deepseek-v4-pro`; providers not used as MCP base URL |
| Agent conversation usable | PASS | Cherry local API chat → `PONG` with DeepSeek V4 Pro |
| MCP mounted | PASS | Exactly one gateway; no Swarm / 8081 / direct upstream |
| memory lifecycle validated (app credentials) | PASS | `validate_cherry_memory_lifecycle.py` → PASS |
| project isolation validated | PASS | A=`agentcore-control-plane` ↔ B=`nfa-alerts-enterprise` |
| Global Memory | PASS (OFF) | `globalMemoryEnabled=false` |
| rollback validated | PASS | `E:\AgentCore-Backups\cherry-pre-alignment-*` + `cherry-runtime-repair-20260720-202353` |

**Do not treat morning/evening enrollment alone as complete live validation.** Runtime PE + Home UI + model chat were required after `3105a43`.

## Timeline

| When | Result |
| --- | --- |
| Morning 2026-07-20 | Live store `mcp.servers=[]` while Cherry running; re-enroll blocked |
| Evening enrollment (`3105a43`) | Cherry quit; enroll exit 0; gateway + Agent + lifecycle scripts PASS — **UI runtime not proven** |
| Night repair (this audit) | ARM64 `registry.node` root cause; official x64 reinstall; assistant model repair; Home UI + chat PASS |

## Live MCP record (sanitized)

```json
{
  "id": "agentcore-gateway",
  "name": "agentcore-gateway",
  "type": "streamableHttp",
  "url": "http://127.0.0.1:8080/mcp",
  "active": true,
  "timeout": 300,
  "has_auth_header": true,
  "auth_env_placeholder": false,
  "auth_bearer_len": 87,
  "provider": "AgentCore"
}
```

Authentication storage posture: bearer materialized into Cherry Local Storage from Windows User env `BIFROST_MCP_VIRTUAL_KEY` (Cherry cannot expand `${env:}`). Never commit live LevelDB/import JSON.

## Memory / duplicate systems

| Setting | Value |
| --- | --- |
| `globalMemoryEnabled` | false |
| Built-in memory MCP | not active as AgentCore memory |
| Knowledge bases | none created for AgentCore |
| OpenClaw gateway slice | stopped |
| Canonical memory | `agentcore-gateway` → `agentcore-memory` → PG18 |

## Agent

| Field | Value |
| --- | --- |
| id | `agentcore-workspace-agent` |
| name | AgentCore Workspace Agent |
| model | `deepseek:deepseek-v4-pro` (repaired; was broken `cherryin:…` with empty CherryIN catalog) |
| mcps | `["agentcore-gateway"]` |
| prompt | `docs/prompts/cherry-agentcore-workspace-agent.md` |
| skills | approved hash-pinned set (excludes find-skills) |
| client_key / agent_key | `cherry-studio` / `cherry-studio-assistant` |
| capability profile | builder |

## Backups

| Backup | Role |
| --- | --- |
| `E:\AgentCore-Backups\cherry-pre-alignment-20260720-192534` | Pre-alignment AppData |
| `E:\AgentCore-Backups\cherry-runtime-repair-20260720-202353` | Full pre-reinstall AppData + Program Files + plugin originals |
| `E:\AgentCore-Backups\cherry-installers-20260720` | Official x64 setup (hash-verified) |
| `E:\AgentCore-Backups\cherry-assistant-model-repair-*` | Persist/assistant model repair |

## Scripts (source-controlled)

- `scripts/cherry/enroll_agentcore_gateway.py`
- `scripts/cherry/patch_mcp_leveldb.js`
- `scripts/cherry/configure_agentcore_agent.py`
- `scripts/cherry/validate_cherry_studio.py`
- `scripts/cherry/validate_cherry_memory_lifecycle.py`
- `scripts/cherry/rollback_cherry_alignment.py`
- `scripts/cherry/repair_cherry_memory_model.js`
- `scripts/cherry/repair_cherry_assistant_models.js`

## Invariants preserved

- No `.env` files
- No secrets printed or committed
- No Bifrost / PostgreSQL / other IDE / Swarm configuration changes
- No app.asar patch
- No port-8081 OAuth/header shim
- Unrelated Studio-interrupt WIP left untouched
