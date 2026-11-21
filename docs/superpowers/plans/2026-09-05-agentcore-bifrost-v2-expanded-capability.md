# AgentCore Bifrost v2 Expanded Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align AgentCore authority, Bifrost v2.0.0, skills, MCP admission, IDE/runtime enrollment, and Process Lasso around broad safe capability with low context overhead.

**Architecture:** One `agentcore-gateway` is the AgentCore MCP front door. Bifrost exposes small tools directly and heavy tools through Code Mode, with named per-tool allowlists and JIT/operator gates for risky operations. Host-native skills or generated adapters teach when to use the capabilities without creating a second router.

**Tech Stack:** Bifrost v2.0.0, MCP Streamable HTTP, PowerShell 7, Python 3 repository venv, JSON/YAML contracts, Agent Skills, Windows Process Lasso.

**Spec:** `docs/superpowers/specs/2026-09-05-agentcore-bifrost-v2-expanded-capability-design.md`

## Global Constraints

- Approval: `AUTH-2026-09-05-UNIVERSAL-IDE-BIFROST-SKILLS-ALIGNMENT`.
- No writes to `D:\github\nfa-platform` or its alerts database/runtime/configuration.
- No writes to SwarmClaw, SwarmRecall, SwarmVault, or the Swarm control plane.
- No secret values in output, Git, prompts, or evidence.
- No public Bifrost bind, public tunnel, whole-drive filesystem MCP, or direct IDE database credential.
- Stage and commit only task-owned files; verify with `git diff --cached --name-only`.

---

### Task 1: Lock Bifrost v2 Documentation and Correct Authority

**Files:**
- Create: `docs-lock.json`
- Modify: `PROJECT_ANCHOR.md`
- Modify: `BLUEPRINT.md`
- Modify: `DOC_AUTHORITY.md`
- Modify: `CONTEXT_BLOCK.md`

**Interfaces:**
- Consumes: live `/api/version`, Arabold `bifrost@2.0.0`, operator approval.
- Produces: exact version lock and OpenClaw/Swarm ownership boundary.

- [ ] Verify `find_version(bifrost, 2.0.0)` plus searches for Code Mode, Skills Repository, and MCP filtering return current results. Record refresh failure honestly when the upstream docs expose a missing root; do not downgrade an otherwise queryable exact corpus.
- [ ] Write `docs-lock.json` with Bifrost `2.0.0`, source `https://docs.getbifrost.ai`, refresh evidence, and installed binary hash.
- [ ] Create timestamped rollback copies and before hashes for protected files.
- [ ] Set `AGENTCORE_AUTHORITY_CAPABILITY=authority_maintainer` and `AGENTCORE_AUTHORITY_APPROVAL_ID=AUTH-2026-09-05-UNIVERSAL-IDE-BIFROST-SKILLS-ALIGNMENT` only for governed edits.
- [ ] Reconcile Bifrost `2.0.0` and exact-version docs statements.
- [ ] Reclassify OpenClaw as AgentCore-owned while leaving SwarmClaw, SwarmRecall, and SwarmVault outside AgentCore execution authority.
- [ ] Run `scripts\.venv\Scripts\python.exe scripts\validate_authority_lock.py` and `scripts\.venv\Scripts\python.exe scripts\bifrost\validate_contracts.py`.
- [ ] Obtain `authority-drift-reviewer` acceptance, record hashes/evidence, and restore file locks.

### Task 2: Align Master Enrollment, Tool Rules, and Host Contracts

**Files:**
- Modify: `MASTER_CONFIG_AND_PROMPT.md`
- Modify: `docs/prompts/install-agentcore-gateway-in-ide.md`
- Modify: `contracts/global-agent-policy.yaml`
- Modify: `contracts/agentcore-gateway-client.json`
- Modify: `contracts/agentcore-alignment-skill-hosts.json`
- Modify: `ide-profiles/IDE_CAPABILITY_MATRIX.yaml`
- Modify: `scripts/render_ide_rules.py`
- Modify: `scripts/bifrost/validate_contracts.py`
- Modify: `scripts/validate_agentcore_alignment_skill.py`
- Modify only where evidence requires it: `ide-profiles/devin/*`, `ide-profiles/reasonix/*`, `renderers/gateway-clients/devin.json`

**Interfaces:**
- Consumes: Task 1 authority and the host certification taxonomy.
- Produces: one executable self-enrollment contract for every named host.

