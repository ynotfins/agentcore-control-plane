# AgentCore Phase 5 — Project Lifecycle Skill Acceptance Audit

**Date:** 2026-07-24  
**Task:** AgentCore Project Lifecycle Skill Integration (Phase 5)  
**Status:** PASS / APPROVED  
**Active Cursor Skill:** `C:\Users\ynotf\.cursor\skills\agentcore-project-lifecycle\SKILL.md` (Count: 1)  

---

## 1. Executive Summary

Phase 5 successfully integrated a governed project lifecycle skill (`agentcore-project-lifecycle`) into AgentCore without creating unnecessary custom code, without modifying live machine configurations or database schemas, and while preserving strict isolation boundaries.

The implementation evaluated candidates from the Skills-Hub registry via Bifrost, isolated CLI behavior in a process-local staging fixture, and adopted a **MINIMAL_WRAPPER** design that vendors reviewed candidates (`quickstart` v1.0.0 and `bootstrap` v4.1.0) into `skills/provenance/` while providing a lean AgentCore overlay in `skills/agentcore-project-lifecycle/SKILL.md`.

---

## 2. Phase 5 Entry Gate Verification

All Phase 5 entry checks passed prior to candidate exploration:

| Entry Check | Requirement | Result |
|---|---|---|
| Global Cursor Rules | Exactly 1 (`C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc`) | PASS |
| Project / Parent / Drive Rules | 0 active rules | PASS |
| Cursor Native Skills | 0 active native skills prior to Phase 5 activation | PASS |
| Cursor MCP Config | Exactly 1 entry (`agentcore-gateway`) | PASS |
| Skills-Hub Retrieval | Bifrost `skills_hub` tools active (`search_skills`, `get_skill_detail`, `list_installed_skills`) | PASS |
| Skills-Hub Installed List | Empty (`[]`) | PASS |
| Firebase & Google Sheets | Disabled and zero tools visible | PASS |
| Bifrost Gateway Health | 200 OK (`http://127.0.0.1:8080/health`) | PASS |
| PostgreSQL 18 Service | Running and Automatic (`AgentCore-PostgreSQL18` on `:55433`) | PASS |
| Tool Counts | 10 `agentcore_memory`, 4 `project_router`, 3 `skills_hub`, 0 Swarm, 0 Obsidian | PASS |
| Memory Lifecycle | `session_open` → `startup_context` → `append_event` → `retrieve_context` → `session_close` green | PASS |
| State Projections | Current (`GLOBAL_STATE.md`, `STATE.md`, `DECISIONS.md`, `CONTEXT_INDEX.md`) | PASS |
| LangGraph Fixture | Fingerprint `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` green | PASS |

---

## 3. Skills-Hub Candidate Search & Evaluation

### A. Search Queries Run
Executed independent searches via `skills_hub-search_skills` through Bifrost for:
`quickstart`, `project bootstrap`, `new project bootstrap`, `project lifecycle`, `milestone workflow`, `engineering workflow`, `agentic development`, `software development lifecycle`, `project governance`, `context management`, `implementation plan`, `code review workflow`, `test-driven workflow`.

Total unique candidate slugs discovered: 43.

### B. Top Candidates Audited

1. **`quickstart` (v1.0.0)**:
   - *Description*: Machine-level onboarding agent (Homebrew/apt/Node.js/Python, Claude Code CLI, skills-hub CLI, MCP additions).
   - *Verdict*: Useful for environment preflight verification, but unsuitable as an AgentCore project lifecycle skill because it assumes broad machine installation authority (`npm -g`, `brew`, `apt`), modifies Claude MCP configs, and lacks AgentCore memory, router, or milestone awareness.

2. **`bootstrap` (v4.1.0)**:
   - *Description*: Project bootstrapper from templates with foundation validation requirements (service layer, string constants, component library, privacy model, scalability, env loading).
   - *Verdict*: Excellent architectural rules (foundation checks prevent rework cascades), but assumes hardcoded paths (`~/git2/claude-config/templates/`) and Claude-specific memory (`~/.claude/projects/.../memory/MEMORY.md`).

3. **`env-setup` (v2.0.0)**:
   - *Description*: Environment setup (creates `.env`, runs Docker, DB migrations).
   - *Verdict*: Rejected for direct use because it creates `.env` files (violating AgentCore secret policy).

### C. Decision: MINIMAL_WRAPPER
- **Rationale**: No single upstream skill satisfies AgentCore's strict requirements (Bifrost-only routing, `agentcore-memory` session open/close, `agentcore-project-router`, state projections, milestone entry/exit gates).
- **Strategy**: Reused architectural foundation checks from `bootstrap` v4.1.0 and environment preflight patterns from `quickstart` v1.0.0. Vendored both as reviewed provenance files (`skills/provenance/quickstart-1.0.0.md` and `skills/provenance/bootstrap-4.1.0.md`). Constructed a minimal AgentCore overlay at `skills/agentcore-project-lifecycle/SKILL.md`.

---

## 4. Isolated CLI Staging Verification

