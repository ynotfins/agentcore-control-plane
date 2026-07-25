# MiniMax Agent Classic Enrollment — Phase 4E

**Date:** 2026-07-25  
**Product:** MiniMax Agent Classic `1.0.0.5` (`com.minimax.agent-classic`)  
**Prior repair:** `audits/MINIMAX_CLASSIC_REPAIR_2026-07-22.md`  
**UI guide:** `ide-profiles/minimax-classic/MCP_ENROLLMENT_UI.md`

---

## Fact-based stop state

Classic **does not** expose a local `mcp.json`. Custom MCP is enrolled only through the Matrix cloud UI/API (`add_or_edit_server` / `list_added_server`, `mcp_server_type=UserCustomized`).

| Check | Result |
| --- | --- |
| Classic install / rules | Present — `C:\Users\ynotf\.minimax-agent\AGENT.md` includes agentcore-gateway guidance |
| Local MCP file | **None** |
| Logs mentioning agentcore/8080 enrollment | **None** in latest Classic logs (last dated 2026-07-22) |
| Operator Matrix UI enrollment this phase | **Not executed** (requires interactive Classic UI; cannot be forged from Cursor) |
| Public tunnel created | **No** (forbidden) |

---

## Product limitation (if Matrix cannot reach localhost)

If Classic’s Matrix path executes remotely and cannot reach `http://127.0.0.1:8080/mcp`, record:

`MINIMAX_CLASSIC_LOCALHOST_MCP_UNSUPPORTED_WITHOUT_PUBLIC_TUNNEL`

Do **not** create a public tunnel to satisfy enrollment.

Until the operator completes UI enrollment (or documents the localhost limitation above), status remains:

`awaiting_operator_cloud_mcp_enrollment`

---

## Operator steps (unchanged)

1. Open MiniMax Agent Classic with `--user-data-dir=C:\Users\ynotf\AppData\Roaming\MiniMaxAgent-Classic`.
2. Matrix custom MCP → add:
   - `server_name`: `agentcore-gateway`
   - `base_url`: `http://127.0.0.1:8080/mcp`
   - `mcp_server_type`: `UserCustomized`
   - Bearer: materialize `BIFROST_MCP_VIRTUAL_KEY` in protected UI only
3. Restart Classic; confirm connection.
4. Run 14-step lifecycle + fresh-chat Continue. from `MINIMAX_CLASSIC_REPAIR_2026-07-22.md`.

---

## Status signal

`MINIMAX_CLASSIC_UI_ENROLLMENT_PENDING` — rules present; cloud MCP enrollment still operator UI-gated; no tunnel.
