# Drift Prevention

Generated: 2026-06-24

## Purpose

The drift-prevention system records durable project facts and detects when key control-plane architecture files change.

The authoritative database table is:

`project_facts`

The daily drift script is:

`D:\MCP-Control-Plane\ops\Test-AgentCoreDrift.ps1`

## What Gets Tracked

Current drift tracking hashes these files:

- `D:\MCP-Control-Plane\AGENT_DATABASE_BOOTSTRAP.md`
- `D:\MCP-Control-Plane\contracts\global-memory-database-contract.json`
- `D:\MCP-Control-Plane\docs\AGENTCORE_STORAGE_DESIGN.md`
- `D:\MCP-Control-Plane\docs\MCP_SERVER_CONFIGURATION_REFERENCE.md`
- `D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`

Each file hash is stored as a versioned fact:

```text
fact_key = file_hash:<relative-path>
fact_value = { path, sha256, checked_at }
```

## Versioning Model

When a tracked file changes:

1. The current fact is marked `is_current = false`.
2. A new fact is inserted with `version = previous + 1`.
3. The new fact references the old one through `supersedes_fact_id`.

This preserves immutable historical facts while exposing the latest version.

## Maintenance Agent Workflow

The designated maintenance agent should:

1. Run `D:\MCP-Control-Plane\ops\Test-AgentCoreDrift.ps1`.
2. Review new `project_facts` versions.
3. If a change reflects an intended architecture decision, update relevant docs and store a compact memory through `global-memory-gateway`.
4. If a change is unintended, stop and notify the user.
5. Never silently rewrite facts to hide drift.

## Schedule

Windows scheduled task:

- Task: `AgentCore\DailyDriftCheck`
- Time: `04:00`
- Command: `D:\MCP-Control-Plane\ops\Test-AgentCoreDrift.ps1`

## Notifications

Current local notification surface is the database itself and the generated automation status file.

Future extension:

- route drift notifications through AgentMail or another approved notification MCP only when the user explicitly enables external notifications.

## Stop Conditions

The drift checker or maintenance agent must stop and notify the user if:

- PostgreSQL is unavailable.
- `agent_ingest` cannot insert into `project_facts`.
- tracked files are missing.
- hashes change unexpectedly.
- an approved drive write fails.
