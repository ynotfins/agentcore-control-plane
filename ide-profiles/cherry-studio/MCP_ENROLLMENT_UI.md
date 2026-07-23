# Cherry Studio — AgentCore Gateway UI Enrollment

Cherry Studio persists MCP servers in Local Storage LevelDB under the redux key
`persist:cherry-studio -> mcp.servers`. It does **not** use a local `mcp.json`.

Use the source-controlled enrollment scripts rather than hand-editing the LevelDB store.

## Operator steps (native enrollment)

1. Fully quit Cherry Studio (no `lockfile`, no `Cherry Studio.exe` process).
2. Confirm `BIFROST_MCP_VIRTUAL_KEY` is set in Windows User env (never print the value).
3. Confirm Bifrost health: `GET http://127.0.0.1:8080/health` returns 200.
4. From `D:\github\agentcore-control-plane`, run:

```powershell
python scripts/cherry/enroll_agentcore_gateway.py --apply
python scripts/cherry/configure_agentcore_agent.py --apply
python scripts/cherry/validate_cherry_studio.py
```

5. Restart Cherry Studio.
6. Open the **AgentCore Workspace Agent**.
7. Confirm MCP tools list only through `agentcore-gateway` (no direct upstreams, no Swarm, no 8081 shim).

## Required AgentCore entry

| Field | Value |
| --- | --- |
| id / name | `agentcore-gateway` |
| type | `streamableHttp` |
| url | `http://127.0.0.1:8080/mcp` |
| timeout | 300 |
| Authorization | Bearer materialized from `BIFROST_MCP_VIRTUAL_KEY` (Cherry cannot expand `${env:}`) |

Do not add direct entries for `agentcore-memory`, Playwright, Arabold, Depwire, Tentra,
Context Fabric, OpenRouter MCP, or Swarm.

## Agent setup

| Field | Value |
| --- | --- |
| id | `agentcore-workspace-agent` |
| display name | `AgentCore Workspace Agent` |
| model | `deepseek:deepseek-v4-pro` (must be a live provider/model with key) |
| mcps | `["agentcore-gateway"]` only |
| prompt source | `docs/prompts/cherry-agentcore-workspace-agent.md` |
| Global Memory | OFF |
| builtin inMemory MCP | inactive |

## Secrets

- Never commit the materialized bearer.
- Never paste secrets into Git-tracked files.
- Record only length and SHA-256 of the User-scope `BIFROST_MCP_VIRTUAL_KEY` in audits.

## Validation

After enrollment:

```powershell
python scripts/cherry/validate_cherry_studio.py
python scripts/cherry/validate_cherry_memory_lifecycle.py
```

Record the result in `ide-profiles/cherry-studio/IDE_PROFILE.yaml` (`last_validation_date`).
