# MiniMax Agent Classic — AgentCore Gateway UI Enrollment

Classic does **not** use a local `mcp.json`. Custom MCP servers are enrolled through
the MiniMax Matrix cloud catalog APIs embedded in the product:

- `POST /matrix/api/v1/mcp/list_added_server`
- `POST /matrix/api/v1/mcp/add_or_edit_server` with payload shape:
  - `server_name`
  - `base_url`
  - `mcp_server_type: UserCustomized`

## Operator steps (native enrollment)

1. Launch **MiniMax Agent (Classic v1.0.0)** from the Start Menu shortcut:
   - Target: `D:\Apps\MiniMaxAgent-Classic\MiniMax Agent.exe`
   - Args: `--user-data-dir="C:\Users\ynotf\AppData\Roaming\MiniMaxAgent-Classic"`
2. Sign in if the login window appears (required for Matrix MCP catalog).
3. Open Custom MCP / Add MCP and create exactly one AgentCore entry:

| Field | Value |
| --- | --- |
| Name / server_name | `agentcore-gateway` |
| URL / base_url | `http://127.0.0.1:8080/mcp` |
| Type | UserCustomized / HTTP (product label may vary) |
| Authorization | `Bearer <BIFROST_MCP_VIRTUAL_KEY>` materialized in the protected live UI only if Classic cannot expand `${env:BIFROST_MCP_VIRTUAL_KEY}` |
| Timeout | 300 seconds if the field exists |

4. Do **not** add direct entries for agentcore-memory, Playwright, Arabold, Depwire,
   Tentra, Context Fabric, OpenRouter MCP, or Swarm.
5. Restart Classic, confirm `agentcore-gateway` is connected, then run the native
   lifecycle in a fresh chat (see `VALIDATION.md`).

## Secrets

- Never commit the materialized bearer.
- Never paste secrets into Git-tracked files.
- Record only length and SHA-256 of the User-scope `BIFROST_MCP_VIRTUAL_KEY` in audits.
