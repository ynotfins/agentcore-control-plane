# Cherry Studio Target Agent Repair — Phase 4C (DRIFT-01)

**Date:** 2026-07-25  
**Backup:** `E:\AgentCore-Backups\cherry-repair-20260725` (+ LDB partial `E:\AgentCore-Backups\cherry-ldb-pre-phase4c-*`)  
**Product:** Cherry Studio (official x64)  
**Target agent:** `agentcore-workspace-agent` / AgentCore Workspace Agent

---

## Fact-based answer (anti-sycophancy)

DRIFT-01 (“Create a session did nothing”) is **not** explained by a missing Agent record or missing model binding in the current store.

| Check | Result |
| --- | --- |
| Agent `agentcore-workspace-agent` present | YES — `type=claude-code`, `model=deepseek:deepseek-v4-pro`, `mcps=["agentcore-gateway"]` |
| DeepSeek provider enabled + key + `deepseek-v4-pro` catalog | YES (LevelDB `llm.providers`) |
| Gateway MCP active | YES — `streamableHttp` `baseUrl=http://127.0.0.1:8080/mcp`, `isActive=true`, Authorization header present |
| Global Memory | OFF (`memory.memoryConfig.globalMemoryEnabled=false`) |
| Pre-existing target sessions | **2** already in `agents.db` before Phase 4C |
| Operator-window logs (2026-07-24) | Repeated `agentcore-gateway` **CONNECTION_REFUSED** / ping timeouts — Bifrost was down |

**Assessment of DRIFT-01:** Partially correct as an operator observation of UI failure during a Bifrost-down window; **incorrect** as a durable claim that the target Agent cannot create sessions. Session rows for the target Agent already existed, and a new session was inserted successfully via the supported `agents.db` schema.

Cherry Claw is still **not** a substitute for AgentCore Workspace Agent (unchanged).

---

## Repairs / proofs performed

1. Closed Cherry Studio; backed up essential Roaming tree to `E:\AgentCore-Backups\cherry-repair-20260725`.
2. Inspected `Data/agents.db` agents + sessions; inspected LevelDB `persist:cherry-studio` for MCP/providers/memory.
3. Confirmed inactive dormant `mcp-gsheets` stdio entry (`isActive=false`) — left dormant; not activated.
4. Re-asserted Global Memory OFF in LevelDB (already false).
5. Created proof session via SQLite (supported schema, not `app.asar`):
   - `session_1784950549575_992ce5921`
   - name: `agentcore-phase4c-session-proof`
   - `agent_id=agentcore-workspace-agent`
   - `model=deepseek:deepseek-v4-pro`
   - `mcps=["agentcore-gateway"]`
   - target agent session count after insert: **3**
6. Did **not** claim HTTP diagnostics as native lifecycle PASS.
7. Full 14-step native lifecycle from the UI Agent remains **operator-gated** with Bifrost healthy.

---

## Status after Phase 4C

| Dimension | Status |
| --- | --- |
| Target Agent record | `live_validated` |
| Model link (`deepseek:deepseek-v4-pro`) | `live_validated` |
| Gateway MCP enrollment | `live_validated` (config) |
| Session creation (schema / DB) | `live_validated` |
| UI “Create a session” click | `configured_restart_required` (operator; Bifrost must be up) |
| Native 14-step from target Agent | `configured_restart_required` |
| Global Memory off | `live_validated` |

**DRIFT-01 reconciliation signal:** `CHERRY_TARGET_AGENT_SESSION_SCHEMA_PROVEN` — premature `live_validated` for full native lifecycle remains revoked until operator UI lifecycle with Bifrost healthy.

---

## Operator follow-up (UI)

1. Ensure Bifrost `/health` = 200.
2. Launch Cherry → open **AgentCore Workspace Agent** (not Cherry Claw).
3. Confirm session `agentcore-phase4c-session-proof` appears **or** click Create a session.
4. Run 14-step gateway memory lifecycle from that Agent.
5. On PASS, update this audit + IDE profile dimensions to `live_validated`.
