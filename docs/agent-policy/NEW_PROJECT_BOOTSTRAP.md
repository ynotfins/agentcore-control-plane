# New Project Bootstrap Standard (Milestone 0)

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-execution-policy.json`.
**Applies to:** every new managed non-Swarm project. Do not begin broad implementation before M0 passes.

## Purpose

Every managed project starts from one governed Bootstrap Milestone (M0) that establishes identity, context, governance files, and a safe initial tool surface — never from unrestricted administrative or destructive authority.

## M0 sequence

1. **Activate/register** the repository and worktree through `agentcore-project-router` (`project_activate`).
2. **Load global context** through `agentcore-memory` (startup context; degraded-mode tolerated until the memory platform lands).
3. **Read in order** (see `DOCUMENTATION_READ_ORDER.md`): global `PROJECT_ANCHOR.md` + `DOC_AUTHORITY.md`, global agent policy (`docs/agent-policy/`), project `AGENTS.md`/`CLAUDE.md`, existing project docs.
4. **Preserve the operator's original project prompt** verbatim in `PROJECT_CHARTER.md` (or reference it through an immutable evidence identifier once the memory platform provides one).
5. **Inspect** manifests, lockfiles, repository state, and Git history.
6. **Run Context Fabric** capture and drift/reality check for the project workspace.
7. **Discover architecture** with Serena (symbols/structure), Depwire (dependency graph/impact), and Tentra local (architecture graph).
8. **Resolve exact dependency versions** and index/query documentation through Arabold Docs.
9. **Create from templates** (`templates/project-governance/.agentcore/`):
   - `PROJECT_CHARTER.md`
   - `MILESTONES.md` + `milestones/M0-bootstrap.md`
   - initial Macro/Micro checklists (`checklists/state.json` + generated Markdown)
   - `TOOL_MANIFEST.yaml`
   - `PROJECT_STATE.json`
   - `RISK_REGISTER.md`
   - `ACCEPTANCE_TESTS.md`
10. **Select tools**: record `core_active` and Milestone-0/Milestone-1 tools in `TOOL_MANIFEST.yaml` per `TOOL_LIFECYCLE_POLICY.md`.
11. **Establish a restore point** (clean commit or tagged state).
12. **Complete M0 acceptance checks** (all governance files exist and validate; original prompt preserved; Context Fabric + Arabold checkpoints recorded).
13. **Perform the first tool audit** and record it in `TOOL_MANIFEST.yaml`.
14. **Disable Bootstrap-only tools** not needed for Milestone 1 (recorded as `dormant` in the manifest; runtime enforcement arrives with memory-platform M6).

## Bootstrap tool profile

The Bootstrap profile provides discovery and bounded project setup only:

- `agentcore-project-router` (activate/status)
- `agentcore-memory` (context retrieval/health)
- `arabold-docs` (exact-version documentation)
- `context-fabric` (capture/drift/health)
- Serena (navigation/read + bounded project edits)
- Depwire (read/impact/verify)
- Tentra local (read/index)
- `sequential-thinking`
- Project-scoped filesystem operations (bounded writes inside the assigned worktree)

It must **not** automatically include: Bifrost administration, raw PostgreSQL, whole-drive filesystem access, destructive GitHub operations, unrestricted browser code execution, process attachment, hosted Tentra upload, direct secret access, live IDE configuration writes, or Swarm tools.

## Idempotency and safety

- Bootstrapping an already-governed project must be idempotent: existing governance files are preserved, missing ones are created from templates.
- The target must be an approved project root — never a Swarm path (`F:\AgentCore\agentmemory`, Swarm product installs), never a protected system path, never outside the assigned worktree.
- No secrets are read, written, or recorded during bootstrap.
- Existing project rules (`AGENTS.md`, `.cursor/rules/`, etc.) are preserved, not overwritten.
