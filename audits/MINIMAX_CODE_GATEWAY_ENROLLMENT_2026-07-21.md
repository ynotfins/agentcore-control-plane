# MiniMax Code AgentCore Gateway Enrollment Evidence (2026-07-21)

**See also:** `BLUEPRINT.md` · `PROJECT_ANCHOR.md` · `MASTER_CONFIG_AND_PROMPT.md` · `contracts/agentcore-gateway-client.json` · `contracts/global-agent-policy.yaml` · `ide-profiles/minimax/` · `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` · `audits/MINIMAX_CODE_MEMORY_LIFECYCLE_2026-07-21.json`

**Scope:** client-local only. MiniMax Code IDE only. No other IDE / no Bifrost runtime / no Swarm / no OpenClaw / no ClawX / no `C:\Users\ynotf\.mavis\` (separate Mavis IDE) / no `D:\MCP-Control-Plane\` was edited.

## Client identity

| Field | Value | Evidence |
| --- | --- | --- |
| Product | MiniMax Code | `C:\Users\ynotf\AppData\Local\Programs\MiniMax Code\MiniMax Code.exe` `ProductName` |
| Installed version | 3.0.53.91 | exe `FileVersion` |
| Active user-data root | `C:\Users\ynotf\.minimax\` | runtime `activeDataDir` |
| Active MCP config path | `C:\Users\ynotf\.minimax\mcp\mcp.json` | matches `contracts/agentcore-gateway-client.json` -> `client_render_hints.minimax.config_path` |
| Active global-rules target | `C:\Users\ynotf\.minimax\AGENT.md` | IDE's native global-rules path (mechanism unverified in `IDE_PROFILE.yaml`; delivered through install prompt + this live file per `INSTALL_OR_UPDATE.md`) |
| Active per-rule file | `C:\Users\ynotf\.minimax\rules\agentcore-memory.md` | IDE's per-topic rule file |
| Supported MCP transport | http/streamable | per gateway-client contract |
| Env-var expansion in HTTP headers | yes (per `supports_env_headers: true`) | `${env:BIFROST_MCP_VIRTUAL_KEY}` left unresolved in live config |
| Restart behavior | full client restart required after MCP config change | per `IDE_PROFILE.yaml` `restart_behavior` |
| Matching IDE profile | `ide-profiles/minimax/` | active data dir = minimax, not mavis |
| Mavis IDE dir (`C:\Users\ynotf\.mavis\`) | untouched | per "do not modify both MiniMax and Mavis" disambiguation rule |

## Status fields (do not collapse)

| Field | Status | Evidence |
| --- | --- | --- |
| MCP configuration enrolled | PASS (already aligned) | Live `mcp.json` has exactly one `agentcore-gateway` entry matching `renderers/gateway-clients/minimax.json`; type=http, url=http://127.0.0.1:8080/mcp, Authorization Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}, timeout=300. SHA256 unchanged from pre-cutover. No edit required. |
| Direct duplicate upstreams removed | N/A | Live config contains only the single gateway entry. The other three MCP entries (matrix, cu, trash) are MiniMax Code built-in companion services at `http://127.0.0.1:15321/mavis/mcp/*` and `https://agent.minimax.io`; not Bifrost upstream duplicates, not removable per scope. |
| Bifrost /health | PASS | `GET http://127.0.0.1:8080/health` -> 200, `{"components":{"db_pings":"ok"},"status":"ok"}` |
| Scheduled task owner | Running | `\AgentCore\AgentCore-Bifrost-Gateway` state=Running, last=267009 |
| `BIFROST_MCP_VIRTUAL_KEY` env | present (length 80, prefix `sk-bf-ag`; never printed in full) | `[Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY','User')` |
| Direct MCP initialize | PASS | `initialize` -> 200, `serverInfo.name=builder`, `version=v2.0.0-prerelease1`, `protocolVersion=2025-06-18` |
| `notifications/initialized` | PASS | 202, empty body (correct for notification) |
| Native tool discovery (`tools/list`) | PASS | 147 tools served through builder VK; 10 agentcore_memory + 4 agentcore_project_router + arabold_docs (12) + depwire (21) + tentra (33) + sequential_thinking (1) + context_fabric (5) + filesystem (14) + playwright (24) + cursor_agent_mcp (10) + obsidian_vault (11) |
| `agentcore_memory` tool surface (exactly 10) | PASS | append_event, build_handoff, docs_search, expand_source, memory_status, propose_fact, retrieve_context, session_close, session_open, startup_context |
| `agentcore_project_router` tool surface (exactly 4) | PASS | project_activate, project_clear, project_list, project_status |
| Forbidden tools absent | PASS | None of: swarm, psql, postgres, bifrost_admin/admin, desktop-commander, global-memory-gateway, context7, mem0, composio, hostinger |
| Filesystem MCP root | PASS (bounded) | `filesystem-list_allowed_directories` -> `D:\github` only (no whole-drive root) |
| Global rules installed | PASS | `AGENT.md` (15038 B, sha256 `4930EFC5B6DB5FCD1C615F1DC27D298D5E4F5B112942797829EC21E1EC9084F0`) installed from canonical `ide-profiles/minimax/GLOBAL_RULES.md` |
| Per-rule file aligned | PASS | `rules/agentcore-memory.md` (4701 B, sha256 `9A10B9219EAC63B7FA6CB062BCB9DCC1B740302F7AE4624786218A29F35A26ED`) authority chain repointed from `D:\workspace\AGENTS.md` to `D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml` |
| Backup outside Git | PASS | `E:\AgentCore-Backups\minimax-enroll-20260722T031719Z\` with `BACKUP_MANIFEST.json` and SHA256 hashes |
| `agentcore_memory-memory_status` (safe read-only) | FAIL (Bifrost upstream health) | Bifrost log shows `agentcore_memory` repeatedly disconnecting + reconnecting; both `memory_status` and `startup_context` consistently timeout at the 2m tool-execution cap. See `Lifecycle` table below. |
| `agentcore_project_router-project_list` | PASS | 55 registered projects, all under `D:\github\` |
| Full native memory lifecycle (14 steps) | BLOCKED | Cannot complete from inside this client because the `agentcore_memory` upstream is currently degraded at the Bifrost layer (out of scope for this client-local config task). Re-run in a fresh MiniMax Code session. |
| New-chat rule validation | DEFERRED | Requires operator to open a new chat in MiniMax Code after restart; the new global rules load at session start. |

**Net enrollment status: `configured_restart_required` -> `awaiting_operator_import` if memory server is not healthy at the time of restart.** The MCP config and global rules are in place; the gate to `live_validated` is a fresh-chat lifecycle pass once Bifrost's `agentcore_memory` upstream is healthy.

## MCP end state (live `C:\Users\ynotf\.minimax\mcp\mcp.json`)

| Key | Type | URL | Auth | Notes |
| --- | --- | --- | --- | --- |
| `agentcore-gateway` | http | `http://127.0.0.1:8080/mcp` | `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}` | Canonical entry; timeout 300. Matches `renderers/gateway-clients/minimax.json` and `contracts/agentcore-gateway-client.json` `client_render_hints.minimax`. |
| `matrix` | n/a (CLI) | n/a | env `MATRIX_BASE_URL=https://agent.minimax.io` | Built-in media/web search tool. Out of scope (not a Bifrost upstream). |
| `cu` | streamable-http | `http://127.0.0.1:15321/mavis/mcp/cu` | none | Built-in Computer-Use companion. Out of scope. |
| `trash` | streamable-http | `http://127.0.0.1:15321/mavis/mcp/trash` | none | Built-in recoverable-deletion companion. Out of scope. |

