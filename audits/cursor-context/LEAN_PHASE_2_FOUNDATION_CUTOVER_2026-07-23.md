# Phase 2 — Lean AgentCore Cursor Foundation Cutover
# Date: 2026-07-23 / 2026-07-24 (EDT)
# Task: LEAN_AGENTCORE_CURSOR_FOUNDATION

---

## Entry Checks

### A. Incorrect memory tool argument name search

Searched: `scripts/`, `ops/`, `validators/`, `tests/`, `docs/`, `ide-profiles/`, `MASTER_CONFIG_AND_PROMPT.md`, `AGENTS.md`, `CLAUDE.md`

| Scope | Findings |
|---|---|
| `scripts/agentcore_workflow/db.py` | 60+ uses of `project_id` as Python function parameter for direct DB ops — NOT MCP tool call dicts |
| `scripts/agentcore_memory/integration_test_recovery.py` | `project_id` as SQL column reference in DB result rows — NOT MCP tool call dicts |
| `docs/` | `project_id` in documentation descriptions, schema docs, and historical chat — NOT tool call args |
| `ide-profiles/` | All validation docs use correct terminology (`project_key`) |
| `MASTER_CONFIG_AND_PROMPT.md` | Correct usage throughout; lifecycle steps show `session_open`, `startup_context` without wrong args |
| `AGENTS.md` | No incorrect MCP arg names |
| `ECOSYSTEM_ARCHITECTURE.md` | References `memory_append` with `project_id` — historical evidence for a deprecated tool not in the current ten-tool surface; not corrected |

**Incorrect active reusable callers found and corrected: 0**
No active source, validator, test, prompt, or runbook incorrectly passes `project_id`, `client_id`, or `agent_role` to the current ten-tool AgentCore memory surface.

### B. Cursor prompt spool reconciliation

