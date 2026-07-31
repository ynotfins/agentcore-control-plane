# Drive Write Boundary Rule

> **Updated 2026-07-31 (ecosystem separation reconciliation).** Storage policy authority is
> `PROJECT_ANCHOR.md` §2 (drive roles) and the Ecosystem and Drive Separation header in
> `D:\github\agentcore-control-plane`.
> `D:\MCP-Control-Plane` is compatibility/live-ops evidence only — not an authority.
> Machine drive facts: `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`.

## Default Write Policy

Agents may write by default only to roles-appropriate roots:

- Source repos, projects, and assigned worktrees: `D:\github\<repo>` (and other explicitly assigned project roots on `D:`)
- Hot database/vector/index runtime: `F:\AgentCore` (via service/API/CLI wrappers only — no raw writes)
- AgentCore Bifrost / AgentRuntime state: `F:\AgentCore\runtime` (including `bifrost`, clients, Tentra, MCP helpers; managed by approved ops scripts)
- AgentCore cold archive and backups: under `E:\AgentCore\...` only (for example `E:\AgentCore-Backups`, `E:\AgentCoreArchive`)
- Disposable scratch / staging: `I:` (non-canonical data only)

Agents must not write outside these roots unless the user explicitly instructs them for the current task:

- `C:` (OS, apps, live IDE configs — app-owned; changes only through approved prompts/ops with backup)
- `G:` (second backup copy target only)
- `H:` (reserved for Swarm after M9 acceptance — never AgentCore final runtime/data home; never format or re-provision)
- `J:` (portable media)
- `E:\Swarm\...` (Swarm cold/backup — outside AgentCore write authority)
- Any location on `D:` outside the assigned repo/worktree

Read-only inspection of any drive is allowed when needed for audit, discovery, validation, or migration planning. Historical `H:\AgentRuntime` was AgentCore-owned prior to relocation and must not be treated as current AgentCore authority.

## Stop Policy

If an agent cannot write to an approved root, or if a tool attempts to redirect writes to an unapproved location, the agent must stop immediately and notify the user.

The agent must not silently fall back to another drive.

Examples that require stopping:

- `F:\AgentCore` is missing, read-only, unavailable, full, or has permission errors.
- An approved `E:\AgentCore\...` backup root is missing when writing backups, exports, or snapshots.
- An IDE reinstall recreates default workspace paths under `C:`.
- A package/tool tries to write project state outside the assigned worktree without explicit user approval.
- A tool attempts to place AgentCore canonical runtime, Bifrost state, or durable rollback material on `H:`.

## Approved Use Cases

Use `F:\AgentCore` (wrapper/service access only) for:

- PostgreSQL runtime and data cluster
- pgvector memory writes
- hot indexes and search runtime
- ingestion staging

Use `F:\AgentCore\runtime` (approved ops scripts) for:

- Bifrost gateway runtime (`F:\AgentCore\runtime\bifrost`)
- Tentra data (`F:\AgentCore\runtime\tentra\data`)
- client cache/logs/scratch under `F:\AgentCore\runtime\clients\{client_key}\`
- hot spool/scratch for the memory platform (per `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`)

Use `E:\AgentCore\...` for:

- cold backups
- database snapshots
- raw exports
- large archived artifacts
- rollback bundles that do not contain raw secrets

## Secret-Bearing Backups

Raw secret-bearing backups are still restricted to:

`D:\Autonomy\secrets-backups`

Do not move raw secret-bearing backups into `F:\AgentCore`, historical `H:\AgentRuntime`, or `E:\AgentCore\...` roots unless a future explicit security policy replaces this rule.

## Required First Read

Before any persistent write, agents must read (repo copies — never the `D:\MCP-Control-Plane` copies):

- `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md` (§2 drive roles, §13 hard gates)
- `D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md` (this file)
- For memory/database writes: `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`
