# Cherry Studio AgentCore Gateway Enrollment Evidence (2026-07-20)

**See also:** `BLUEPRINT.md` · `docs/operations/CHERRY_STUDIO_AGENTCORE.md` · `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` · `docs/operations/OPENROUTER_MCP.md` · `audits/CHERRY_MEMORY_LIFECYCLE_2026-07-20.json` · `audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md`

**Version:** 1.9.12 (win|prod|packaged)  
**AppData:** `%APPDATA%\CherryStudio`  
**Install:** `C:\Program Files\Cherry Studio\Cherry Studio.exe`

## Status fields (do not collapse)

| Field | Status | Evidence |
| --- | --- | --- |
| configuration enrolled | PASS | LevelDB `agentcore-gateway` active @ `http://127.0.0.1:8080/mcp` timeout 300 |
| MCP connected | PASS | Authenticated Bifrost initialize + tools/list via same endpoint/auth Cherry stores |
| tools discovered | PASS | 155 tools; prefixes include agentcore_memory (10), project_router, arabold_docs, depwire, tentra, …; Swarm=0 |
| Agent mounted | PASS | `agentcore-workspace-agent` / `AgentCore Workspace Agent`; `mcps=["agentcore-gateway"]` |
| memory lifecycle validated | PASS | `audits/CHERRY_MEMORY_LIFECYCLE_2026-07-20.json` |
| project isolation validated | PASS | A=`agentcore-control-plane` ↔ B=`nfa-alerts-enterprise` |
| model provider validated | PASS | Providers untouched; MCP not used as model base URL; OpenRouter MCP distinct |
| rollback validated | PASS | Backup `E:\AgentCore-Backups\cherry-pre-alignment-20260720-192534` (+ enroll snapshots); `rollback_cherry_alignment.py --prove-only` |

## Timeline

| When | Result |
| --- | --- |
| Morning 2026-07-20 | Live store `mcp.servers=[]` while Cherry running; re-enroll blocked |
| Evening enrollment | Cherry quit; enroll exit 0; gateway record active |
| Alignment closeout (this pass) | Renderer/contract/validators/Agent/prompt/lifecycle/rollback docs completed |

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

Authentication storage posture: bearer materialized into Cherry Local Storage from Windows User env `BIFROST_MCP_VIRTUAL_KEY` (Cherry cannot expand `${env:}`). Never commit live LevelDB/import JSON. Record only env name, length, and redacted hash (`vk_sha256_12=9a3c6a137010` at validation time).

## Memory / duplicate systems

| Setting | Value |
| --- | --- |
| `globalMemoryEnabled` | false |
| Built-in memory MCP | not active as AgentCore memory |
| Knowledge bases | empty / none created this task |
| OpenClaw gateway slice | stopped |

## Agent

| Field | Value |
| --- | --- |
| id | `agentcore-workspace-agent` |
| name | AgentCore Workspace Agent |
| mcps | `["agentcore-gateway"]` |
| prompt | `docs/prompts/cherry-agentcore-workspace-agent.md` |
| skills | approved hash-pinned set (excludes find-skills) |
| client_key / agent_key | `cherry-studio` / `cherry-studio-assistant` |
| capability profile | builder |

## Backups

| Backup | Role |
| --- | --- |
| `E:\AgentCore-Backups\cherry-pre-alignment-20260720-192534` | Full protected pre-alignment AppData tree + SHA-256 manifest |
| `E:\AgentCore-Backups\cherry-enroll-*` | Enroll-time LevelDB/agents snapshots |

## Scripts (source-controlled)

- `scripts/cherry/enroll_agentcore_gateway.py`
- `scripts/cherry/patch_mcp_leveldb.js`
- `scripts/cherry/configure_agentcore_agent.py`
- `scripts/cherry/validate_cherry_studio.py`
- `scripts/cherry/validate_cherry_memory_lifecycle.py`
- `scripts/cherry/rollback_cherry_alignment.py`
- `scripts/cherry/package.json` (classic-level; `node_modules/` gitignored)

## Invariants preserved

- No `.env` files
- No secrets printed or committed
- No Bifrost / PostgreSQL / other IDE / Swarm configuration changes
- No app.asar patch
- No port-8081 OAuth/header shim
- Unrelated Studio-interrupt WIP left untouched
- Experimental `inject_cherry_*.js` / `_node_workspace` left untracked per disposition
