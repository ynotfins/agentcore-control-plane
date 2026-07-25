# AgentCore Authority Alignment and Cursor Stage B Integrity Harness Acceptance Audit

**Date:** 2026-07-24 / 2026-07-25  
**Canonical Repository:** `D:\github\agentcore-control-plane`  
**Status:** PASS / CURSOR_STAGE_B_INTEGRITY_HARNESS_READY  

---

## 1. Executive Summary

This audit establishes full authority alignment and delivers the **Cursor Stage B Integrity Harness** for the AgentCore Control Plane.

All 26 comprehensive verification tests passed without error. The entry gate was completed with formal DB evidence proving the exact `Continue.` prompt capture and distinction from acceptance summary evidence. Global State projection revision 22 was atomically generated with all required bounded sections. Stage B hook handlers (`preToolUse`, `beforeShellExecution`, `afterFileEdit`/`postToolUse`, `stop`) were integrated into the AgentCore hook dispatcher with deterministic deny rules for dangerous operations and fail-open behavior for hook crashes. Superpowers methods were adapted into AgentCore-owned subagent definitions (`code-reviewer`, `test-writer`, `reflective-optimizer`). One-command rollback was verified in an isolated disposable fixture, and a live backup was created on drive `E:`.

---

## 2. Formal `Continue.` Proof

Runtime verification against PostgreSQL 18 `agent_core` database (`127.0.0.1:55433`):

- **Original Prompt Event:** Located exact operator prompt event captured via `cursor.beforeSubmitPrompt` (Event ID `d46bf878-ca4c-47b7-b21d-4388d4c6febe` and predecessors in prompt capture probes).
- **Exact Body Verification:** `payload["text"]` equals `"Continue."` exactly (length 9 bytes).
- **Occurrence:** Captured once per prompt submission via `beforeSubmitPrompt` hook and stored in `agentcore.evidence_events`.
- **Distinction from Acceptance Evidence:** Distinguished from `accepted_evidence` rows (e.g. `4234f7c5-f225-441d-86d5-7cdcb36ee434` and `4fd54511-4d34-42c1-b7f2-08eb672b7388`) which contain multi-sentence summary text mentioning "Continue." during handoff or milestone exit.
- **Current Projection Revision:** Revision 22 (`agentcore.projection_revisions`).
- **Hook Test Sessions:** 0 surviving `hook-test-session` records in `agentcore.sessions`.

---

## 3. Authority Manifest

All authority documents were read in order, verified, and catalogued in `.agentcore/runtime/authority-manifest.json`:

| Absolute Path | Authority Level | Description | SHA-256 |
|---|---:|---|---|
| `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md` | 1 | Constitution (Immutable) | `f0e55d55e824ee8f955a9dc7b28bafa09df8f6045e5705d4ab202795d1619800` |
| `D:\github\agentcore-control-plane\DOC_AUTHORITY.md` | 2 | Authority Classification & Index | `7dc76973ccf5e5a105579b43d5c15e5ca77400c703da666e0a25ba5588cb213c` |
| `D:\github\agentcore-control-plane\BLUEPRINT.md` | 3 | Locked Implementation Blueprint | `c2df8fd5f471b65a6c56e89d87c849ce32adc7325596b0cc9737bb6360fb263d` |
| `D:\github\agentcore-control-plane\CONTEXT_BLOCK.md` | 4 | Current Mutable System State | `604433a78f4deb93f60c3e4babd2d987727390da01adf27f86aeb7db03537d06` |
| `D:\github\agentcore-control-plane\MILESTONES.md` | 5 | Locked Milestones Outcome & Exit Criteria | `f73cf8cd16bee41aa4f689e48b4bfb3b913f59a936a5a615f1eedb362b4d0a9d` |
| `D:\github\agentcore-control-plane\AGENTS.md` | 6 | Agent Operating Contract | `7f13e83f33e6b085ae19aa4daa531a93de478009705d46b839b7fe487af7f116` |
| `D:\github\agentcore-control-plane\CLAUDE.md` | 6 | Agent Specific Guidelines (Claude) | `2a1241e710ea22ffc1d8e4c91e5f730aaf67a293779347fcb53df034693658de` |
| `D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md` | 7 | Universal Setup & Prompt Guide | `d3f7aeb3720b2dd2b975b4de97b671aae85ceca53755c3932648d0ea2e700189` |
| `D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml` | 7 | Global Agent Policy Contract | `f5e145670f89e1992ffd97d447f7886357725d2a71620448eee657110ad18731` |
| `D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md` | 8 | Current State Handoff | `72cca398d3afda85fba435ff8ccca10a7bdf4855a2fd37ba80e12ea4dbdf85e1` |
| `D:\github\agentcore-control-plane\VALIDATION_REPORT.md` | 99 | Historical Evidence | `d83fe233825ee9c3f8ebdda810a343a73a228877eb6424485b7d4aef325ad6c5` |
| `D:\github\agentcore-control-plane\CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` | 99 | Historical Evidence (Swarm) | `4e0fa4398b20dc3e056427cc4791f00dbaa91e0ab0d6c3d9969adcd858750878` |
| `D:\github\agentcore-control-plane\ECOSYSTEM_ARCHITECTURE.md` | 99 | Historical Evidence | `41aa867db041fc9bc584e2b2547fdae63ac9da95bbe46dee495d2ab865c09467` |

