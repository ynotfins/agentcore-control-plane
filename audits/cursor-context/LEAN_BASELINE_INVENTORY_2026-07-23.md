# Lean AgentCore Cursor Foundation — Phase 1 Baseline Inventory
# Date: 2026-07-23
# Task: LEAN_AGENTCORE_CURSOR_FOUNDATION
# Phase: 1 — Baseline, Backup, and Active-Context Inventory

---

## A. Git Baseline

| Field | Value |
|---|---|
| Branch | `main` |
| HEAD | `24da5ff64f27d71e744987823d5d02eadd1b3300` |
| Commit message | Phase 6: quarantine contradictory memory rules, populate .cursorignore, fix env-policy frontmatter |
| Worktree | `D:\github\agentcore-control-plane` (sole worktree; no additional worktrees active) |
| Canonical repository | `D:\github\agentcore-control-plane` |

### Inherited WIP (uncommitted / untracked)

```
 M audits/M6/studio-launch-stdout.log
?? audits/M5/pg18-restore-test-20260721-033001.json
?? audits/M5/pg18-restore-test-20260722-033001.json
?? audits/M5/pg18-restore-test-20260723-033002.json
?? audits/cursor-context/CURSOR_SKILL_PLUGIN_FULL_AUDIT_2026-07-23.md
?? audits/cursor-context/archive/
?? docs/CHERRY_NEWAPI_INTEGRATION.md
?? scripts/_scratch/  (multiple probe/debug scripts)
?? scripts/cherry/    (multiple injection and scratch scripts)
?? scripts/uv.lock
```

Classification: audit files, nightly backup JSON records, scratch/probe scripts, and Cherry Studio integration work. None are secrets. None are staged. These are pre-existing dirty state — not introduced by this task.

---

## B. Current Cursor Hook Event Set

Source: `D:\github\agentcore-control-plane\.cursor\hooks.json`

| Event | Command |
|---|---|
| `sessionStart` | `powershell ... agentcore-hook.ps1 -Event sessionStart` (timeout 90s) |
| `beforeSubmitPrompt` | `powershell ... agentcore-hook.ps1 -Event beforeSubmitPrompt` (timeout 90s) |

- `preToolUse`: **NOT registered** (offline-tested per AGENTS.md; hard gate pending)
- Hook source: `.cursor/hooks/agentcore-hook.ps1` in the project repository

---

## C. Active Cursor Rules Inventory

### C1. Project rules (`D:\github\agentcore-control-plane\.cursor\rules\`)

| File | alwaysApply | Notes |
|---|---|---|
| `agentcore-env-policy.mdc` | true | AgentCore Windows env var policy (no .env, gateway routing) |

**Count: 1** — current state already lean at project level.

### C2. Drive-root rules (`D:\.cursor\rules\`)

| File | alwaysApply | Notes |
|---|---|---|
| `10-autonomous-mcp-routing.mdc` | (unknown) | MCP routing, Simplification Principle, Completion/Push Policy |
| `11-depwire-foundation.mdc` | (unknown) | DepWire mandatory foundation tool rules |

**Count: 2** — D:-drive global rules loaded for all D: projects.

### C3. Parent-directory rules (`D:\github\.cursor\rules\`)

| File | Notes |
|---|---|
| `autonomous-rule-creation.mdc` | Rule creation policy (no sprawl) |
| `auto-error-fixing.mdc` | Auto-fix syntax/import/type errors |
| `decisive-implementation.mdc` | Autonomous technical decisions |
| `post-task-cleanup.mdc` | Cleanup after tasks |
| `proactive-completion.mdc` | Complete obvious TODOs |
| `proactive-scanning.mdc` | Scan for obvious issues |
| `rule-visibility.mdc` | Don't list all rules in every response |
| `smart-assumptions.mdc` | Make reasonable assumptions |

**Count: 8** — GitHub-parent-directory global rules.

### C4. User rules (`C:\Users\ynotf\.cursor\rules\`)

