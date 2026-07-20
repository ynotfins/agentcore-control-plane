# Cherry Studio AgentCore Gateway Enrollment Evidence (2026-07-20)

**See also:** `BLUEPRINT.md` (single-gateway topology) · `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` · `docs/operations/OPENROUTER_MCP.md` (no direct OpenRouter MCP) · `audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md` · `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md`

**Version:** 1.9.12 (win|prod|packaged)  
**AppData:** `%APPDATA%\CherryStudio`

## Timeline

| When | Result |
| --- | --- |
| Morning 2026-07-20 | Live store `mcp.servers=[]` while Cherry processes running; re-enroll blocked |
| Evening 2026-07-20 (reconstruction closeout) | Cherry **quit**; `enroll_agentcore_gateway.py` exit 0; Local Storage dump shows `agentcore-gateway` active |

## Morning verification (historical — empty store)

| Check | Result |
| --- | --- |
| Cherry processes running | YES — blocked Local Storage mutation |
| `persist:cherry-studio` → `mcp.servers` | **`[]` empty** |
| Prior Gate C claim of one gateway | Stale vs then-live store |

**Backup (morning):** `E:\AgentCore-Backups\cherry-pre-enrollment-20260720-023141`

## Evening re-enroll + validation (current)

| Check | Result |
| --- | --- |
| Cherry processes / lockfile | None / absent |
| `python scripts/cherry/enroll_agentcore_gateway.py` | exit 0 (Unicode print fixed for cp1252) |
| Backup | `E:\AgentCore-Backups\cherry-enroll-20260720-190500` |
| Import artifact | `%APPDATA%\CherryStudio\Data\agentcore-gateway-mcp-import.json` |
| `dump_mcp.js` → `mcp.servers` | **2 entries:** (1) built-in `inMemory` inactive; (2) **`agentcore-gateway`** `streamableHttp` `http://127.0.0.1:8080/mcp` **active=true** |
| Direct OpenRouter MCP | absent from dump |
| Secrets printed | no |

### Target configuration (satisfied for gateway record)

- name: `agentcore-gateway`
- type: `streamableHttp`
- URL: `http://127.0.0.1:8080/mcp`
- Authorization: Bearer from `BIFROST_MCP_VIRTUAL_KEY` (materialized; Cherry does not expand `${env:}`)
- timeout: 300 seconds
- no direct OpenRouter MCP; OpenRouter API provider remains separate

### Remaining operator UI check

After next Cherry launch: confirm Settings → MCP shows one AgentCore gateway and tools/list includes the ten `agentcore-memory` tools. Cursor already proves the ten-tool surface independently.

## Invariants preserved

- No `.env` files created
- No secrets printed in this evidence
- Swarm untouched
- Default models/providers not changed by this enrollment work