**No direct duplicate baseline upstreams served by Bifrost were found in this client.** No removal was performed.

## Forbidden-route audit (live `tools/list`)

| Pattern | Present? |
| --- | --- |
| swarm* | no |
| psql / postgres | no |
| bifrost_admin / bifrost-admin / admin | no |
| desktop-commander | no |
| global-memory-gateway | no |
| context7 | no |
| mem0 | no |
| composio | no |
| hostinger | no |
| whole-drive filesystem root | no (filesystem bounded to `D:\github`) |

## Bifrost runtime caveats observed

- `serena` upstream is in a known-disconnected state at the Bifrost layer (`failed to initialize MCP client after 5 retries: transport error: context deadline exceeded`); tools still appear in `tools/list` but tool calls will time out. Documented in `MASTER_CONFIG_AND_PROMPT.md` and `ops/bifrost/evidence/`.
- `agentcore_memory` upstream repeatedly disconnects and reconnects during the validation window; both `memory_status` and `startup_context` consistently time out at the 2m Bifrost tool-execution cap. The underlying server `D:\github\agentcore-control-plane\scripts\agentcore_memory\server.py` exists and is 68426 bytes; the issue is at the gateway/upstream transport layer. This is **outside the scope of the MiniMax Code IDE config task** ("Do not edit files in agentcore-gateway project"). Surfaced for follow-up; does not block the IDE-side config enrollment.