| File | alwaysApply | Notable content / issues |
|---|---|---|
| `agentcore-memory.mdc` | true | Memory discipline; references stale `D:\workspace\AGENTS.md` and embeds mutable model token profiles and OpenRouter routing detail — violates stable-rule requirement |
| `context-fabric-bootstrap.mdc` | (unknown) | Context Fabric bootstrap rules |
| `00-core-evidence-first.mdc` | true | Evidence-first kernel |
| `10-mcp-tool-router.mdc` | (unknown) | MCP tool routing |
| `20-arabold-docs.mdc` | (unknown) | Arabold docs usage |
| `30-multi-agent-workflow.mdc` | (unknown) | Multi-agent workflow |
| `40-secrets-and-env.mdc` | (unknown) | Secret/env policy |
| `45-managed-config-surfaces.mdc` | (unknown) | Managed config protocol |
| `50-drive-write-boundary.mdc` | (unknown) | Drive write scope |
| `60-code-quality-habits.mdc` | (unknown) | Code quality |
| `65-task-completion-and-commits.mdc` | (unknown) | Commit/push policy |
| `70-cursor-background-agents.mdc` | (unknown) | Background agents |
| `80-agent-skills-usage.mdc` | (unknown) | Skills usage |
| `90-yolo.mdc` | (unknown) | YOLO/autonomous mode |
| `artiforge-usage.mdc` | (unknown) | Artiforge tool usage |
| `autonomous-rule-creation.mdc` | (unknown) | Duplicate of D:\github parent rule |
| `coding-standards.mdc` | (unknown) | Coding standards |
| `cursor-rules-meta.mdc` | (unknown) | Rules meta |

**Count: 18** — Large user-level rule set; several overlap or contain mutable state.

### Total active rules: 29

---

## D. Active Cursor Skills Inventory

### D1. Cursor-native skills (`C:\Users\ynotf\.cursor\skills-cursor\`)

| Skill | Notes |
|---|---|
| `automate` | Create Cursor Automations |
| `babysit` | PR merge-ready skill |
| `canvas` | Live React canvas |
| `create-hook` | Create Cursor hooks |
| `create-rule` | Create Cursor rules — **OPERATOR-ONLY per audit** |
| `create-skill` | Create Cursor skills — **OPERATOR-ONLY per audit** |
| `create-subagent` | Create subagents |
| `env-setup` | Environment setup |
| `loop` | Loop/recurring prompts |
| `migrate-to-skills` | Skills migration |
| `onboard` | Onboarding |
| `review` | Code review |
| `review-bugbot` | Bugbot review |
| `review-security` | Security review |
| `sdk` | Cursor SDK guide |
| `shell` | Shell specialist |
| `split-to-prs` | Split to PRs |
| `statusline` | Custom status line |
| `update-cli-config` | CLI config |
| `update-cursor-settings` | Settings editor — **OPERATOR-ONLY per audit** |

**Count: 20** — All Cursor-native SDK skills. Several (create-rule, create-skill, update-cursor-settings) should be operator-only.

### D2. User skills (`C:\Users\ynotf\.cursor\skills\`)

| Skill | Notes |
|---|---|
| `context7-mcp` | **UNINSTALL_FROM_CURSOR** per audit — conflicts with Arabold Docs authority |

**Count: 1** — context7 in active user skill path; scheduled for removal.

### D3. Third-party plugin cache (`C:\Users\ynotf\.cursor\plugins\cache\cursor-public\`)

| Plugin | Skill count | Recommendation (from CURSOR_SKILL_PLUGIN_FULL_AUDIT) |
|---|---|---|
| `cloudflare` | 9 | DISABLE GLOBALLY; PROJECT-SCOPE LATER |
| `context7-plugin` | 1 | UNINSTALL_FROM_CURSOR |
| `continual-learning` | 1 | QUARANTINE/UNINSTALL_FROM_CURSOR |
| `cursor-team-kit` | 17 | Mix: 6 CURATE, 11 DISABLE GLOBALLY |
| `firebase` | 11 | Mix: 1 CURATE, 10 DISABLE GLOBALLY |
| `superpowers` | 14 | Mix: 9 KEEP/ADAPT, 3 DISABLE UNTIL REPAIR, 1 OPERATOR-ONLY, 1 DISABLE-DOCTRINE |
| `twilio-developer-kit` | 55 | DISABLE/UNINSTALL GLOBALLY |
| `vercel` | 42 | Mix: 4 CURATE, 21 DISABLE, 17 EXCLUDE |

