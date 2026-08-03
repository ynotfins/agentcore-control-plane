---
name: agentcore-project-lifecycle
description: "Governed AgentCore project lifecycle orchestrator for new project bootstrap (Milestone 0) and milestone entry/exit boundaries. Integrates AgentCore memory, governance templates, Arabold docs, and project-scoped continuity without machine-global router mutation."
version: 1.1.0
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

1. **Routing**: Route every MCP integration strictly through Bifrost `agentcore-gateway` (`http://127.0.0.1:8080/mcp`). Execute approved repository-local commands locally with `cwd=<absolute_project_root>`. Project-scoped host adapters must follow their documented identity and path boundary.
   - Memory: `agentcore_memory` (`session_open`, `startup_context`, `append_event`, `retrieve_context`, `expand_source`, `build_handoff`, `session_close`)
   - Docs: `arabold_docs` (`search_docs`, `fetch_url`)
   - Machine-global `agentcore_project_router` tools are operator-maintenance only and are never required or invoked by this skill.
   - Continuity and semantic code tools are invoked only through their approved project-scoped host adapter or repo-local command with the exact repository cwd; never by mutating shared router state.
2. **Templates Source**: `@D:\github\agentcore-control-plane\templates\project-governance\.agentcore`
3. **Hard Boundaries**:
   - Never write `.env` files (use Windows User environment variables only).
   - Never direct-write generated projections (`.agentcore/STATE.md`, `DECISIONS.md`, `CONTEXT_INDEX.md`).
   - Never execute raw SQL against PostgreSQL.
   - Never cross Swarm boundaries (SwarmRecall, SwarmVault, SwarmClaw are excluded).
   - **Context Fabric Boundary**: Context Fabric is an optional, capability-gated component. Its absence or failure must never block bootstrap, milestone entry, or milestone exit. PostgreSQL and AgentCore memory remain canonical; Git provides workspace history fallback. Context Fabric does not write durable ledgers or auto-install git hooks.

============================================================
OPERATION 1: NEW PROJECT BOOTSTRAP (MILESTONE 0)
============================================================

Use when initializing a new project or onboarding an un-governed repository.

### Step 1.1: Exact Project Enrollment
1. Verify repository root and git status (`git status`).
2. Verify that `<project_key>` and `<absolute_project_root>` are an exact pair in `@D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json`.
3. If the pair is absent or mismatched, halt before memory/database writes and request governed enrollment. Do not auto-enroll or select a similarly named repository.

### Step 1.2: Durable Session & Startup Context
1. Open a durable memory session:
   `agentcore_memory-session_open(project_key="<project_key>", project_root="<absolute_project_root>", client_key="<host-client-key>", agent_key="project-lifecycle", session_key="<stable-task-key>")`
2. Retrieve startup context:
   `agentcore_memory-startup_context(project_key="<project_key>", project_root="<absolute_project_root>", session_id="<session_id>")`
3. Before any project-file write, append the redacted bootstrap request through the signed host adapter:
   `agentcore_memory-append_event(project_key="<project_key>", project_root="<absolute_project_root>", session_id="<session_id>", event_kind="prompt", idempotency_key="m0-bootstrap-request-<sha256(project_key|session_key|redacted-request)>", payload={"source":"project-lifecycle","request":"<redacted-operator-request>"})`
   The payload must exclude secrets and volatile timestamps so replay produces the same deterministic key.

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
1. Capture the workspace baseline through the approved project-scoped Context Fabric adapter or repo-local command with `cwd=<absolute_project_root>`. Context Fabric is optional and never changes AgentCore project identity.
2. Query/index project dependencies in Arabold Docs: `arabold_docs-search_docs(query="...")`.

### Step 1.6: Record Bootstrap Evidence
Append the redacted bootstrap completion event through the same signed host adapter using a deterministic key:
`agentcore_memory-append_event(project_key="<project_key>", project_root="<absolute_project_root>", session_id="<session_id>", event_kind="accepted_evidence", idempotency_key="m0-bootstrap-<deterministic-key>", payload={...})`

============================================================
OPERATION 2: MILESTONE BOUNDARY (ENTRY GATE)
============================================================

Use before commencing work on any project Milestone.

1. **Read Authority & State**: Read `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, project `AGENTS.md`, and generated `.agentcore/STATE.md`.
2. **Verify Repository State**: Confirm clean worktree and active branch (`git status`, `git log -1`).
3. **Check Previous Gate**: Confirm previous Milestone is `passed` in `.agentcore/checklists/state.json`.
4. **Retrieve Chronology**: Retrieve recent events via `agentcore_memory-retrieve_context(project_key="<project_key>", project_root="<absolute_project_root>")`.
5. **Expand Evidence**: Expand key artifact/decision references with the same exact `project_key` + `project_root` via `agentcore_memory-expand_source(...)`.
6. **Query Docs**: Resolve exact dependency/framework versions with `arabold_docs`.
7. **Audit Tool Leases**: Inspect `.agentcore/TOOL_MANIFEST.yaml` and verify active tool leases for the Milestone.
8. **Refine Checklists**: Refine Macro and Micro steps for the current Milestone in `.agentcore/checklists/state.json`.
9. **Record Entry Evidence**: Append `state_transition` event to `agentcore_memory`.

============================================================
OPERATION 3: MILESTONE BOUNDARY (EXIT GATE)
============================================================

Use upon completing all Micro steps in a Milestone.

1. **Run Deterministic Tests**: Run test suite, project validators (`validate_contracts.py`), `ReadLints`, and secret scan.
2. **Run Structural Verification**: Run Depwire, Serena symbol checks, and optional Context Fabric drift through approved project-scoped adapters or repo-local commands with `cwd=<absolute_project_root>`; never activate the machine-global router from this skill.
3. **Verify Micro Step Evidence**: Ensure every Micro step in `.agentcore/checklists/state.json` has `status: "passed"` and a valid `evidence_ref` (file path, commit hash, test transcript).
4. **Record Decisions**: Document architectural decisions in `.agentcore/DECISIONS.md`.
5. **Update Projections**: Execute `Invoke-M3ProjectionWorker.ps1` to update `.agentcore/STATE.md`.
6. **Record Completion**: Append a signed, redacted, deterministic `accepted_evidence` completion event before handoff.
7. **Build Handoff**: Construct the handoff via `agentcore_memory-build_handoff(project_key="<project_key>", project_root="<absolute_project_root>", session_id="<session_id>")`.
8. **Close Session**: Close via `agentcore_memory-session_close(project_key="<project_key>", project_root="<absolute_project_root>", session_id="<session_id>")`.
9. **Audit & Release Leases**: Update `.agentcore/TOOL_MANIFEST.yaml` tool lifecycle audit.
10. **Git Commit & Push**: Stage source-controlled files, commit with concise message, and push to remote (`docs/GIT_PUSH_ONLY_POLICY.md`).

============================================================
SELF-HEALING & IDEMPOTENCY
============================================================

- Re-running M0 Bootstrap on an already governed project is idempotent: existing governance files are preserved; missing files are scaffolded.
- If a memory call fails, verify gateway status via `agentcore_memory-memory_status` before retrying.
- Every project-scoped memory call supplies the exact enrolled `project_key` and `project_root`; signed host adapters supply device identity assertions.
- All actions produce verifiable evidence references recorded in `.agentcore/checklists/state.json` and `agentcore_memory`.
