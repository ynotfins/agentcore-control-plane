# Cherry Studio AgentCore Gateway Enrollment Evidence (2026-07-20)

**Version:** 1.9.12 (win|prod|packaged)  
**AppData:** `%APPDATA%\CherryStudio`  
**Backup:** `E:\AgentCore-Backups\cherry-pre-enrollment-20260720-023141` (+ shared-read `agents.db` SHA256 `26FEF803…1329D8`)

## Live verification

| Check | Result |
| --- | --- |
| Cherry processes running | YES (multiple `Cherry Studio.exe`) — blocks Local Storage mutation |
| `persist:cherry-studio` → `mcp.servers` | **`[]` empty** (parsed from Local Storage `000244.log`) |
| `globalMemoryEnabled` | **false** |
| Direct OpenRouter MCP (`mcp.openrouter.ai`) | **absent** in Local Storage |
| `agents.db` agent `mcps` columns | `None` / empty (gateway strings only in chat history) |
| Prior Gate C claim of one gateway | **stale vs live store** — gateway must be re-added |

## Required target (not yet applied — Cherry must quit)

- name: `agentcore-gateway`
- type: Streamable HTTP / `streamableHttp`
- URL: `http://127.0.0.1:8080/mcp`
- Authorization: Bearer from `BIFROST_MCP_VIRTUAL_KEY` (materialized; Cherry does not expand `${env:}`)
- timeout: 300 seconds
- exactly one record; no duplicate; no direct OpenRouter MCP; OpenRouter API provider remains separate

## Repair path

```powershell
# 1) Fully quit Cherry Studio (File → Exit; confirm no Cherry Studio.exe)
# 2) Run:
python D:\github\agentcore-control-plane\scripts\cherry\enroll_agentcore_gateway.py
# 3) Import Data\agentcore-gateway-mcp-import.json via Settings → MCP Servers if needed
# 4) Restart Cherry; validate tools/list = ten agentcore-memory tools + lifecycle
```

## Lifecycle validation

Deferred until gateway record is restored in Cherry UI/store. Cursor gateway already proves the ten-tool surface independently.

## Invariants preserved

- No `.env` files created
- No secrets printed in this evidence
- Swarm untouched
- Default models/providers not changed by this enrollment work