**Total plugin skills visible to Cursor: ~150 (from plugins.zip audit)**
**Directive: Third-party plugin discovery must be turned OFF during Phase 2.**

---

## E. Plugin Contributions (Current Active State)

Plugin discovery: currently **ON** (all 8 plugin caches are present and discoverable).

| Plugin | Current state | Required action |
|---|---|---|
| Continual Learning | INSTALLED; auto-trigger previously disabled | QUARANTINE/UNINSTALL |
| Context7 | INSTALLED | UNINSTALL |
| Superpowers | INSTALLED; automatic doctrine active | RETAIN source; DISABLE auto-doctrine |
| Vercel | INSTALLED | DISABLE GLOBALLY |
| Cursor Team Kit | INSTALLED | DISABLE GLOBALLY (curate subset later) |
| Firebase | INSTALLED | DISABLE GLOBALLY |
| Cloudflare | INSTALLED | DISABLE GLOBALLY |
| Twilio Developer Kit | INSTALLED | DISABLE/UNINSTALL GLOBALLY |

---

## F. Settings-Backed User Rules (Cursor settings.json)

Location: `C:\Users\ynotf\AppData\Roaming\Cursor\User\settings.json`

Cursor-relevant settings found:
```json
{
  "cursor.composer.queueMessageDefaultBehavior": "stop-and-send",
  "cursor.composer.usageSummaryDisplay": "always"
}
```

No explicit plugin enable/disable flags in settings.json — plugin state is managed by Cursor's internal extension registry.

AGENTS.md user rules (workspace-level AGENTS.md): present and active as always-applied workspace rule.

---

## G. MCP Configuration

Cursor live MCP config (`C:\Users\ynotf\.cursor\mcp.json`):
- **Exactly 1 server entry**: `agentcore-gateway` at `http://127.0.0.1:8080/mcp`
- No direct upstream MCP servers in Cursor config
- Compliant with single-gateway policy

---

## H. Before-State Acceptance Baseline

### H1. Infrastructure

| Check | Result |
|---|---|
| Bifrost health (`GET /health`) | **200 OK** |
| PostgreSQL service (`AgentCore-PostgreSQL18`) | **Running, Automatic** |
| PostgreSQL endpoint | `127.0.0.1:55433` confirmed via memory_status |
| Migrations applied | m2.001, m3.001, m3.002, m4.001_quarantine_filter, m5.001, m6.001, m8.001, m8.002 |
| LangGraph module importable | **PASS** (`agentcore_workflow.db` imports OK) |
| Cognee status | available (v1.3.0 in isolated venv) |
| agentcore-memory version | v0.6.0 |

### H2. Tool Counts

| Surface | Expected | Actual | Status |
|---|---|---|---|
| `agentcore_memory-*` tools | 10 | **10** | **PASS** |
| `agentcore_project_router-*` tools | 4 | **4** | **PASS** |
| Playwright tools | 24 (spec) | 24 (via MCP catalog) | **PASS** |
| Swarm tools | 0 | 0 | **PASS** |
| Obsidian tools | 0 | 0 | **PASS** |

### H3. Memory Lifecycle

| Tool | Result | Notes |
|---|---|---|
| `memory_status` | **PASS** — healthy, DB reachable | Baseline confirmed |
| `project_activate` | **PASS** — agentcore-control-plane activated | Normal activation path |
| `project_list` | **PASS** — 55 projects listed | Isolation confirmed |
| `session_open` | **FAIL — internal error (sanitized)** | Pre-existing issue; server-side error |
| `startup_context` | **FAIL — internal error (sanitized)** | Pre-existing issue; same root cause |
| `retrieve_context` | **FAIL — internal error (sanitized)** | Pre-existing issue; same root cause |
| `expand_source` | NOT TESTED (depends on session) | — |
| `append_event` | FAIL (logged in Bifrost — same error pattern) | Pre-existing |
| `build_handoff` | NOT TESTED | — |

