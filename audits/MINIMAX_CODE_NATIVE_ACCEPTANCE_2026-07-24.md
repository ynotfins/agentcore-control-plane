# MiniMax Code Native MCP Investigation — Phase 4A

**Date:** 2026-07-25  
**Product:** MiniMax Code `3.0.53.91`  
**Executable:** `C:\Users\ynotf\AppData\Local\Programs\MiniMax Code\MiniMax Code.exe`  
**Active data root:** `C:\Users\ynotf\.minimax` (`.mavis` = junction → same root)  
**Backup:** `E:\AgentCore-Backups\minimax-repair-20260725-phase4a`  
**Prior backup:** `E:\AgentCore-Backups\minimax-repair-20260722T205648Z`

---

## Verdict (anti-sycophancy / evidence-first)

| Route | Verdict | Signal |
| --- | --- | --- |
| **CLI wrappers** (`mavis.cmd` / `minimax.cmd` → `resources\resources\daemon\cli.js`) | **Unsupported on this install** | `MINIMAX_CODE_NATIVE_MCP_UNSUPPORTED_WITH_REASON` **for the CLI route only** |
| **In-app MCP** (`mcp.json` → Bifrost `agentcore-gateway`) | **Product-supported; config repaired; native lifecycle not yet proven in-session** | **Not** `live_validated`. Status: `configured_restart_required` |

**Do not claim:** overall product “has no MCP support.” Official changelog documents MCP Tool Integration (v3.0.20) and Native MCP Tool Exposure (v3.0.28). Version 3.0.53.91 is after both.

**Do not claim:** HTTP `tools/list` against Bifrost = MiniMax-native acceptance.

---

## Evidence — CLI route broken

Wrappers (installer-managed under `C:\Users\ynotf\.minimax\bin\`):

```bat
set ELECTRON_RUN_AS_NODE=1
"...\MiniMax Code.exe" "...\resources\resources\daemon\cli.js" %*
```

Runtime:

```text
Error: Cannot find module
'...\MiniMax Code\resources\resources\daemon\cli.js'
code: 'MODULE_NOT_FOUND'
```

Install layout check:

- `resources\resources\` contains only installer assets (icons, nsh, dmg backgrounds) — **no** `daemon\`, **no** `matrix-mcp-cli\`
- `npx @electron/asar list app.asar` shows **zero** `daemon` paths
- Builtin `matrix` MCP entry also points at missing `resources\resources\matrix-mcp-cli\index.js`

**Reason string (CLI):** MiniMax Code 3.0.53.91 ships PATH wrappers that target a nonexistent on-disk `daemon\cli.js`. No repairable CLI entry point exists in the installed tree without patching `app.asar` (forbidden). CLI-based MCP invocation is unsupported on this install.

---

## Evidence — In-app MCP path exists

1. Official docs: [MiniMax Code changelog](https://agent.minimax.io/docs/changelog) — MCP integration + native MCP tool exposure in 3.0.x.
2. Live `mcp.json` contains `agentcore-gateway` at `http://127.0.0.1:8080/mcp` plus builtin companions `matrix` / `cu` / `trash`.
3. Daemon logs (`daemon-2026071414.log`) show MiniMax **did** attempt Streamable HTTP MCP refresh for `agentcore-gateway`.
4. Failure mode was auth, not “MCP unsupported”:

```text
Failed to connect to MCP server "agentcore-gateway": Streamable HTTP error:
... status_code 401 ... "virtual key required to access mcp server"
```

5. Pre-repair live Authorization was `Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}` — User-scope VK exists (len 80, prefix `sk-bf-`), but MiniMax did **not** expand the placeholder → 401.

---

## Repair performed (client-local only)

1. Closed all MiniMax Code processes (entry gate).
2. Backed up `mcp.json` + wrappers → `E:\AgentCore-Backups\minimax-repair-20260725-phase4a`.
3. Materialized `BIFROST_MCP_VIRTUAL_KEY` into live `Authorization: Bearer …` (value not committed; not printed beyond prefix).
4. Set gateway `type` to `streamable-http` (matches daemon client + companion style).
5. Bifrost `/health` remains 200 after repair.
6. Did **not** patch `app.asar`; did **not** invent session IDs; did **not** treat diagnostic HTTP as native.

Live secrets remain outside Git. Source template still documents `${env:…}` with a materialization note.

---

## Native 14-step lifecycle

**Not executed in this chat** — requires an operator MiniMax Code session. Prior audits only marked steps `READY_FOR_OPERATOR`.

### Operator acceptance message (paste in fresh MiniMax Code chat on `D:\github\agentcore-control-plane`)

```text
AgentCore native acceptance — MiniMax Code only.

Use only tools from agentcore-gateway. Do not ask me to recap history.

1) project_list
2) project_activate agentcore-control-plane at D:\github\agentcore-control-plane
3) session_open session_key=agentcore-control-plane:minimax-code:native-acceptance:2026-07-25
4) startup_context
5) append_event documenting this acceptance run (deterministic idempotency key)
6) repeat the same append_event and confirm idempotent_replay=true
7) retrieve_context with pagination
8) expand_source on the event_id from step 5
9) build_handoff
10) session_close
11) session_open same session_key (resume)
12) activate a different registered project, retrieve_context, prove no cross-project leak
13) reactivate agentcore-control-plane
14) confirm exactly ten agentcore-memory tools and that Playwright is present only through agentcore-gateway
```

After PASS → update `ide-profiles/minimax/IDE_PROFILE.yaml` dimensions to `live_validated` and append evidence to this audit.

---

## Docs searched

- https://agent.minimax.io/docs/changelog (v3.0.20 MCP Tool Integration; v3.0.28 Native MCP Tool Exposure; v3.0.52 latest notes reviewed)
- Prior AgentCore audits: `MINIMAX_CODE_REPAIR_2026-07-22.md`, `MINIMAX_CODE_GATEWAY_ENROLLMENT_2026-07-21.md`, handoff DRIFT on cli.js

---

## Status signals

- `MINIMAX_CODE_NATIVE_MCP_UNSUPPORTED_WITH_REASON` — **CLI wrapper route only** (missing `daemon\cli.js` on 3.0.53.91)
- In-app MCP: `configured_restart_required` after VK materialization + `streamable-http`
- Overall: **not** `live_validated` until operator 14-step completes

**Phase 4A exit:** investigation complete; CLI unsupported documented; in-app path repaired; native acceptance operator-gated.