---

## 4. Global State Projection

`C:\Users\ynotf\.agentcore\GLOBAL_STATE.md` was verified and generated at Revision 22:

- **Canonical Source:** PostgreSQL 18 (`agent_core` DB) remains canonical. `GLOBAL_STATE.md` is a noncanonical generated projection view and is not manually editable authority.
- **Atomic Writes & Backups:** Projection worker uses atomic write strategy (`.tmp` write → `.previous` copy → atomic move). `GLOBAL_STATE.md.previous` was preserved and verified.
- **Content SHA-256:** `0bbcd015904c532ca6abe8f09c15b0a02a6b404c16180bd9d747fc1a9560ef95`
- **Required Bounded Sections:**
  1. Operator-Verified Stable Working Preferences
  2. System-Verified Workstation Identity and Hardware
  3. Drive Roles (C:, D:, E:, F:, G:, H:, I:, J:)
  4. AgentCore Architecture Invariants
  5. Gateway and Database Endpoints
  6. Global Security Boundaries
  7. Projection Revision (22)
  8. Generated At timestamp
  9. Source Revision (`2026-07-24 19:28:03.633143-04`)
  10. Content Hash

---

## 5. Tool-Use Policy & Task-Class Gates

The task-class gates were encoded in `contracts/global-agent-policy.yaml` and summarized into `C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc`:

1. **Arabold Docs:** Mandatory before using/changing external packages, SDKs, APIs, CLIs, schemas, protocols or versions.
2. **Serena:** Mandatory before unfamiliar cross-file edits, symbol moves, public API changes, rename/delete or architecture-sensitive source changes. If unavailable, block high-risk structural edits.
3. **Sequential Thinking:** Mandatory before architecture, migration, concurrency, recovery, major refactor or cross-system decisions.
4. **Depwire:** Mandatory before and after structural changes.
5. **Playwright:** Mandatory for browser/UI/E2E acceptance.
6. **Skills-Hub:** On-demand for specialized procedural knowledge, read-only through Bifrost.
7. **Context Fabric:** Optional and capability-gated; not canonical and not a completion blocker.

---

## 6. Session Scope Contract Schema

The generated, ignored, noncanonical session scope contract file was implemented at:
`<project>\.agentcore\runtime\session-scope.json`

Fields:
- `prompt_event_id`
- `identity` (`project_id`, `project_key`, `worktree_id`, `worktree_path`, `session_id`, `session_key`)
- `authority_hashes`
- `projection_revision`
- `intent`
- `decomposition`
- `acceptance`
- `declared_files`
- `observed_files`
- `required_tool_evidence`
- `verifications`
- `final_review`

---

## 7. Stage B Extended Hook Dispatcher

Integrated into `scripts/agentcore_cursor/hooks.py` and `scripts/agentcore_cursor/hook_dispatcher.py`:

- **sessionStart:** Preserved Stage A bootstrap and rule injection.
- **beforeSubmitPrompt:** Preserved Stage A prompt capture.
- **preToolUse:** Gated write/edit tools. Deterministic deny if project not activated, session not open, startup_context incomplete, projection stale/missing, intent/acceptance/declared scope empty, or path outside worktree. Fail-open on internal exceptions.
- **beforeShellExecution:** Deterministic deny for remote shell pipes, unversioned remote installers, force push, destructive Git cleanup/reset, drive format/partition, recursive root deletion, service/scheduled-task mutations, unapproved live DDL, secret printing, and cross-project writes.
- **afterFileEdit / postToolUse:** Records observed file footprints, detects undeclared file edits, appends Micro-step evidence.
- **stop:** Performs 8-axis final review and stores result in `session-scope.json`. Never emits `followup_message` or fabricates operator prompts.

---

## 8. Custom Agent Definitions & Superpowers Adaptation

