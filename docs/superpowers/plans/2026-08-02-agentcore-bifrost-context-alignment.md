# AgentCore Bifrost and Context Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile AgentCore authority and current-state documents to the approved five-owner architecture, establish local official-doc and project-drift controls, and add focused Cursor subagents without enabling experimental runtimes.

**Architecture:** AgentCore remains canonical truth and recovery; Bifrost remains the sole normal MCP gateway; the Context Engine orchestrates rolling context above `agentcore-memory`; neutral SwarmRecall remains a server-side semantic projection; Arabold and Context Fabric provide documentation currency and project drift evidence. OmniRoute, Graphify, Hindsight, and CrewAI remain benchmark-gated future adapters.

**Tech Stack:** Markdown authority contracts, Python validators, PowerShell health/readiness scripts, Bifrost `2.0.0-prerelease1`, AgentCore memory `0.7.0`, Context Fabric `1.0.7`, Arabold Docs MCP, Cursor `.cursor/agents/*.md`.

## Global Constraints

- Approval identifier is `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`.
- Work on `main` is explicitly operator-approved and follows the repository push-only policy.
- Preserve every inherited dirty or untracked file outside the task-owned set.
- Create timestamped rollback copies and SHA-256 evidence before editing protected files.
- Use `AGENTCORE_AUTHORITY_CAPABILITY=authority_maintainer` and the approval identifier for governed validation.
- Do not install, start, configure, or enroll OmniRoute, Graphify, Hindsight, CrewAI, or a new MCP upstream.
- Do not modify Swarm repositories, services, databases, credentials, backups, or runtime roots.
- Do not edit generated `.agentcore/STATE.md`, `.agentcore/DECISIONS.md`, or `.agentcore/CONTEXT_INDEX.md` directly.
- Secrets remain Windows User-scope environment variables and must not appear in source or evidence.

---

### Task 1: Capture before-state and rollback evidence