- [ ] Add failing validator cases for missing named hosts, stale direct-MCP instructions, missing Code Mode discovery, missing installed-skill hashes, nonexistent evidence files, and OpenClaw misclassification.
- [ ] Run the focused tests and confirm each fails for the intended missing behavior.
- [ ] Update the master and standalone setup prompts with the complete host set, skill delivery, session/milestone tool discovery, and exact when-to-use rules.
- [ ] Preserve host/plugin-owned integrations while forbidding duplicate AgentCore upstreams.
- [ ] Correct Devin's direct-server/public-tunnel template and reset unsupported Reasonix/Hindsight claims to evidence-backed states.
- [ ] Regenerate global rules and run the focused tests to green.
- [ ] Run `scripts\.venv\Scripts\python.exe scripts\bifrost\test_contracts.py`, `scripts\.venv\Scripts\python.exe scripts\render_ide_rules.py --check`, `scripts\.venv\Scripts\python.exe scripts\bifrost\validate_ide_enrollment_scope.py`, and both Cursor prompt validators.
- [ ] Obtain independent authority and code review.

### Task 3: Govern and Publish the AgentCore Skill Set

**Files:**
- Create: `contracts/bifrost-skills-publication.json`
- Create: `contracts/schemas/bifrost-skills-publication.schema.json`
- Modify: `ops/bifrost/Sync-AgentCoreBifrostSkillsRepository.ps1`
- Create: `.agents/skills/agentcore-tool-discovery/`
- Create: `.agents/skills/morph-source-workflows/`
- Create: `.agents/skills/zoo-roo-code-workflows/`
- Test: `scripts/bifrost/test_bifrost_skills_sync.py`

**Interfaces:**
- Consumes: registry tool policy and Task 2 host delivery contract.
- Produces: versioned, hash-locked skills and host adapters.

- [ ] For each skill, run a baseline agent scenario without the skill and record the specific routing failure.
- [ ] Add one skill at a time with valid frontmatter, concise instructions, references only where needed, and no routing-engine behavior.
- [ ] Run the same scenario with the skill and verify correct tool selection and stop behavior.
- [ ] Add failing sync tests for unapproved skills, hash/version/license mismatch, malformed routing references, and secret-like content.
- [ ] Move the publication allowlist from PowerShell into the schema-validated contract and run tests to green.
- [ ] Publish approved versions with `Sync-AgentCoreBifrostSkillsRepository.ps1 -Apply` and verify the Skills API and Codex marketplace records without printing credentials.
- [ ] Install only through native supported host mechanisms; use generated rules/adapters for other hosts.

### Task 4: Admit and Classify Primary MCP Servers

**Files:**
- Modify: `contracts/bifrost-upstream-mcp-registry.json`
- Modify: `contracts/schemas/bifrost-upstream-mcp-registry.schema.json`
- Modify: `scripts/bifrost/render_bifrost_config.py`
- Modify: `scripts/bifrost/test_contracts.py`
- Modify: `docs/bifrost/BIFROST_CODE_MODE_RUNBOOK.md`

**Interfaces:**
- Consumes: exact package/repository, version, license, tool inventory, auth, and storage evidence.
- Produces: active, dormant, JIT, rejected, or `catalogued_unverified` decision for every primary server.

- [ ] Verify existing Serena, Sequential Thinking, Tentra, Depwire, Filesystem, GitHub, and Playwright entries and replace broad grants with named per-tool policies.
- [ ] Resolve Shadcn, PostHog, Fetch, wcgw, Docker, PostgreSQL, SQLite, Ref, and AgentMail to exact official artifacts; reject ambiguous or commercially unsuitable candidates.
- [ ] Add failing contract tests for unpinned artifacts, missing licenses, wildcard grants, missing dangerous-tool classifications, database write defaults, and absent Code Mode decisions.
- [ ] Admit candidates as disabled/catalogued until health and tool inventory pass; activate only safe profiles.
- [ ] Keep normal IDE database tools behind a governed read-only facade; all writes remain in the owning migration workflow. Do not connect to the NFA alerts database during this rollout.
- [ ] Render to a temporary file, diff, then apply through the Bifrost installer with rollback evidence.
- [ ] Run authenticated initialize, `tools/list`, Code Mode stub reads, and one safe read-only canary per active server.

### Task 5: Roll Out Host Profiles Without False Parity Claims

