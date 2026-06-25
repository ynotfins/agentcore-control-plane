# Drive Write Boundary Rule

`D:\MCP-Control-Plane` is the authority for agent storage policy on this PC.

## Default Write Policy

Agents may write by default only to the approved AgentCore roots:

- Active work: `F:\AgentCore`
- Cold archive and backups: `E:\AgentCoreArchive`

Agents must not write to these drives unless the user explicitly instructs them for the current task:

- `C:`
- `D:`
- `G:`
- `H:`
- `I:`

Read-only inspection of those drives is allowed when needed for audit, discovery, validation, or migration planning.

## Stop Policy

If an agent cannot write to an approved drive, or if a tool attempts to redirect writes to an unapproved drive, the agent must stop immediately and notify the user.

The agent must not silently fall back to another drive.

Examples that require stopping:

- `F:\AgentCore` is missing, read-only, unavailable, full, or has permission errors.
- `E:\AgentCoreArchive` is missing when writing backups, exports, or snapshots.
- An IDE reinstall recreates default workspace paths under `C:`.
- A package/tool tries to write project state under `D:`, `G:`, `H:`, or `I:` without explicit user approval.

## Approved Use Cases

Use `F:\AgentCore` for:

- active agent workspaces
- PostgreSQL runtime
- PostgreSQL data cluster
- pgvector memory writes
- ingestion staging
- hot backups

Use `E:\AgentCoreArchive` for:

- cold backups
- database snapshots
- raw exports
- large archived artifacts
- rollback bundles that do not contain raw secrets

## Secret-Bearing Backups

Raw secret-bearing backups are still restricted to:

`D:\Autonomy\secrets-backups`

Do not move raw secret-bearing backups into `F:\AgentCore` or `E:\AgentCoreArchive` unless a future explicit security policy replaces this rule.

## Required First Read

Before any persistent write, agents must read:

- `D:\MCP-Control-Plane\AGENT_DATABASE_BOOTSTRAP.md`
- `D:\MCP-Control-Plane\contracts\global-memory-database-contract.json`
- `D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`
