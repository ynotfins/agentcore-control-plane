# Drive Write Boundary Rule

> **Updated 2026-07-14 (authority reconciliation).** Storage policy authority is
> `PROJECT_ANCHOR.md` §2 (drive roles) in `D:\github\agentcore-control-plane`.
> `D:\MCP-Control-Plane` is compatibility/live-ops evidence only — not an authority.
> Machine drive facts: `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`.

## Default Write Policy

Agents may write by default only to roles-appropriate roots:

- Source repos, projects, and assigned worktrees: `D:\github\<repo>` (and other explicitly assigned project roots on `D:`)
- Hot database/vector/index runtime: `F:\AgentCore` (via service/API/CLI wrappers only — no raw writes)
- Gateway/agent runtime state: `H:\AgentRuntime` (Bifrost runtime, Tentra data; managed by approved ops scripts — **never format or re-provision H:**)
- Cold archive and backups: `E:\AgentCoreArchive`
- Disposable scratch: `I:` (non-canonical data only)

Agents must not write outside these roots unless the user explicitly instructs them for the current task:

- `C:` (OS, apps, live IDE configs — app-owned; changes only through approved prompts/ops with backup)
- `G:` (backup target only)
- `J:` (portable media)
- Any location on `D:` outside the assigned repo/worktree

Read-only inspection of any drive is allowed when needed for audit, discovery, validation, or migration planning.

## Stop Policy

If an agent cannot write to an approved root, or if a tool attempts to redirect writes to an unapproved location, the agent must stop immediately and notify the user.

The agent must not silently fall back to another drive.

Examples that require stopping:

- `F:\AgentCore` is missing, read-only, unavailable, full, or has permission errors.
- `E:\AgentCoreArchive` is missing when writing backups, exports, or snapshots.
- An IDE reinstall recreates default workspace paths under `C:`.
- A package/tool tries to write project state outside the assigned worktree without explicit user approval.

## Approved Use Cases

Use `F:\AgentCore` (wrapper/service access only) for:

- PostgreSQL runtime and data cluster
- pgvector memory writes
- hot indexes and search runtime
- ingestion staging

Use `H:\AgentRuntime` (approved ops scripts) for:

- Bifrost gateway runtime (`H:\AgentRuntime\bifrost`)
- Tentra data (`H:\AgentRuntime\tentra\data`)
- hot spool/scratch for the future memory platform (per `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`)

Use `E:\AgentCoreArchive` for:

- cold backups
- database snapshots
- raw exports
- large archived artifacts
- rollback bundles that do not contain raw secrets

## Secret-Bearing Backups

Raw secret-bearing backups are still restricted to:

`D:\Autonomy\secrets-backups`

Do not move raw secret-bearing backups into `F:\AgentCore`, `H:\AgentRuntime`, or `E:\AgentCoreArchive` unless a future explicit security policy replaces this rule.

## Required First Read

Before any persistent write, agents must read (repo copies — never the `D:\MCP-Control-Plane` copies):

- `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md` (§2 drive roles, §13 hard gates)
- `D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md` (this file)
- For memory/database writes: `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`
