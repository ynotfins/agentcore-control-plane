# AgentCore Full-Recovery Live Rollout Handoff — 2026-07-17

## Status

**LIVE.** Backend deployed and live-validated through Cursor. Universal IDE self-enrollment pending
for Codex, Claude Code, Claude Desktop, MiniMax, Mavis, Antigravity, and Open Interpreter.

## Completion Language

    UNBOUNDED DURABLE MEMORY IMPLEMENTED — LIVE IDE SELF-ENROLLMENT PENDING

## What Was Deployed

### Source Branch
`task/unbounded-durable-memory` — worktree at `D:\github\agentcore-control-plane-unbounded-memory`
Commit: `59114a8f3c72f8b5a23e64eb195e3ecda078f46a` (fix(memory): harden project recovery boundaries)

### Database Migration Applied
`m3.002` — effectively-unbounded recovery, versioned summary correction, model-aware context
profiles, governed project snapshots
Applied: 2026-07-17 01:47:30 -04:00 by postgres on 127.0.0.1:55433 (agent_core)

New tables created:
- `agentcore.model_context_profiles` — 6 profiles seeded (acceptance-small through future-above-million)
- `agentcore.recovery_operations` — paginated recovery audit trail
- `agentcore.project_snapshots` — governed snapshot metadata
- `agentcore.model_context_profile_aliases` — backward-compatible aliases

### Server Deployed
`agentcore-memory` 0.5.0 → **0.6.0**
Server path at deployment: `D:\github\agentcore-control-plane-unbounded-memory\scripts\agentcore_memory\server.py`
Registry updated: `contracts/bifrost-upstream-mcp-registry.json` (path pointed to unbounded-memory worktree)

> **Note (2026-07-17 M8 consolidation):** Server path was corrected to canonical repo as part of the M8 worktree retirement.
> Current canonical server path: `D:\github\agentcore-control-plane\scripts\agentcore_memory\server.py`
> See `audits/M8/UNBOUNDED_DURABLE_MEMORY_RELEASE_ACCEPTANCE.md` §2 for source path correction evidence.

### Bifrost Restarted
Scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` restarted at 2026-07-17 01:50:22 -04:00
Gateway health: `{"status":"ok"}` on http://127.0.0.1:8080/health

### Backup Taken Before Migration
`E:\AgentCoreArchive\agentcore-memory\backups\pg18\20260717-014501`
Databases: agent_core (448 restore entries), cognee_core (171 restore entries)
G: secondary backup not available (drive not mounted); E: primary confirmed.

## Live Acceptance Evidence

| Test | Result |
|---|---|
| memory_status | PASS — version 0.6.0, migrations m2.001/m3.001/m3.002/m4.001/m5.001/m6.001 visible |
| session_open | PASS — session_id e04dbf2a, project_id 8a3bbea1 |
| startup_context | PASS — profile standard-context, hard_context_limit 131072, durable_memory_contract: effectively_unbounded_by_model_token_limits |
| append_event | PASS — event_id f765b341 recorded |
| retrieve_context | PASS — stable pagination, 5 items/page, continuation_cursor, content_hashes, exact_expansion_references, omitted_item_count |
| expand_source | PASS — exact original event returned with content_sha256 |
| session_close | PASS — session e04dbf2a closed |
| recovery unit suite | 23/23 PASS |
| M3 full recovery integration | PASS — 269 events, 6 profiles, future_limit 2,000,000 |
| contract validator | 111 checks PASS |
| IDE renderer check | All 8 IDE GLOBAL_RULES current |
| control-plane source validator | All PASS |
| Context Fabric drift | 0.0% (LOW severity) |
| secret scan | Clean |

## Context Profile Verification

| Profile | hard_context_limit | production_profile | Verified |
|---|---|---|---|
| acceptance-small | 4,096 | false | PASS (not a production default) |
| legacy-4096 | 6,144 | false | PASS |
| standard-context | 131,072 | true | PASS |
| large-context | 262,144 | true | PASS |
| one-million-context | 1,000,000 | true | PASS (not a durable memory cap) |
| future-above-million | 2,000,000 | false | PASS (extensibility proof) |

The `hard_context_limit` field accepts any positive bigint. No universal maximum is enforced.

## Durable Memory Contract

AgentCore durable project memory is effectively unbounded by model token limits.

- A model context limit controls only one assembled active request.
- A one-million-token profile is a supported active-context profile, not a storage or retention ceiling.
- The complete project path remains retained locally in PostgreSQL.
- Compaction changes only the active representation; it never deletes or replaces canonical originals.
- Bad summaries can be superseded and rebuilt from exact source edges.
- Full history is recoverable through stable chronological pagination.
- Cold evidence on E: remains searchable and exactly expandable.
- Agents query agentcore-memory before asking the operator to repeat project history.

## Universal IDE Self-Enrollment Package

All eight IDE profiles and GLOBAL_RULES are current and rendered from `contracts/global-agent-policy.yaml`.
The install prompt at `docs/prompts/install-agentcore-gateway-in-ide.md` is complete.

Each IDE must:
1. Identify its own profile.
2. Obey its own editability mode.
3. Back up its own live configuration.
4. Preserve its model and context-window configuration.
5. Install its tailored global rules.
6. Add exactly one logical MCP entry: `agentcore-gateway` at `http://127.0.0.1:8080/mcp`.
7. Validate the exact ten agentcore-memory tools.
8. Test: memory_status, session_open, startup_context, append_event, retrieve_context, expand_source, session_close.
9. Report factual status: live_validated / awaiting_restart / awaiting_operator_import / unsupported_with_reason.

Cursor: **live_validated** (2026-07-17)
All other IDEs: awaiting_operator_import (operator must paste install prompt into each IDE).

## Remaining Steps

1. For each non-Cursor IDE, paste `docs/prompts/install-agentcore-gateway-in-ide.md` into a new agent session.
   The agent will identify its own profile, configure only itself, and report factual status.
2. After each IDE completes its own self-enrollment and validation, update `IDE_PROFILE.yaml` `last_validation_date`.
3. After all supported IDEs report `live_validated`, change completion language to:
       GLOBAL MEMORY AND ROLLING CONTEXT FULLY DEPLOYED

## Rollback

- Database rollback: `m3.002 DOWN` migration is intentionally guarded — refuses to run if recovery, snapshot,
  or summary-correction records exist. Rollback requires operator-approved pg_restore to `20260717-014501`.
- Server rollback: revert `bifrost-upstream-mcp-registry.json` path to main repo, re-render, restart Bifrost.
- Source rollback: revert to branch `task/authority-reconciliation` (pre-M3.002 head at `f705d7b`).

## Authority

- BLUEPRINT.md remains locked architecture authority.
- `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` is implementation authority.
- `docs/handoffs/AGENTCORE_FULL_RECOVERY_SOURCE_HANDOFF_2026-07-16.md` is the source acceptance record.
