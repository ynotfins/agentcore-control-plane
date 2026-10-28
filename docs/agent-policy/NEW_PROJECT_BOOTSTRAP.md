# New Project Bootstrap Standard (Milestone 0)

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-execution-policy.json`.
**Applies to:** every new managed non-Swarm project. Do not begin broad implementation before M0 passes.

## Purpose

Every managed project starts from one governed Bootstrap Milestone (M0) that establishes identity, context, governance files, and a safe initial tool surface — never from unrestricted administrative or destructive authority.

## M0 sequence

1. **Enroll identity once** by adding the exact approved repository/worktree root to
   `contracts/agentcore-project-enrollment.json` through the authority-maintainer path.
   The contract is default-deny; directory discovery and name-based exclusions are not enrollment.
2. **Resolve identity** from the host's exact enrolled repository/worktree root and pass that
   explicit identity to `agentcore-memory`; ordinary IDE profiles do not mutate machine-global
   project-router state.
3. **Load global context** through `agentcore-memory` (startup context; degraded-mode tolerated until the memory platform lands).
4. **Read in order** (see `DOCUMENTATION_READ_ORDER.md`): global `PROJECT_ANCHOR.md` + `DOC_AUTHORITY.md`, global agent policy (`docs/agent-policy/`), project `AGENTS.md`/`CLAUDE.md`, existing project docs.
5. **Preserve the operator's original project prompt** verbatim in `PROJECT_CHARTER.md` (or reference it through an immutable evidence identifier once the memory platform provides one).
6. **Inspect** manifests, lockfiles, repository state, and Git history.
7. **Run Context Fabric locally** through the repository hook/CLI for capture and drift/reality checks.
8. **Discover architecture** with native IDE semantic/source tools; use an explicit project-owned Serena process only when needed, and run Depwire/Tentra diagnostics with an explicit cwd.
9. **Inventory and ingest direct external dependencies** from active runtime, development, and build manifests, plus directly used external SDKs/APIs/CLIs. Exclude transitive and project-local packages. Resolve exact installed or locked versions first; a version range is not an exact pin. Use latest stable only when no exact project version exists and record the resolved version. For every `library@version`, verify the shared `F:\AgentCore\runtime\docs-store\CATALOG.json` entry, Arabold `find_version`, and real `search_docs` hits. On missing or invalid coverage, scrape the official source for that version, wait for `get_job_info` to finish, write/update the catalog and `F:\AgentCore\runtime\docs-store\official\{library}\{version}\` snapshot, then search locally. Record when the publisher has no versioned docs; do not claim exact-version coverage from unverified latest docs. Context7 through the gateway may bridge a public-doc question while scraping but is not completion evidence.
10. **Create from templates** (`templates/project-governance/.agentcore/`):
   - `PROJECT_CHARTER.md`
   - `MILESTONES.md` + `milestones/M0-bootstrap.md`
   - initial Macro/Micro checklists (`checklists/state.json` + generated Markdown)
   - `TOOL_MANIFEST.yaml`
   - `PROJECT_STATE.json`
   - `RISK_REGISTER.md`
   - `ACCEPTANCE_TESTS.md`
11. **Select tools**: record `core_active` and Milestone-0/Milestone-1 tools in `TOOL_MANIFEST.yaml` per `TOOL_LIFECYCLE_POLICY.md`.
12. **Establish a restore point** (clean commit or tagged state).
13. **Complete M0 acceptance checks** (all governance files exist and validate; original prompt preserved; Context Fabric checkpoint recorded; Arabold checkpoint means verified shared coverage for every direct external dependency, or an explicit blocker for missing/failed coverage; the project records only a lightweight docs checkpoint with library, exact resolved version, official URL, shared-catalog status, and last verification, never scraped third-party docs).
14. **Perform the first tool audit** and record it in `TOOL_MANIFEST.yaml`.
15. **Disable Bootstrap-only tools** not needed for Milestone 1 (recorded as `dormant` in the manifest; runtime enforcement arrives with memory-platform M6).

## Bootstrap tool profile

The Bootstrap profile provides discovery and bounded project setup only:

- `agentcore-memory` (context retrieval/health)
- `arabold-docs` (exact-version documentation)
- repository-local Context Fabric (capture/drift/health)
- native IDE semantic/source tools; optional project-owned Serena
- explicit-cwd Depwire (read/impact/verify)
- explicit-project Tentra local (read/index)
- `sequential-thinking`
- Native IDE filesystem operations bounded to the assigned worktree

The four `agentcore-project-router` controls are operator-only maintenance and
must not be treated as a concurrent-session boundary. Serena, Depwire, Tentra,
filesystem, and Context Fabric stay dormant in shared Bifrost profiles while
their calls lack trustworthy explicit per-session project identity.

It must **not** automatically include: Bifrost administration, raw PostgreSQL, whole-drive filesystem access, destructive GitHub operations, unrestricted browser code execution, process attachment, hosted Tentra upload, direct secret access, live IDE configuration writes, or Swarm tools.

## Idempotency and safety

- Bootstrapping an already-governed project must be idempotent: existing governance files are preserved, missing ones are created from templates.
- The target must exactly match a path in `contracts/agentcore-project-enrollment.json`.
  Missing enrollment returns `project_not_enrolled`; Swarm ownership returns
  `swarm_project_refused`. Never broaden this into a whole-root discovery rule.
- No secrets are read, written, or recorded during bootstrap.
- Existing project rules (`AGENTS.md`, `.cursor/rules/`, etc.) are preserved, not overwritten.
