# Canonical Global Agent Rules

**Source of truth:** `contracts/global-agent-policy.yaml` (policy_revision 2026-07-14).
This file is the human-readable rendering. Per-IDE renderings live under `ide-profiles/<ide>/GLOBAL_RULES.md` and must not contradict it.

## Mandatory rules

1. **AgentCore authority.** `D:\github\agentcore-control-plane` is the single source authority. Read order: `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `CONTEXT_BLOCK.md` → `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` → Bifrost contracts/handoff → `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md` (machine facts). `D:\MCP-Control-Plane` is evidence only.
2. **One Bifrost gateway entry.** Non-Swarm IDEs use exactly one MCP entry: `agentcore-gateway` at `http://127.0.0.1:8080/mcp` with `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`. Never paste the upstream registry or direct per-tool MCP entries into IDE configs.
3. **Swarm isolation.** SwarmRecall, SwarmVault, and SwarmClaw are a separate ecosystem. Never require Swarm MCP servers, Swarm databases, or Swarm file roots for non-Swarm work. Never modify Swarm product installs. OpenClaw/ClawX are Swarm-managed.
4. **New Project Bootstrap.** Every new managed project runs Milestone 0 per `docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md` before broad implementation.
5. **Milestone execution.** Work is organized in Milestones (outcome boundaries) with entry and exit gates per `docs/agent-policy/MILESTONE_EXECUTION_STANDARD.md`.
6. **Macro and Micro steps.** Macro steps are workstreams with Micro checklists; Micro steps are atomic and independently verifiable.
7. **Evidence-backed checklists.** Status vocabulary: `pending` / `in_progress` / `passed` / `blocked` / `failed` / `skipped_with_reason`. `passed` requires an evidence reference. Markdown checkboxes are generated projections of machine-readable state.
8. **Context Fabric checkpoints.** Capture and drift checks at every Milestone entry and exit; unresolved drift blocks closure.
9. **Arabold exact-version documentation.** Mandatory before dependency or external-API work; documentation checkpoint per Milestone.
10. **Milestone tool audits.** Audit the tool surface at every Milestone entry and exit per `docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`.
11. **Progressive tool disclosure.** Only tools needed for the current project and Milestone are actively exposed. Projects begin with the Bootstrap profile. Runtime lease enforcement arrives with memory-platform M6; until then the tool manifest records desired state and agents honor it behaviorally.
12. **Write boundaries.** Write only inside the assigned repo/worktree and role-appropriate runtime roots per `docs/DRIVE_WRITE_BOUNDARY_RULE.md`. Never expose whole-drive filesystem roots. Never format H: (live Bifrost runtime).
13. **Secrets.** Windows User-scope environment variables only. No `.env` files. Never print, store, or commit secret values. Missing variable → stop and report the name.
14. **No direct database access.** Normal IDE agents never connect to PostgreSQL directly and hold no database credentials. Memory flows through `agentcore-gateway` → `agentcore-memory`.
15. **Git safety.** Push after every completed task with narrow validation and a secret/junk scan first. Never pull/fetch/merge/rebase or force-push without explicit operator instruction. See `docs/GIT_PUSH_ONLY_POLICY.md`.

## Forbidden routes

`context7` · raw Mem0 (rejected for v1; must not be installed) · direct Composio · `global-memory-gateway` (retired identity) · direct per-IDE MCP baselines · whole-drive filesystem MCP roots · Postgres credentials in IDE configs · Swarm MCP in non-Swarm IDE baselines · port `:65432`.