## Lifecycle (HTTP diagnostic, not native — see Status table)

| Step | Tool | Diagnostic result | Native result |
| --- | --- | --- | --- |
| 1 | `agentcore_project_router-project_list` | PASS (55 projects) | n/a — tool not exposed as a function in this session |
| 2 | `agentcore_project_router-project_activate` | not retried (would mutate active-project.json; out of scope) | n/a |
| 3 | `agentcore_memory-session_open` | BLOCKED — `agentcore_memory` upstream timeouts | n/a |
| 4 | `agentcore_memory-startup_context` | FAIL (2m timeout) | n/a |
| 5 | `agentcore_memory-append_event` (idempotency) | BLOCKED — upstream | n/a |
| 6 | repeat append + idempotent_replay | BLOCKED — upstream | n/a |
| 7 | `agentcore_memory-retrieve_context` (pagination) | BLOCKED — upstream | n/a |
| 8 | `agentcore_memory-expand_source` | BLOCKED — upstream | n/a |
| 9 | `agentcore_memory-build_handoff` | BLOCKED — upstream | n/a |
| 10 | `agentcore_memory-session_close` | BLOCKED — upstream | n/a |
| 11 | resume same session | BLOCKED — upstream | n/a |
| 12 | switch projects + isolation | BLOCKED — upstream | n/a |
| 13 | switch back + continuity | BLOCKED — upstream | n/a |
| 14 | confirm exactly 10 agentcore_memory tools | PASS (10 tool names enumerated above) | n/a |

`agentcore_memory-memory_status` (safe read-only) also FAIL (2m timeout). Re-runs in fresh session are needed once the upstream is healthy.

## Global rules (live `C:\Users\ynotf\.minimax\AGENT.md`)

Replaced the prior 1195-line Codex-flavored file with a 60-line canonical rendering of `ide-profiles/minimax/GLOBAL_RULES.md` (derived from `contracts/global-agent-policy.yaml` policy_revision `2026-07-17`). The new file:

- Codifies all 19 mandatory rules from the global policy (Authority, Single-gateway, Swarm isolation, New-Project Bootstrap, Effectively-unbounded durable memory, Canonical memory recovery, Continuous durable capture, Milestone execution, Macro/Micro steps, Evidence-backed checklists, Context Fabric checkpoints, Arabold exact-version docs, Milestone tool audits, OpenRouter MCP operating rules, Progressive tool disclosure, Project/worktree write boundaries, Secrets policy, No direct database access, Git safety).
- Adds the four session-startup / tool-use / write-boundaries / completion sections required by the new prompt.
- Names the matching IDE profile, the canonical policy source, the live MCP config target, and the source-controlled renderer.
- Re-states the "exactly ten agentcore-memory tools" invariant and the `4096`-is-legacy-only rule.
- Notes the `live_global_rule_target: unverified` product limitation.
- Names MiniMax Code's local companion entries (matrix, cu, trash) explicitly so future agents do not flag them as gateway duplicates.

`C:\Users\ynotf\.minimax\rules\agentcore-memory.md` was also rewritten to:

