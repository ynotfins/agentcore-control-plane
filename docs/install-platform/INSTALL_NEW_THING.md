# Install New Thing

Use this as the operator entrypoint before installing or repairing any app, repo, MCP server, IDE plugin, skill, service, runtime, or database-backed tool.

## Operator Input

Provide:

```text
Name:
Source URL or installer:
Purpose:
Expected UI/runtime:
Does it need a local database or vector store:
Does it need MCP access:
Does it need AgentCore project continuity:
```

## Agent Requirements

Before changing anything, the agent must:

1. Read `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, this install policy, `SCENARIO_CATALOG.yaml`, and `contracts/install-target-policy.json`.
2. Confirm the active repo and branch if working in a Git repo.
3. Locate the target project root. For Git repos, run:

```powershell
git -C '<candidate-path>' rev-parse --show-toplevel
```

4. Inspect existing config, storage paths, launcher scripts, and service/task definitions.
5. Produce an install plan with exact source, data, backup, runtime, log, and cache paths.
6. Stop for approval before install, migration, service creation, config write, MCP registration, or project enrollment.

## Required Output

The agent must produce:

```text
Project/app root:
Install scenario:
Source location:
Data/database location:
Backup location:
Runtime/log/cache location:
MCP exposure:
Memory/project continuity:
Secrets/env vars:
Rollback plan:
Validation checks:
Commands pending approval:
```

## Default Decision

If the app has any durable local database or vector store, default to:

```text
I:\LocalApps\<AppName>
```

If the app is source-controlled and upstream expects a repo-local `data` directory, use a junction only after backup:

```text
<RepoRoot>\data -> I:\LocalApps\<AppName>\data
```

Do not use AgentCore, Swarm, or neutral Recall databases as the app's backing store unless a current approved ADR says so.
