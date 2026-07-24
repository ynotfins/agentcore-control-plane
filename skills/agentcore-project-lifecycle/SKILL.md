---
name: agentcore-project-lifecycle
description: "Governed AgentCore project lifecycle orchestrator for new project bootstrap (Milestone 0) and milestone entry/exit boundaries. Integrates AgentCore memory, router, governance templates, Arabold docs, and Context Fabric through Bifrost."
version: 1.0.0
category: meta
provenance:
  decision: MINIMAL_WRAPPER
  reused_candidates:
    - slug: "bootstrap"
      version: "4.1.0"
      reused_aspects: "Foundation validation rules (service layer, privacy model, config strategy), template-driven project initialization, pipeline recommendations"
    - slug: "quickstart"
      version: "1.0.0"
      reused_aspects: "Environment preflight verification and project type detection"
---

# AgentCore Project Lifecycle Skill

Orchestrates governed project initialization (Milestone 0 Bootstrap) and Milestone entry/exit boundaries for all AgentCore-managed projects.

============================================================
AUTHORITY & PRECONDITIONS
============================================================

1. **Routing**: Route all tools strictly through Bifrost `agentcore-gateway` (`http://127.0.0.1:8080/mcp`).
   - Router: `agentcore_project_router` (`project_activate`, `project_status`, `project_list`)
   - Memory: `agentcore_memory` (`session_open`, `startup_context`, `append_event`, `retrieve_context`, `expand_source`, `build_handoff`, `session_close`)
   - Docs: `arabold_docs` (`search_docs`, `fetch_url`)
   - Continuity: `context_fabric` (`cf_capture`, `cf_drift`, `cf_health`)
2. **Templates Source**: `@D:\github\agentcore-control-plane\templates\project-governance\.agentcore`
3. **Hard Boundaries**:
   - Never write `.env` files (use Windows User environment variables only).
   - Never direct-write generated projections (`.agentcore/STATE.md`, `DECISIONS.md`, `CONTEXT_INDEX.md`).
   - Never execute raw SQL against PostgreSQL.
   - Never cross Swarm boundaries (SwarmRecall, SwarmVault, SwarmClaw are excluded).

============================================================
OPERATION 1: NEW PROJECT BOOTSTRAP (MILESTONE 0)
============================================================

Use when initializing a new project or onboarding an un-governed repository.

### Step 1.1: Worktree & Router Activation
1. Verify repository root and git status (`git status`).
2. Activate the project in `agentcore_project_router`:
   `agentcore_project_router-project_activate(path="<absolute_project_root>")`

### Step 1.2: Durable Session & Startup Context
1. Open a durable memory session:
   `agentcore_memory-session_open(project_key="<project_key>", client_key="cursor", agent_key="project-lifecycle")`
2. Retrieve startup context:
   `agentcore_memory-startup_context(project_key="<project_key>")`

### Step 1.3: Governance Files Scaffolding
Create missing `.agentcore/` files from `@D:\github\agentcore-control-plane\templates\project-governance\.agentcore`:
- `.agentcore/PROJECT_CHARTER.md` (record the original operator prompt verbatim)
- `.agentcore/MILESTONES.md` and `.agentcore/milestones/M0-bootstrap.md`
- `.agentcore/checklists/state.json` (canonical execution checklist)
- `.agentcore/TOOL_MANIFEST.yaml` (initial tool disclosure manifest)
- `.agentcore/PROJECT_STATE.json`
- `.agentcore/RISK_REGISTER.md`
- `.agentcore/ACCEPTANCE_TESTS.md`
- Root `AGENTS.md` and `CLAUDE.md` if missing.

### Step 1.4: Foundation Requirements Validation
Verify the codebase against critical architectural foundations (adapted from `bootstrap` v4.1.0):
1. **Service Layer**: Domain-split service modules exist (no monolithic single file).
2. **String Constants / L10N**: User-facing brand terms and strings are centralized.
3. **Component Library**: Reusable UI widgets with accessibility and design tokens.
4. **Privacy-Aware Data Model**: Public vs private data models separated.
5. **Config & Env Loading Strategy**: Centralized config module reading Windows User env vars; `.env.example` provided for documentation; **NO `.env` files**.

Flag any missing items as `TODO` in `PROJECT_CHARTER.md` and `state.json`.

### Step 1.5: Continuity & Documentation Registration
1. Capture workspace baseline in Context Fabric: `context_fabric-cf_capture()`.
2. Query/index project dependencies in Arabold Docs: `arabold_docs-search_docs(query="...")`.

### Step 1.6: Record Bootstrap Evidence
Append bootstrap completion event:
`agentcore_memory-append_event(session_id="<session_id>", event_kind="accepted_evidence", idempotency_key="m0-bootstrap-<timestamp>", payload={...})`

============================================================
OPERATION 2: MILESTONE BOUNDARY (ENTRY GATE)
============================================================

Use before commencing work on any project Milestone.

1. **Read Authority & State**: Read `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, project `AGENTS.md`, and generated `.agentcore/STATE.md`.
2. **Verify Repository State**: Confirm clean worktree and active branch (`git status`, `git log -1`).
3. **Check Previous Gate**: Confirm previous Milestone is `passed` in `.agentcore/checklists/state.json`.
4. **Retrieve Chronology**: Retrieve recent events via `agentcore_memory-retrieve_context(project_key="<project_key>")`.
5. **Expand Evidence**: Expand key artifact/decision references via `agentcore_memory-expand_source(...)`.
6. **Query Docs**: Resolve exact dependency/framework versions with `arabold_docs`.
7. **Audit Tool Leases**: Inspect `.agentcore/TOOL_MANIFEST.yaml` and verify active tool leases for the Milestone.
8. **Refine Checklists**: Refine Macro and Micro steps for the current Milestone in `.agentcore/checklists/state.json`.
9. **Record Entry Evidence**: Append `state_transition` event to `agentcore_memory`.

============================================================
OPERATION 3: MILESTONE BOUNDARY (EXIT GATE)
============================================================

Use upon completing all Micro steps in a Milestone.

1. **Run Deterministic Tests**: Run test suite, project validators (`validate_contracts.py`), `ReadLints`, and secret scan.
2. **Run Structural Verification**: Run Depwire (`depwire-verify_change`), Serena symbol checks, and Context Fabric drift check (`context_fabric-cf_drift`).
3. **Verify Micro Step Evidence**: Ensure every Micro step in `.agentcore/checklists/state.json` has `status: "passed"` and a valid `evidence_ref` (file path, commit hash, test transcript).
4. **Record Decisions**: Document architectural decisions in `.agentcore/DECISIONS.md`.
5. **Update Projections**: Execute `Invoke-M3ProjectionWorker.ps1` to update `.agentcore/STATE.md`.
6. **Build Handoff**: Construct project handoff packet via `agentcore_memory-build_handoff(project_key="<project_key>")`.
7. **Close Session**: Close memory session: `agentcore_memory-session_close(session_id="<session_id>")`.
8. **Audit & Release Leases**: Update `.agentcore/TOOL_MANIFEST.yaml` tool lifecycle audit.
9. **Git Commit & Push**: Stage source-controlled files, commit with concise message, and push to remote (`docs/GIT_PUSH_ONLY_POLICY.md`).

============================================================
SELF-HEALING & IDEMPOTENCY
============================================================

- Re-running M0 Bootstrap on an already governed project is idempotent: existing governance files are preserved; missing files are scaffolded.
- If a memory call fails, verify gateway status via `agentcore_memory-memory_status` before retrying.
- All actions produce verifiable evidence references recorded in `.agentcore/checklists/state.json` and `agentcore_memory`.
