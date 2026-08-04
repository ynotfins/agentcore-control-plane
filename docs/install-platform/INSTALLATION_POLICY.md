# AgentCore Install Intake Policy

**Authority:** `PROJECT_ANCHOR.md` -> `DOC_AUTHORITY.md` -> this policy.
**Applies to:** every new local app, source repo, MCP server, IDE plugin, skill, Python/Node runtime, Windows service, scheduled task, database-backed tool, vector store, and model-provider helper installed on this PC.

## Purpose

New installs must pass through AgentCore control-plane intake before they create durable state. The goal is simple: source code can stay easy to work with, but databases, vector stores, caches, runtime data, secrets, MCP exposure, and project continuity must land in the right owned location.

## Hard Rules

1. Do not place durable databases, vector stores, app data, runtime state, or persistent caches on `C:` or `D:`.
2. Source repositories may live on `D:\github\...` or another approved source root.
3. Third-party local app data defaults to `I:\LocalApps\<AppName>\...`.
4. Third-party local app backups default to `E:\LocalApps\Backups\<AppName>\...`.
5. AgentCore-owned databases and runtime state remain AgentCore-owned. Do not attach third-party apps directly to AgentCore PG18, Bifrost SQLite, Cognee, LangGraph checkpoints, or AgentCore memory tables.
6. Swarm and neutral Recall storage remain under their own authority. Do not attach third-party apps directly to SwarmRecall, SwarmVault, SwarmClaw, or Swarm-owned databases.
7. Integration with AgentCore memory uses `agentcore-gateway` -> `agentcore-memory` only.
8. Integration with MCP uses the governed Bifrost/AgentCore path only after approval. Do not add raw MCP servers directly to IDEs as the default path.
9. Secrets live only in Windows User-scope environment variables. Do not write real secrets to `.env`, source files, config files, prompts, or committed docs.
10. Before migration or repair, create a rollback backup and record the exact source path, target path, health check, and rollback command.

## Default Storage Layout

| Purpose | Default Location |
| --- | --- |
| Source repo | `D:\github\<repo>` or approved source root |
| App database | `I:\LocalApps\<AppName>\data\...` |
| Vector/index data | `I:\LocalApps\<AppName>\indexes\...` |
| Runtime files | `I:\LocalApps\<AppName>\runtime\...` |
| Logs | `I:\LocalApps\<AppName>\logs\...` |
| Caches | `I:\LocalApps\<AppName>\cache\...` |
| Backups | `E:\LocalApps\Backups\<AppName>\...` |
| Source-local compatibility path | NTFS junction from source path to `I:\LocalApps\<AppName>\...`, only after backup |

## Intake Sequence

1. Identify the app, repo, installer, and purpose.
2. Classify the scenario using `SCENARIO_CATALOG.yaml`.
3. Locate the project root before editing. For Git repos, use `git rev-parse --show-toplevel`.
4. Inspect the app's default storage behavior before install or launch.
5. Choose source, data, backup, runtime, and log paths from `contracts/install-target-policy.json`.
6. Decide whether the app needs AgentCore project enrollment.
7. If enrolled, create or update project-root `AGENTS.md` and `CLAUDE.md` using AgentCore rules.
8. If the app exposes MCP, keep it dormant until Bifrost registration and capability exposure are explicitly approved.
9. Write an install manifest or report before mutation.
10. Validate health after install and record rollback instructions.

## Database-backed App Rule

If an app tries to create SQLite, Chroma, LanceDB, DuckDB, Postgres data, Qdrant data, Meilisearch data, or any other durable local database under `C:` or `D:`, stop and redirect it to `I:\LocalApps\<AppName>`.

If the app only supports a project-relative path, create a source-local compatibility junction after a verified backup:

```text
D:\path\to\repo\data  ->  I:\LocalApps\<AppName>\data
```

Do not create the junction until the source and target paths are exact and the rollback copy exists.

## Odysseus Current Classification

Current observed project root: `D:\odysseus`.

Odysseus is a third-party local app/source repo with web UI and local durable stores. It must not use AgentCore PG18, legacy PG16, neutral SwarmRecall PG/Meili, or any inherited global `DATABASE_URL`. Its durable app data should live under:

```text
I:\LocalApps\Odysseus
```

If upstream expects `D:\odysseus\data`, use a junction from `D:\odysseus\data` to `I:\LocalApps\Odysseus\data` after backing up the existing directory to `E:\LocalApps\Backups\Odysseus`.

## Stop Conditions

Stop before mutation if any of these are true:

- The installer wants a database on `C:` or `D:`.
- The installer wants to reuse AgentCore, Swarm, or neutral Recall database paths directly.
- The app needs a secret and no Windows User-scope environment variable name has been approved.
- The app wants to bind a service to `0.0.0.0` or open firewall ports.
- The project root cannot be proven.
- The app's storage behavior cannot be identified.
- A rollback backup cannot be created.