**Files:**
- Create or modify only evidence-backed directories under `ide-profiles/` and `renderers/gateway-clients/`.
- Modify: `ops/Test-AgentCoreLiveClientAdoption.ps1`

**Interfaces:**
- Consumes: Tasks 2-4 contracts and skills.
- Produces: objective certification state per named host.

- [ ] Add validator coverage for every named host and each certification state.
- [ ] Enroll one host at a time with backup, syntax validation, restart/fresh task, gateway discovery, Code Mode discovery, and memory lifecycle proof.
- [ ] Install Zoo/Roo only in verified VS Code extension hosts. Record `unsupported_with_reason` elsewhere and supply the workflow skill/rules instead.
- [ ] Repair the designated AgentCore OpenHands runtime and its live state; do not start or modify the stale NFA-specific container.
- [ ] Prove OpenHands can reach Bifrost without a public bind, and prove an unrelated container/external interface cannot.
- [ ] Enroll OpenClaw through its canonical AgentCore live root after source/live authority is resolved and backed up.
- [ ] Run `ops\Test-AgentCoreLiveClientAdoption.ps1` and host-native safe canaries.

### Task 6: Repair Process Lasso Safely

**Files:**
- Modify outside Git after backup: `C:\ProgramData\ProcessLasso\config\prolasso.ini`
- Modify outside Git after backup: `C:\ProgramData\ProcessLasso\config\AgentCore-IDE-Performance\prolasso.ini`
- Modify outside Git after backup: `C:\ProgramData\ProcessLasso\config\AgentCore-IDE-Performance\Apply-AgentCoreProcessLassoProfile.ps1`

**Interfaces:**
- Consumes: observed process paths and current active Process Lasso configuration.
- Produces: persistent low-interference scheduling without cache thrash.

- [ ] Export/hash the active and staged configs and verify target paths remain under `C:\ProgramData\ProcessLasso\config`.
- [ ] Disable SmartTrim working-set trims and standby-list purges while preserving ProBalance and unrelated GPU/UI rules.
- [ ] Add exact observed priority-app rules including Zcode and Open Interpreter; use path/command-line rules for OpenHands and never generic Docker/WSL/node/python names.
- [ ] Replace whole-file copying with a validated merge of owned keys so future applies preserve live unrelated settings.
- [ ] Restart/reload Process Governor only if required, verify priorities and persistence, and inspect logs for new trim/purge events.
- [ ] Record a 24-hour observation checkpoint. Roll back for commit charge above 85%, increased hard faults/stalls, or priority-app regression.

### Task 7: Adopt High-Value Bifrost v2 Features Through Canaries

**Files:**
- Modify only after canary design acceptance: Bifrost contracts, renderer, tests, and feature-adoption report.

**Interfaces:**
- Consumes: stable MCP/host rollout and non-NFA canary client.
- Produces: adopted/deferred/rejected feature matrix with evidence.

- [ ] Verify semantic-cache correctness and invalidation across configuration changes.
- [ ] Add bounded observability and retention checks without prompt-content leakage.
- [ ] Move governed reusable prompts into the Prompt Repository.
- [ ] Configure retries/fallbacks, budgets, model limits, and required headers in a non-NFA profile.
- [ ] Run explicit requests or at most 5% eligible traffic for 24 hours; require correct routing, zero auth errors, budget compliance, no leakage, and no p95 latency regression above 20%.
- [ ] Only after that gate, evaluate complexity routing, routing rules, async inference, and signed webhooks.
- [ ] Do not reroute global IDE inference or NFA traffic during the canary.

### Task 8: Final Acceptance and Git Integration

**Files:**
- Create: bounded audit evidence under `audits/`.

**Interfaces:**
- Consumes: all completed task evidence.
- Produces: final pass/partial/fail report and rollback map.

- [ ] Run authority, contract, schema, renderer, ecosystem-separation, host-adoption, secret/junk, gateway/watchdog, skill, and Process Lasso checks.
- [ ] Obtain `authority-drift-reviewer` and `code-reviewer` final verdicts.
- [ ] Confirm `git diff --cached --name-only` contains only task-owned files and no NFA or Swarm paths.
- [ ] Commit and push the active branch according to `docs/GIT_PUSH_ONLY_POLICY.md`.
- [ ] Report each host and feature as passed, partial, deferred, rejected, or unsupported with exact evidence and remaining risk.