Testing was performed using the pinned CLI (`H:\AgentRuntime\skills-hub\node_modules\@skills-hub-ai\cli\dist\index.js`) in process-isolated staging roots:
- `H:\AgentRuntime\skills-hub\staging\phase5-project-lifecycle\quickstart\`
- `H:\AgentRuntime\skills-hub\staging\phase5-project-lifecycle\bootstrap\`

Environment variables set per-process:
- `HOME=H:\AgentRuntime\skills-hub\staging\phase5-project-lifecycle\<candidate>\home`
- `USERPROFILE=H:\AgentRuntime\skills-hub\staging\phase5-project-lifecycle\<candidate>\home`
- `HOMEDRIVE=H:`
- `HOMEPATH=\AgentRuntime\skills-hub\staging\phase5-project-lifecycle\<candidate>\home`

**Install Results**:
- `quickstart` v1.0.0 installed to `quickstart\home\.cursor\skills\quickstart\SKILL.md` (12,320 bytes).
- `bootstrap` v4.1.0 installed to `bootstrap\home\.cursor\skills\bootstrap\SKILL.md` (8,611 bytes).
- **Safety check**: 0 files escaped to `C:\Users\ynotf\.cursor`, `C:\Users\ynotf\.claude`, `C:\Users\ynotf\.codex`, `C:\Users\ynotf\.agents`, or `D:\github\agentcore-control-plane\.cursor`.

---

## 5. Implementation & Hash Parity

Canonical source files:
- `D:\github\agentcore-control-plane\skills\provenance\quickstart-1.0.0.md`
- `D:\github\agentcore-control-plane\skills\provenance\bootstrap-4.1.0.md`
- `D:\github\agentcore-control-plane\skills\agentcore-project-lifecycle\SKILL.md`

Live rendered active skill:
- `C:\Users\ynotf\.cursor\skills\agentcore-project-lifecycle\SKILL.md`

**Hash Verification**:
- Source SHA-256: `7C97B389A4123AA0A3E4301BD9CE05F52110C58A210EA324C06074B7F4209B68`
- Live SHA-256:   `7C97B389A4123AA0A3E4301BD9CE05F52110C58A210EA324C06074B7F4209B68`
- Byte-Identical: **YES**
- Active Operator Cursor Skill Count: **1**
- Context Fabric Boundary: Refined in Phase 5B to explicitly state that Context Fabric is optional, capability-gated, and noncanonical (PostgreSQL & AgentCore memory remain canonical authority).

---

## 6. Fixture Testing & Required Lifecycle Behavior

Verified on disposable registered project fixture `D:\github\phase5-disposable-fixture`:

1. **Operation 1: New Project Bootstrap (M0)**:
   - Activated via `agentcore_project_router-project_activate`.
   - Durable session opened via `agentcore_memory-session_open`.
   - `agentcore_memory-startup_context` called.
   - Scaffolded governance files from `templates/project-governance/.agentcore/`.
   - Verified foundation requirements (service layer, Privacy model, config strategy).
   - Captured Context Fabric snapshot via `context_fabric-cf_capture`.
   - Appended `accepted_evidence` event to memory ledger.

2. **Operation 2: Milestone Entry Gate**:
   - Authority and generated state verified.
   - Worktree and git commit verified.
   - Context retrieved via `agentcore_memory-retrieve_context`.
   - Tool manifest and leases audited.
   - Recorded `state_transition` entry event.

3. **Operation 3: Milestone Exit Gate**:
   - Verified Micro step execution and evidence references.
   - Built handoff via `agentcore_memory-build_handoff`.
   - Closed session via `agentcore_memory-session_close`.
   - Resumed session safely via `agentcore_memory-session_open` with existing key.

---

## 7. Regression Gate Verification

Final post-implementation regression checks:

| Check | Expected | Observed | Status |
|---|---|---|---|
| Active Global Rules | Exactly 1 (`agentcore-foundation.mdc`) | 1 (`agentcore-foundation.mdc`) | PASS |
| Active Cursor Skills | Exactly 1 (`agentcore-project-lifecycle\SKILL.md`) | 1 (`agentcore-project-lifecycle\SKILL.md`) | PASS |
| Third-Party Discovery | OFF | OFF | PASS |
| Cursor MCP Config | Exactly 1 entry (`agentcore-gateway`) | 1 entry (`agentcore-gateway`) | PASS |
| Bifrost Gateway Health | 200 OK | 200 OK | PASS |
| Memory Tools | Exactly 10 | 10 | PASS |
| Router Tools | Exactly 4 | 4 | PASS |
| Skills-Hub Tools | Exactly 3 (read-only) | 3 (`get_skill_detail`, `list_installed_skills`, `search_skills`) | PASS |
| Write/Install Tools Exposed | 0 | 0 | PASS |
| Firebase & Sheets | Disabled / 0 tools | 0 tools | PASS |
| Installed Skill List | Empty (`[]`) | `[]` | PASS |
| Memory Lifecycle | Green | `session_open` → `append` → `close` PASS | PASS |
| State Projections | Current | Updated deterministically via `Invoke-M3ProjectionWorker.ps1` | PASS |
| LangGraph Fixture | Fingerprint `a86e40e8ddd0...` | Fingerprint `a86e40e8ddd0...` (15 nodes) | PASS |

---

## 8. Rollback Plan

If rollback is required:
1. Delete `C:\Users\ynotf\.cursor\skills\agentcore-project-lifecycle\SKILL.md`.
2. Delete `skills/agentcore-project-lifecycle/` and `skills/provenance/`.
3. `git checkout main -- .` to restore source repository state.
4. Verify `C:\Users\ynotf\.cursor\skills` returns to 0 active skills.
