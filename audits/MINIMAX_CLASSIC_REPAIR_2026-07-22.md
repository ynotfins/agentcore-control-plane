# MiniMax Agent Classic Repair Evidence — 2026-07-22

**Scope:** MiniMax Agent Classic only. Does not claim MiniMax Code validation.

## Product identity (proven)

| Field | Value |
| --- | --- |
| Product name | MiniMax Agent |
| Marketing label | MiniMax Agent (Classic v1.0.0) |
| App ID | `com.minimax.agent-classic` |
| Version | 1.0.0.5 |
| Executable | `D:\Apps\MiniMaxAgent-Classic\MiniMax Agent.exe` |
| Start Menu | `C:\Users\ynotf\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\MiniMax Agent (Classic v1.0.0).lnk` |
| Launch args | `--user-data-dir="C:\Users\ynotf\AppData\Roaming\MiniMaxAgent-Classic"` |
| Electron user-data | `C:\Users\ynotf\AppData\Roaming\MiniMaxAgent-Classic` |
| Working directory (config) | `C:\Users\ynotf\.minimax-agent\projects` |
| Global rules path | `C:\Users\ynotf\.minimax-agent\AGENT.md` |
| MCP configuration path | **None local** — Matrix cloud `add_or_edit_server` / `list_added_server` |
| Settings / tokens | `C:\Users\ynotf\AppData\Roaming\MiniMaxAgent-Classic\minimax-agent-config.json` (secret-bearing) |
| Logs | `C:\Users\ynotf\AppData\Roaming\MiniMaxAgent-Classic\logs\` |
| Backup | `E:\AgentCore-Backups\minimax-classic-repair-20260722T210236Z` (secret-bearing) |

Same binary SHA-256 as `C:\Users\ynotf\AppData\Local\Programs\MiniMax Agent\MiniMax Agent.exe`, but **isolated** user-data via `--user-data-dir`. Default MiniMax Agent uses App ID `com.minimax.agent` and `C:\Users\ynotf\AppData\Roaming\MiniMax Agent` — **not** Classic.

## Candidate data-root hypotheses

| Path | Type | Verdict |
| --- | --- | --- |
| `C:\Users\ynotf\.minimax` | Normal directory | **Confirmed** MiniMax Code active root |
| `C:\Users\ynotf\.mavis` | Junction → `.minimax` | **Confirmed** alias of MiniMax Code; not a separate Mavis app install |
| `C:\Users\ynotf\.minimax-agent` | Normal directory | **Confirmed** Classic workspace root (`AGENT.md` + `projects/`); not Code |
| `C:\Users\ynotf\.mmx` | Normal directory | **Confirmed** updater/launcher metadata (`config.json`, `update-state.json`); secret-bearing `api_key` present — not an IDE root |

## MCP repair

**Product limitation:** Classic embeds Matrix cloud MCP management (`server_name`, `base_url`, `mcp_server_type=UserCustomized`). No local `mcp.json` exists to patch file-wise.

Source-controlled enrollment guidance:

- `ide-profiles/minimax-classic/MCP_ENROLLMENT_UI.md`
- `ide-profiles/minimax-classic/MCP_CONFIG_TEMPLATE.json`

Required AgentCore entry (operator UI):

| Field | Value |
| --- | --- |
| server_name | `agentcore-gateway` |
| base_url | `http://127.0.0.1:8080/mcp` |
| mcp_server_type | `UserCustomized` |
| Authorization | Materialize bearer in protected live UI if env expansion unsupported |

Do not add direct agentcore-memory / Playwright / Arabold / Depwire / Tentra / OpenRouter / Swarm entries.

## Global rules repair

- Created profile `ide-profiles/minimax-classic/`
- Installed rendered `GLOBAL_RULES.md` to `C:\Users\ynotf\.minimax-agent\AGENT.md`
- Removed prior Codex-flavored / non-AgentCore authority content from that live file (backed up)

## Native acceptance

**Status: `READY_FOR_MINIMAX_CLASSIC_NATIVE_ACCEPTANCE`**

Gateway HTTP health was proved independently for MiniMax Code repair; it does **not** prove Classic native enrollment.

### Operator test message (after UI MCP enrollment)

```text
AgentCore native acceptance — MiniMax Agent Classic only.

First confirm agentcore-gateway is connected and that Playwright/memory/project-router tools appear only through that gateway (exactly ten agentcore-memory tools, four project-router tools; no Swarm/SQL/admin/whole-drive tools).

Then run:
1) project_list
2) project_activate agentcore-control-plane at D:\github\agentcore-control-plane
3) session_open session_key=agentcore-control-plane:minimax-classic:native-acceptance:2026-07-22
4) startup_context
5) append_event for this acceptance run
6) repeat append_event; expect idempotent_replay=true
7) retrieve_context with pagination
8) expand_source exactly
9) build_handoff
10) session_close
11) resume same session_key
12) second-project isolation
13) return to agentcore-control-plane
14) re-confirm exactly ten agentcore-memory tools

Open a fresh Classic chat in the same project with no recap and recover via AgentCore before asking for history.
```
