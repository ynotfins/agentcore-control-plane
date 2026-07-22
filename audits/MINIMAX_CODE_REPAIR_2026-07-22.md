# MiniMax Code Repair Evidence — 2026-07-22

**Scope:** MiniMax Code client-local only (plus approved Bifrost runtime restart via scheduled task). No Cherry/Codex/Claude/Cursor live config, no `PROJECT_ANCHOR.md` / `BLUEPRINT.md` edits, no PostgreSQL schema, no Swarm.

## Client identity

| Field | Value |
| --- | --- |
| Product | MiniMax Code |
| Version | 3.0.53.91 |
| Executable | `C:\Users\ynotf\AppData\Local\Programs\MiniMax Code\MiniMax Code.exe` |
| Active root | `C:\Users\ynotf\.minimax` |
| `.mavis` | Junction → `C:\Users\ynotf\.minimax` (same Code data root; not a separate Mavis app) |
| Global rules | `C:\Users\ynotf\.minimax\AGENT.md` |
| MCP config | `C:\Users\ynotf\.minimax\mcp\mcp.json` |
| In-app persona | `C:\Users\ynotf\.minimax\agents\mavis\agent.md` (persona only) |
| Backup | `E:\AgentCore-Backups\minimax-repair-20260722T205648Z` |

## Root cause (missing native MCP tools)

**Bifrost gateway was down**, not a MiniMax `mcp.json` defect.

| Evidence | Result |
| --- | --- |
| Pre-repair `/health` | connection refused |
| Scheduled task last result | `-1073741510` (`STATUS_CONTROL_C_EXIT`) |
| Bifrost stdout | graceful `received signal terminated` at `2026-07-22T12:54:16-04:00` |
| Live `mcp.json` | already correct single `agentcore-gateway` entry + companions `matrix`/`cu`/`trash` |
| Shadow `mcp.json` | none (single path only) |
| `BIFROST_MCP_VIRTUAL_KEY` | present User-scope, length 80, prefix `sk-bf-ag`, SHA-256 `9a3c6a13701093c39d4ef02237a3c91bb5a5ade3e568fb2072250e2c6df7df2e` (value never printed in audits) |

## Shared gateway diagnostic (HTTP — not native MiniMax)

| Check | Result |
| --- | --- |
| Restart | `schtasks /run /tn "\AgentCore\AgentCore-Bifrost-Gateway"` |
| `/health` | 200 `status=ok` |
| `initialize` | 200, `serverInfo.name=builder`, protocol `2025-06-18` |
| `notifications/initialized` | 202 |
| `tools/list` | 135 tools |
| `agentcore_memory-*` | exactly 10 |
| `agentcore_project_router-*` | exactly 4 |
| `playwright-*` | 24 |
| Forbidden (swarm/sql/admin/whole-drive/bifrost-admin) | absent |
| `memory_status` | healthy; PG18 `127.0.0.1:55433` reachable |
| `project_list` | 55 projects |

PG18 Windows service remains `Stopped` while port accepts connections (known M8 ownership note; not changed).

## Client-local repairs

1. Re-rendered and installed `AGENT.md` from `ide-profiles/minimax/GLOBAL_RULES.md` (hash match after install).
2. Aligned in-app persona `agents\mavis\agent.md` away from retired `global-memory-gateway`, OpenClaw-as-authority, and `D:\MCP-Control-Plane` authority.
3. Set `enabled: true` and `configured: true` on `agentcore-gateway` while preserving `${env:BIFROST_MCP_VIRTUAL_KEY}` placeholder and companions.
4. Relaunched MiniMax Code (process running). Runtime logs show local mavis APIs healthy; **no in-session native tool-call evidence** (product limitation).

## Native acceptance

**Status: `READY_FOR_MINIMAX_NATIVE_ACCEPTANCE`**

HTTP diagnostics do **not** prove MiniMax-native enrollment. Operator must run the lifecycle inside MiniMax Code.

### Operator test message (paste into a fresh MiniMax Code chat on `D:\github\agentcore-control-plane`)

```text
AgentCore native acceptance — MiniMax Code only.

Use only tools from agentcore-gateway. Do not ask me to recap history.

1) project_list
2) project_activate agentcore-control-plane at D:\github\agentcore-control-plane
3) session_open session_key=agentcore-control-plane:minimax-code:native-acceptance:2026-07-22
4) startup_context
5) append_event documenting this acceptance run (deterministic idempotency key)
6) repeat the same append_event and confirm idempotent_replay=true
7) retrieve_context with pagination
8) expand_source on the event_id from step 5
9) build_handoff
10) session_close
11) session_open same session_key (resume)
12) activate a different registered project, retrieve_context, prove no PROJECT_A_PROTECTED_DATA leak
13) reactivate agentcore-control-plane
14) confirm exactly ten agentcore-memory tools and that Playwright is present only through agentcore-gateway

Then open a second fresh chat in the same project with no recap and recover via startup_context/retrieve_context/expand_source before asking me anything historical.
```

## Source files (Git)

- `ide-profiles/minimax/*`
- `audits/MINIMAX_CODE_REPAIR_2026-07-22.md`
- `audits/MINIMAX_CODE_MEMORY_LIFECYCLE_2026-07-22.json`

Live MiniMax config and persona files are **not** committed.