**Files:**
- Create: `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-02.md`
- Back up outside Git: `E:\AgentCore-Backups\agentcore-control-plane\context-alignment-20260802-232010\`

**Interfaces:**
- Consumes: protected-file list from `contracts/authority-lock.yaml`
- Produces: immutable before hashes, backup paths, Git status, runtime status, and approval record

- [ ] Record the exact Git branch, HEAD, dirty-file inventory, Bifrost health, AgentCore memory health, and Context Fabric health.
- [ ] Copy each task-owned protected file to the timestamped rollback directory without overwriting an existing backup.
- [ ] Record SHA-256 for each source and backup and prove the pairs match.
- [ ] Write the audit preflight section with sanitized evidence and the explicit approval identifier.

### Task 2: Reconcile locked architecture and current state

**Files:**
- Modify: `BLUEPRINT.md`
- Modify: `CONTEXT_BLOCK.md`
- Modify: `DOC_AUTHORITY.md`
- Modify: `MASTER_CONFIG_AND_PROMPT.md`
- Modify: `MILESTONES.md`
- Modify: `AGENTS.md`
- Create: `docs/adr/ADR-2026-08-02-agentcore-bifrost-context-alignment.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-08-02-agentcore-bifrost-context-alignment-design.md`, current acceptance audits, live status probes
- Produces: one consistent architecture and current-state truth for all managed agents

- [ ] Patch `BLUEPRINT.md` to define the responsibility model, transport-plane separation, Context Fabric disposition, future extension gates, and Codex/Cursor execution split.
- [ ] Patch `CONTEXT_BLOCK.md` to record current 2026-08-02/03 live facts, RUN11, Context Engine acceptance, neutral Recall, current drive paths, true residuals, and adopted Context Fabric role.
- [ ] Patch `DOC_AUTHORITY.md` to classify the new ADR/spec/plan and the authoritative acceptance evidence.
- [x] Patch `MASTER_CONFIG_AND_PROMPT.md` so every IDE receives the neutral-memory exception, current Context Engine lifecycle, Arabold/Context Fabric drift rules, and the unchanged single-gateway contract.
- [x] Patch `MILESTONES.md` and `AGENTS.md` so execution ownership is AgentCore authority-maintainer-led and Cursor remains a bounded implementation/review surface without changing Milestone outcomes.
- [x] Add an ADR that records decision, alternatives, consequences, rollback, and benchmark gates.
- [x] Search current authority files for stale H-drive AgentCore ownership, obsolete SwarmRecall prohibition, Cursor-only ownership language, or experimental components presented as live.

### Task 3: Establish local official-document authority

**Files:**
- Modify: `DOC_AUTHORITY.md`
- Update: `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-02.md`

**Interfaces:**
- Consumes: current official Bifrost, Cursor, Context Fabric, Hindsight, OmniRoute, Graphify, and CrewAI sources
- Produces: version-labelled Arabold libraries and retrieval proof

- [ ] Verify current official release/version identifiers from primary sources.
- [ ] Index or refresh Bifrost `2.0.0-prerelease1`, Cursor current subagent docs, Context Fabric `1.0.7`, Hindsight `0.7.0`, OmniRoute `3.8.49`, Graphify `0.9.22`, and CrewAI `1.14.7` in Arabold.
- [ ] Wait for every indexing job to complete or record an exact failed job and cause.
- [ ] Run one targeted retrieval query per library and record result URLs/version evidence.
- [ ] Update the Arabold table in `DOC_AUTHORITY.md` to match the successfully indexed corpus only.

### Task 4: Lock the accepted repository state into Context Fabric

**Files:**
- Modify only Context Fabric local state under: `.context-fabric/`
- Update: `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-02.md`

**Interfaces:**
- Consumes: accepted Git commit created after Tasks 2-3 and active project-router selection
- Produces: committed-state capture, decision projection, drift report, and health proof

- [ ] Prove `.context-fabric` is at the repository root and no invalid non-repo root exists in the approved scan set.
- [x] Run `cf_capture` after the authority commit so the capture is based on committed Git objects.
- [x] Record the approved responsibility-model decision through `cf_log_decision` as a convenience projection.
- [ ] Run `cf_drift` and `cf_query` with drift enabled; classify any remaining drift as inherited dirty work or task error.
- [ ] Run `cf_health`; record that its store is rebuildable and non-canonical.

### Task 5: Add focused Cursor subagents

**Files:**
- Create: `.cursor/agents/authority-drift-reviewer.md`
- Create: `.cursor/agents/bifrost-runtime-diagnostician.md`
- Create: `.cursor/agents/mcp-contract-engineer.md`
- Modify only if schema correction is required: existing `.cursor/agents/*.md`

**Interfaces:**
- Consumes: current official Cursor subagent schema and AgentCore authority chain
- Produces: three focused project-level specialists using `model: inherit`

- [ ] Add a read-only authority/drift reviewer that compares claims to protected docs, current audits, Git, Arabold, and Context Fabric.
- [ ] Add a read-only Bifrost runtime diagnostician that distinguishes gateway health, upstream health, and IDE MCP discovery state without mutating runtime.
- [ ] Add an MCP contract engineer restricted to contracts/renderers/tests and forbidden from live rollout or authority changes without approval.
- [ ] Validate YAML frontmatter fields against current Cursor docs and confirm the files appear under `.cursor/agents/`.
- [ ] Keep the agent count focused; do not duplicate built-in Explore/Bash/Browser or existing code-review/test roles.

### Task 6: Validate, independently review, lock, commit, and push

**Files:**
- Modify: `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-02.md`

**Interfaces:**
- Consumes: all task changes and runtime/index/capture evidence
- Produces: final acceptance, after hashes, rollback instructions, scoped Git commit, and pushed `origin/main`

- [ ] Run `python scripts/validate_authority_lock.py`.
- [ ] Run `python scripts/bifrost/validate_contracts.py` and `python scripts/bifrost/test_contracts.py`.
- [ ] Run `python scripts/validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md`, IDE scope, ecosystem-separation, and rendered-rule checks.
- [ ] Run a scoped secret/junk/generated-artifact scan and confirm no unrelated dirty files enter the task diff.
- [ ] Perform a fresh-context independent review using the read-only Cursor reviewer or equivalent current project reviewer, record `independent_review: PASS`, and resolve all blocking findings.
- [ ] Record after SHA-256 values and exact rollback procedure in the audit.
- [ ] Stage only task-owned architecture/subagent files, create the implementation commit, and capture that committed HEAD in Context Fabric.
- [ ] Append the capture/review evidence to the audit, create the acceptance commit, and push both commits to `origin main`.
- [ ] Capture the final accepted HEAD and rerun drift without rewriting canonical projections directly.