**Pre-existing memory lifecycle issue:** Bifrost routes `memory_status` successfully but all session-management tools (`session_open`, `startup_context`, `retrieve_context`, `append_event`) return internal errors. The Bifrost stdout log shows these tool handlers start then immediately return errors. The agentcore-memory v0.6.0 server process is live (health probe succeeds), but the session management layer is degraded. This was the state at the start of this task — not introduced by Phase 1.

**Implication for Phase 2:** The rule/skill teardown must not be cited as the cause of this degradation. This is a pre-existing issue that must be independently investigated and repaired before the memory lifecycle acceptance gate in Phase 7 can pass.

### H4. Serena Status

Bifrost stdout log shows Serena MCP client repeatedly failing to reconnect (`transport error: context deadline exceeded`). Serena is unhealthy in the current Bifrost upstream pool. This is a separate pre-existing issue.

---

## I. Generated Projection State

| File | Last modified | Size | Status |
|---|---|---|---|
| `.agentcore/STATE.md` | 2026-07-19 21:00 | 30 lines | **STALE** (4 days old) |
| `.agentcore/DECISIONS.md` | 2026-07-19 21:00 | 5 lines | **STALE** |
| `.agentcore/CONTEXT_INDEX.md` | 2026-07-19 21:00 | 6 lines | **STALE** |
| `.agentcore/MILESTONE_DELTA.md` | NOT FOUND | — | **MISSING** |

STATE.md at 30 lines is well within the 300–500 preferred range but is 4 days old relative to the most recent commits (HEAD is from ~2026-07-21+). Projections are stale because the memory session layer is degraded (cannot append events or rebuild projections through normal lifecycle).

---

## J. Rollback Backup