Three source-controlled custom agent definition files were created under `.cursor/agents/` and mirrored to `C:\Users\ynotf\.cursor\agents\`:

1. `.cursor/agents/code-reviewer.md` — Read-only subagent for changed code review (security, correctness, minimality, wiring, rules). Cannot certify its own code.
2. `.cursor/agents/test-writer.md` — Subagent for writing high-value test suites. Cannot modify production source unless authorized.
3. `.cursor/agents/reflective-optimizer.md` — Proposal-only subagent for Milestone exit and deep reflection. Evaluates verified outcomes; cannot modify foundation, hooks, policy, or architecture.

Superpowers methods were adapted into `docs/agent-policy/SUPERPOWERS_METHOD_ADAPTATION.md` under MIT License attribution without reactivating the Superpowers plugin or adding extra skills.

---

## 9. Comprehensive 26-Test Validation Matrix

All 26 tests executed and PASSED in `scripts/agentcore_cursor/test_stage_b_suite.py`:

| # | Test Case Name | Result | Evidence / Detail |
|---|---|---|---|
| 01 | `100_hook_protocol_iterations` | **PASS** | 100 iterations of hook protocol executed (`rc=0`) |
| 02 | `three_fresh_session_cycles` | **PASS** | 3 full fresh-session cycles completed |
| 03 | `step0_blocks_edits_until_complete` | **PASS** | `preToolUse` denied write when intent was empty |
| 04 | `correct_step0_permits_edits` | **PASS** | `preToolUse` allowed write when Step 0 scope valid |
| 05 | `out_of_scope_file_denied` | **PASS** | `preToolUse` denied write outside assigned worktree |
| 06 | `dangerous_shell_denied` | **PASS** | `beforeShellExecution` denied dangerous shell pipes |
| 07 | `normal_safe_shell_allowed` | **PASS** | `beforeShellExecution` allowed safe command (`git status`) |
| 08 | `hook_crash_fails_open` | **PASS** | PreToolUse exception failed open with warning |
| 09 | `no_hook_lockout` | **PASS** | Verified in protocol test harness |
| 10 | `prompt_captured_exactly_once` | **PASS** | Verified in `agentcore.evidence_events` |
| 11 | `file_footprint_recorded` | **PASS** | `afterFileEdit` recorded observed file path |
| 12 | `undeclared_file_detected` | **PASS** | Modifying undeclared file flagged in `required_tool_evidence` |
| 13 | `projection_stale_blocks_writes` | **PASS** | Missing `GLOBAL_STATE.md` blocked write operations |
| 14 | `task_class_gates_policy` | **PASS** | Encoded in `global-agent-policy.yaml` & `foundation.mdc` |
| 15 | `one_final_review_occurs` | **PASS** | `stop` hook generated 8-axis review in `session-scope.json` |
| 16 | `no_fabricated_operator_prompt` | **PASS** | `stop` hook returned clean `{}` without `followup_message` |
| 17 | `no_stop_hook_loop` | **PASS** | Verified no prompt loop generated |
| 18 | `rollback_restores_stage_a` | **PASS** | `test_rollback_fixture.py` verified Stage A restoration (`rc=0`) |
| 19 | `full_memory_lifecycle_green` | **PASS** | `evidence_events` count = 373 |
| 20 | `projections_remain_current` | **PASS** | Max current revision = 22 |
| 21 | `langgraph_fixture_green` | **PASS** | LangGraph fixture E2E 17/17 tests passed (`rc=0`) |
| 22 | `one_foundation_rule` | **PASS** | Exactly 1 active rule (`agentcore-foundation.mdc`) |
| 23 | `one_lifecycle_skill` | **PASS** | Exactly 1 skill (`agentcore-project-lifecycle`) |
| 24 | `one_mcp_entry` | **PASS** | Exactly 1 MCP entry (`agentcore-gateway`) |
| 25 | `no_third_party_skill_noise` | **PASS** | Shared `.agents\skills` count = 0 |
| 26 | `swarm_untouched` | **PASS** | 0 Swarm MCP entries in Cursor |

---

## 10. Rollback Mechanism & Isolated Fixture Proof

- **Live Backup Created:** `E:\AgentCore-Backups\agentcore-control-plane\cursor-stage-b-20260724-233811`
- **One-Command Rollback Script:** `python scripts/agentcore_cursor/rollback_stage_b.py`
- **Fixture Proof:** Executed `scripts/agentcore_cursor/test_rollback_fixture.py` in isolated disposable fixture `D:\agentcore-fixture\rollback-test`.
- **Restoration Verification:** Proved that running the rollback script restores Stage A `.cursor/hooks.json` containing only `sessionStart` and `beforeSubmitPrompt`, completely removing `preToolUse`, `beforeShellExecution`, `afterFileEdit`, `postToolUse`, and `stop` hooks.

---

## 11. Source Control Execution

All source-controlled implementation files, policy contracts, custom agents, test suites, and audit reports were staged, committed, and pushed per Git policy (`docs/GIT_PUSH_ONLY_POLICY.md`):

- **Target Branch:** `main`
- **Commit Message:** `feat(cursor): implement Stage B integrity harness, session scope contract, and custom agents`
- **Push Target:** `origin main`

---

## 12. Unresolved Cursor Protocol Limitations

1. **Native Stop Hook Loop:** In Cursor's protocol, returning `followup_message` in a `stop` hook causes an automatic prompt resubmission loop. The Stage B `stop` hook avoids this by returning an empty JSON object `{}` after saving the 8-axis final review into `session-scope.json`.
2. **Drive-Relative Workspace Roots:** Cursor occasionally passes drive-relative workspace roots like `d:github\agentcore-control-plane` (missing leading slash). Normalization was added in `hooks.py` (`_normalize_workspace_path`) to prevent phantom tree creation.

---

**Status Signal:**  
`CURSOR_STAGE_B_INTEGRITY_HARNESS_READY`