- Repoint the authority chain from the legacy `D:\workspace\AGENTS.md` to the canonical `D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml` (with the explicit "if this file and any other authority document drift, the canonical policy wins" precedence rule).
- Add the exact-10-tool surface, idempotency-key requirement, and project-isolation requirement as code-level rules.
- Keep the OpenRouter workspaces section (operator's existing private config) but not the legacy "D:\workspace\AGENTS.md wins" line that contradicted AgentCore authority.

## Backups (outside Git)

```
E:\AgentCore-Backups\minimax-enroll-20260722T031719Z\
  BACKUP_MANIFEST.json
  mcp\mcp.json                sha256 C267EC9734A2A0BB396941FCFA734CEC40ED917B33C84A853095BD48CB09CBBD
  AGENT.md                    sha256 BE118D8FFAA8930DB4EF910FD6B395A574AC7AC7D2363679D912436A4B74CBF7
  rules\agentcore-memory.md   sha256 72465E7C99DE3612C17D12ED170AE6FC6E70DF8431BE1BAD4EA700BEC43BFEF0
```

## Source-controlled changes (committed in this audit pack)

| File | Change |
| --- | --- |
| `audits/MINIMAX_CODE_GATEWAY_ENROLLMENT_2026-07-21.md` (this file) | New — sanitized enrollment evidence |
| `audits/MINIMAX_CODE_MEMORY_LIFECYCLE_2026-07-21.json` | New — lifecycle diagnostic results (only steps that returned a result; upstream-blocked steps recorded as `BLOCKED`) |
| `ide-profiles/minimax/IDE_PROFILE.yaml` | `last_validation_date` set to `2026-07-21` |

## Invariants preserved

- No `.env` files created.
- No secrets printed in full (Bearer prefix `sk-bf-ag` and length 80 only; never the value).
- No Bifrost runtime / no `H:\AgentRuntime\bifrost\config.json` / no scheduled task changes.
- No other IDE config touched (Cursor, Codex, Claude, Cherry, Antigravity, Open Interpreter, OpenClaw, ClawX all left untouched).
- No Swarm product install touched.
- No `C:\Users\ynotf\.mavis\` touched (separate Mavis IDE).
- No `D:\MCP-Control-Plane\` treated as authority.
- No raw SQL / no direct PostgreSQL access.
- No whole-drive filesystem root exposed.
- No Git push/pull/merge/rebase performed in this turn.
- Pre-cutover `mcp.json` content unchanged (it was already correct).

## Remaining operator actions

1. **Restart MiniMax Code** to pick up the new `AGENT.md` global rules.
2. **Open a fresh chat** in any project and confirm the agent runs the full memory lifecycle (project_activate -> session_open -> startup_context -> append_event with deterministic idempotency key -> retrieve_context with pagination -> expand_source -> build_handoff -> session_close; resume; project isolation; tool-surface count = 10). Per `ide-profiles/minimax/VALIDATION.md` steps 1-18.
3. **Investigate `agentcore_memory` upstream timeouts at the Bifrost layer** if the lifecycle still fails after the rules are loaded. The issue is transport-layer (`disconnected -> reconnected` cycle in `H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log`), not a MiniMax Code config issue. Document and fix at the Bifrost runtime layer; **not in scope for this client-local enrollment task**.
4. **Optional cleanup** of `C:\Users\ynotf\.minimax\agents\mavis\agent.md` (per-agent Mavis system prompt inside MiniMax Code's data dir) — still references retired `global-memory-gateway`, `D:\MCP-Control-Plane`, and "OpenClaw is source of truth". Out of scope for the IDE config task; needs separate operator approval because it is a per-agent persona file rather than an IDE global-rules file.

## Rollback

```powershell
# Restore the prior Codex-flavored AGENT.md, rules file, and mcp.json (unchanged but backup taken)
Copy-Item -Force 'E:\AgentCore-Backups\minimax-enroll-20260722T031719Z\AGENT.md'          'C:\Users\ynotf\.minimax\AGENT.md'
Copy-Item -Force 'E:\AgentCore-Backups\minimax-enroll-20260722T031719Z\rules\agentcore-memory.md' 'C:\Users\ynotf\.minimax\rules\agentcore-memory.md'
# mcp.json was not modified by this enrollment; the backup is a safety copy.
```