### Location
`E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300\`

### Contents backed up

| Directory | Contents |
|---|---|
| `project-rules\` | `D:\github\agentcore-control-plane\.cursor\rules\*.mdc` (1 file) |
| `drive-root-rules\` | `D:\.cursor\rules\*.mdc` (2 files) |
| `parent-dir-rules\` | `D:\github\.cursor\rules\*.mdc` (8 files) |
| `user-rules\` | `C:\Users\ynotf\.cursor\rules\*.mdc` (18 files) |
| `cursor-skills-cursor\` | `C:\Users\ynotf\.cursor\skills-cursor\` (20 skill directories + manifests) |
| `cursor-skills\` | `C:\Users\ynotf\.cursor\skills\` (1 skill: context7-mcp) |
| `hooks\` | `.cursor/hooks.json` + hook scripts |
| `projections\` | `.agentcore/STATE.md`, `DECISIONS.md`, `CONTEXT_INDEX.md` |
| `bifrost-config\` | `H:\AgentRuntime\bifrost\config.json` (sanitized; no secrets resolved) |
| Root | `AGENTS.md`, `CLAUDE.md` |

### SHA-256 manifest
`E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300\SHA256SUMS.txt`
Total files hashed: **85**

### What was NOT backed up (intentionally)
- `C:\Users\ynotf\.cursor\mcp.json` — may contain resolved virtual key values; structure documented: exactly 1 server (`agentcore-gateway`)
- `C:\Users\ynotf\.cursor\plugins\cache\` — third-party plugin cache (~150 skill files); source-controlled by plugins; the audit CSV/MD captures their full inventory
- Node_modules, caches, generated runtime state
- PostgreSQL data
- Secret-bearing files

---

## K. Summary of Issues Requiring Attention

| # | Issue | Severity | Phase impact |
|---|---|---|---|
| K1 | `session_open`, `startup_context`, `retrieve_context`, `append_event` all fail with internal error | **HIGH** | Phase 7 acceptance cannot pass until this is repaired |
| K2 | Serena MCP client failing to reconnect in Bifrost | MEDIUM | Serena unavailable; DepWire local is available as fallback |
| K3 | Generated projections stale (4 days old; `MILESTONE_DELTA.md` missing) | MEDIUM | Cannot generate fresh STATE until memory lifecycle repaired |
| K4 | `agentcore-memory.mdc` user rule references stale `D:\workspace\AGENTS.md` authority and contains mutable model token profiles | LOW | Will be quarantined in Phase 2 |
| K5 | 18 user rules + 8 parent-dir rules + 2 drive-root rules = 28 rules loaded globally beyond the 1 project rule | INFORMATIONAL | Phase 2 will quarantine non-foundational rules |
| K6 | ~150 third-party plugin skills discoverable (Twilio, Firebase, Cloudflare, Vercel, etc.) | INFORMATIONAL | Phase 2 will disable third-party discovery |
| K7 | `context7-mcp` skill in active user skill path | INFORMATIONAL | Phase 2 will remove |
| K8 | LangGraph workflow CLI unavailable via system Python (needs venv) | LOW | Not blocking; DB connectivity confirmed via memory_status |

---

## L. Active Cursor Context: Before-State Token Footprint Estimate

| Source | Rule/skill count | Estimated token load |
|---|---|---|
| Project rule (`agentcore-env-policy.mdc`) | 1 | ~500 tokens |
| Drive-root rules | 2 | ~2,000 tokens |
| Parent-dir rules | 8 | ~4,000 tokens |
| User rules | 18 | ~12,000 tokens |
| AGENTS.md (always-applied workspace rule) | 1 | ~3,500 tokens |
| Cursor-native skills (20) | 20 | ~15,000 tokens (discovery overhead) |
| Third-party plugins (~150 skills) | ~150 | ~75,000 tokens (if all injected) |
| **Total estimate** | | **~112,000 tokens context load** |

Post-lean-foundation target: ~5,000–8,000 tokens for static context (1 foundation rule + session startup packet).

---

## M. Acceptance Gate: Phase 1 Pass/Fail

| Gate | Status |
|---|---|
| Git baseline recorded | PASS |
| Rollback backup created with SHA-256 manifest | PASS |
| Bifrost health 200 | PASS |
| Exactly 10 agentcore-memory tools | PASS |
| Exactly 4 project-router tools | PASS |
| Zero Swarm tools | PASS |
| Zero Obsidian tools | PASS |
| `memory_status` succeeds | PASS |
| `session_open` succeeds | **FAIL (pre-existing)** |
| `startup_context` succeeds | **FAIL (pre-existing)** |
| `retrieve_context` succeeds | **FAIL (pre-existing)** |
| `expand_source` | NOT TESTED (session dependency) |
| `append_event` succeeds | **FAIL (pre-existing)** |
| Project isolation succeeds | PASS (`project_activate` OK; 55 projects listed with Swarm rejected) |
| LangGraph DB reachable | PASS (via memory_status migrations confirmed; direct Python import OK) |
| LangGraph fixture green | UNABLE TO TEST (workflow CLI needs venv; not blocking baseline) |
| PostgreSQL service Running+Automatic | PASS |
| Generated projection state reported | PASS (stale noted) |
| Active-context inventory produced | PASS |

**Phase 1 result: CONDITIONAL PASS**

The baseline is documented. Three pre-existing memory lifecycle failures (`session_open`, `startup_context`, `retrieve_context`) are recorded. These failures predate this task. Proceeding to Phase 2 requires operator acknowledgment that the final acceptance gate (Phase 7) will require memory lifecycle repair as a separate prerequisite — or that the repair is included in scope before Phase 7.

**The rule/skill teardown in Phase 2 MUST NOT be held responsible for the pre-existing memory lifecycle degradation.**

---

*Produced by: AgentCore baseline auditor*
*Timestamp: 2026-07-23T22:43:00-04:00*
*Rollback backup: E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300*