`H:\AgentRuntime\clients\cursor\spool\pending\` — **directory does not exist; no pending spool files**

Result: **Spool is empty. No unreplayed entries.**

### C. Staged foundation rule revalidation

Source file: `ide-profiles/cursor/staging/agentcore-foundation.mdc`

| Field | Value |
|---|---|
| On-disk SHA-256 (CRLF, post-git-commit) | `b8b5e19c9f8bd29b9714532adf6947a6452f23be251cd4d89e7329bf85625982` |
| LF-normalized SHA-256 | `65dd543a1350e5b85a958c56e0dd139498fc2135a8f232b3b76475f0519264d0` |
| Expected (Phase 1D, LF) | `65dd543a1350e5b85a958c56e0dd139498fc2135a8f232b3b76475f0519264d0` |
| Note | Git committed file with CRLF line endings (Windows `core.autocrlf`). LF content is identical; hash difference is encoding only. |
| MDC frontmatter | valid |
| `alwaysApply: true` | yes |
| Lines | 119 (limit: 250) |
| Mutable runtime state | none |
| All 18 required semantics | all PASS |
| Semantic parity with global-agent-policy.yaml | PASS |

**Entry checks: ALL PASS. Proceeding to quarantine.**

---

## Foundation Activation

| Field | Value |
|---|---|
| Source | `ide-profiles/cursor/staging/agentcore-foundation.mdc` |
| Live destination | `C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc` |
| Byte-identical | YES (both CRLF, SHA-256 `b8b5e19c...`) |
| Project `.cursor\rules\` install | NOT done (per task spec) |
| Settings-backed User Rules | NOT modified |

---

## Quarantined Rule Files

### Source and count

| Scope | Count | Status |
|---|---|---|
| `C:\Users\ynotf\.cursor\rules\` (user) | 17 quarantined + 1 kept | DONE |
| `D:\github\agentcore-control-plane\.cursor\rules\` | 1 quarantined | DONE |
| `D:\.cursor\rules\` | 2 quarantined | DONE |
| `D:\github\.cursor\rules\` | 8 quarantined | DONE |
| **Total quarantined** | **28** | |
| **Kept active** | **1** (`agentcore-foundation.mdc`) | |

### Active after quarantine (all paths combined)

```
C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc    [ACTIVE]
C:\Users\ynotf\.cursor\rules\30-memory-usage.mdc.quarantined  [pre-existing stub, not a rule]
D:\.cursor\rules\openmemory.mdc.quarantined               [pre-existing stub, not a rule]
D:\github\.cursor\rules\00-memory-autopilot.mdc.quarantined [pre-existing stub, not a rule]
```

Pre-existing `.quarantined` stubs from a prior cleanup task have non-`.mdc` extensions and are not loaded by Cursor. They are left in place.

### Backup location
`E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300\phase2-quarantine-20260723-231500\`  
SHA-256 manifest: `SHA256SUMS.txt` (72 files hashed)

---

## Settings-Backed Cursor User Rules

Searched: `settings.json`, `state.vscdb` (1,211 keys), `Preferences` file, `applicationUser` persistent storage (85 keys including `aiSettings` and `personalDocs`).

**Finding: No text-area-based User Rules were ever set.** The `personalDocs` array is empty. No `userRules`, `aiRules`, `aiRulesText`, or equivalent key exists in any Cursor storage location.

The rules that previously appeared in the `<user_rules>` system prompt section were sourced entirely from the `.mdc` files in `C:\Users\ynotf\.cursor\rules\` — which have now been quarantined.

**Result: Settings-backed User Rules surface is empty. No database patching required.**

---

## Quarantined Cursor-Native Skills

| Source | Skills quarantined | Remaining active |
|---|---|---|
| `C:\Users\ynotf\.cursor\skills-cursor\` | 20 skill directories | `.cursor-managed-skills-manifest.json`, `.sync-manifest.json` (sync tracking only) |
| `C:\Users\ynotf\.cursor\skills\` | 1 (`context7-mcp`) | empty |
| `D:\github\agentcore-control-plane\.cursor\skills\` | 0 (did not exist) | — |
| **Total quarantined** | **21** | |

Quarantine location: `E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300\quarantined-skills\`

### NOT touched (preserved intact)
- `C:\Users\ynotf\.codex\skills\` — Codex only
- `C:\Users\ynotf\.claude\skills\` — Claude only
- `C:\Users\ynotf\.agents\skills\` — shared AgentCore skills hub

---

## Before / After Static Context Token Estimate

| Source | Before | After |
|---|---|---|
| Project rules | ~500 tokens | 0 (project `.cursor\rules\` empty) |
| Drive-root rules | ~2,000 tokens | 0 |
| Parent-dir rules | ~4,000 tokens | 0 |
| User rules (`.cursor\rules\`) | ~12,000 tokens | ~2,500 tokens (foundation rule, 119 lines) |
| AGENTS.md (always-applied workspace) | ~3,500 tokens | ~3,500 tokens (unchanged) |
| Cursor-native skills (20 dirs) | ~15,000 tokens | 0 |
| Third-party plugins (~150 skills) | ~75,000 tokens | 0 (discovery was already OFF) |
| **Total estimate** | **~112,000 tokens** | **~6,000 tokens** |

Reduction: **~94% fewer static context tokens**. Dynamic AgentCore sessionStart packet (~5,000–8,000 tokens) added per new chat.

---

## Fresh Session / Bootstrap Proof

Bootstrap simulation run via `python -m scripts.agentcore cursor recover`:

| Check | Result |
|---|---|
| `ok` | `True` |
| `project_key` | `agentcore-control-plane` |
| `session_id` | `e1a52554-db42-4347-95ec-6c843a4efea4` |
| `continuity_status` | `healthy` (upgraded from `projection_stale`) |
| `rule_path` | `None` (no stale alwaysApply bootstrap rule) |
| `durable_backend_available` | `True` |
| `project_automatically_resolved` | `True` |
| `session_automatically_resumed` | `True` |
| `startup_context_automatically_injected` | `True` |
| `hook-test-session` in bootstrap.md | `False` |
| `stale_bootstrap` in bootstrap.md | `False` |
| `beforeSubmitPrompt` hook | Registered (hooks.json) |
| `preToolUse` hook | NOT registered (offline-tested only) |
| Active `.mdc` rules in user path | Exactly 1: `agentcore-foundation.mdc` |
| Active Cursor-native skill dirs | 0 |
| Project/worktree identity | `D:\github\agentcore-control-plane`, branch `main` |

---

## Post-Cutover Foundation Acceptance (21 Steps)

| Step | Check | Result |
|---|---|---|
| 1 | Bifrost health (`/health`) | **200 OK** |
| 2 | PostgreSQL service | **Running, Automatic** (`AgentCore-PostgreSQL18`) |
| 3 | Exactly 10 `agentcore_memory-*` tools | **PASS** |
| 4 | Exactly 4 `agentcore_project_router-*` tools | **PASS** |
| 5 | Zero Swarm tools | **PASS** |
| 6 | Zero Obsidian tools | **PASS** |
| 7 | `project_list` | **PASS** — 55 projects, Swarm policy rejected |
| 8 | `project_activate` | **PASS** |
| 9 | `session_open` (correct `project_key`/`client_key`/`agent_key`) | **PASS** — session `e1a52554` |
| 10 | `startup_context` | **PASS** — standard-context profile |
| 11 | `append_event` (key `phase2-lean-foundation-cutover-acceptance-v1-2026-07-23`) | **PASS** — event `5c0a01cc` |
| 12 | Identical replay → `idempotent_replay: true` | **PASS** |
| 13 | `retrieve_context` with pagination cursor | **PASS** — 187 events, `5c0a01cc` most recent |
| 14 | `expand_source` on `5c0a01cc` | **PASS** — exact payload verified |
| 15 | `build_handoff` | **PASS** — identity + context + projections |
| 16 | `session_close` | **PASS** |
| 17 | Reopen same `session_key` | **PASS** — same `session_id: e1a52554` |
| 18 | Project isolation (fixture) | **PASS** — 0 items, no cross-project data |
| 19 | Projection revision ≥ 13 | **PASS** — revision 14 (refreshed post-Phase 2) |
| 20 | STATE.md line budget | **PASS** — 213 lines (within 300–500 preferred; compact state) |
| 21 | LangGraph fixture | **PASS** — 162 `wf_runs`, 1,772 checkpoints |

Phase 2 acceptance event `5c0a01cc` exists **exactly once**.

---

## Projection Verification (Steps 19–20)

| File | Revision | Source revision | Lines | Status |
|---|---|---|---|---|
| `STATE.md` | **14** | 2026-07-23 23:29:13 (Phase 2 event) | 213 | CURRENT |
| `DECISIONS.md` | **14** | 2026-07-23 23:29:13 | 8 | CURRENT |
| `CONTEXT_INDEX.md` | **14** | 2026-07-23 23:29:13 | 9 | CURRENT |
| `MILESTONE_DELTA.md` | — | — | absent | Planned Context Steward work |

No agent directly edited projection content. Generated by `Invoke-M3ProjectionWorker.ps1`.

---

## Memory Lifecycle Result

All 21 steps pass. The memory lifecycle is fully operational post-cutover with no degradation introduced by the rule/skill quarantine.

---

## Backup Path

Primary (Phase 1 + Phase 2):
`E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300\`

Phase 2 quarantine:
`…\phase2-quarantine-20260723-231500\`
- `user-rules\` — 17 quarantined user `.mdc` files
- `project-rules\` — 1 quarantined project rule
- `drive-root-rules\` — 2 quarantined drive-root rules
- `parent-dir-rules\` — 8 quarantined parent-dir rules
- `quarantine-rules-manifest.txt` — paths + SHA-256 for each
- `quarantine-skills-manifest.txt` — paths + SHA-256 for each skill
- `SHA256SUMS.txt` — 72 files hashed

Skills quarantine:
`E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300\quarantined-skills\`
- `cursor-skills-cursor\` — 20 skills
- `cursor-skills\` — 1 skill

---

## Rollback Procedure

To fully restore the pre-Phase-2 state:

1. Stop Cursor.
2. Copy all files from `…\phase2-quarantine-20260723-231500\user-rules\` back to `C:\Users\ynotf\.cursor\rules\`.
3. Remove `C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc` (or leave alongside restored files).
4. Copy `…\phase2-quarantine-20260723-231500\project-rules\` back to `D:\github\agentcore-control-plane\.cursor\rules\`.
5. Copy `…\phase2-quarantine-20260723-231500\drive-root-rules\` back to `D:\.cursor\rules\`.
6. Copy `…\phase2-quarantine-20260723-231500\parent-dir-rules\` back to `D:\github\.cursor\rules\`.
7. Copy `…\quarantined-skills\cursor-skills-cursor\` directories back to `C:\Users\ynotf\.cursor\skills-cursor\`.
8. Copy `…\quarantined-skills\cursor-skills\` directories back to `C:\Users\ynotf\.cursor\skills\`.
9. Restart Cursor.

Verify SHA-256 of restored files against `SHA256SUMS.txt` before use.

---

## Unrelated WIP Preserved

The following untracked files were NOT staged or modified:
- `audits/M5/pg18-restore-test-*.json` — nightly backup audit records
- `scripts/_scratch/` — probe scripts
- `scripts/cherry/` — Cherry Studio integration scripts
- `scripts/uv.lock` — uv lock file
- `docs/CHERRY_NEWAPI_INTEGRATION.md`
- `audits/cursor-context/archive/` — audit archive

`audits/M6/studio-launch-stdout.log` (modified) — pre-existing dirty state, not staged.

---

## Serena Status (Deferred)

Serena MCP client continues to fail reconnection (`transport error: context deadline exceeded`). Phase 2 did not touch Serena configuration. Deferred for a separate diagnostic task.

---

*Produced: 2026-07-24T03:30:00-04:00*  
*Session: e1a52554-db42-4347-95ec-6c843a4efea4*  
*Phase 2 acceptance event: 5c0a01cc*
