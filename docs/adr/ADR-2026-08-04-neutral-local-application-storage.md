# ADR-2026-08-04: Neutral Local-Application Storage

Status: accepted
Approval: `AUTH-2026-08-04-NEUTRAL-LOCAL-APPLICATION-STORAGE`

## Decision

`I:\LocalApps` is the durable hot-data tier for neutral local applications. It is neither AgentCore nor Swarm storage. Neutral application databases, indexes, runtime state, caches, and logs live under an isolated `I:\LocalApps\<AppName>` root. Cold backups live under `E:\LocalApps\Backups\<AppName>`.

AgentCore hot runtime and staging remain under `F:\AgentCore`; the AgentCore staging root is `F:\AgentCore\staging`. Source repositories, projects, worktrees, and build files remain on D:. C: remains Windows and installed programs. H: remains Swarm and neutral-Recall hot storage under its existing boundaries.

Each neutral application owns separate data roots, databases, indexes, credentials, services, logs, backups, and recovery. No application gains raw access to another application's database. Any AgentCore integration uses governed APIs or MCP, never shared database ownership.

## Odysseus application

- Source: `D:\odysseus`.
- Durable data: `I:\LocalApps\Odysseus\data`.
- Native database: SQLite.
- Native vector/RAG service: ChromaDB on `127.0.0.1:8100`.
- Compatibility path: `D:\odysseus\data` may be an NTFS junction to the durable data root after backup, quiescence, copy verification, and rollback proof.
- Backups: `E:\LocalApps\Backups\Odysseus`.
- Forbidden: direct AgentCore PG18, legacy AgentCore PG16, neutral Recall, SwarmVault, or any Swarm-owned database.

## Consequences

Existing AgentCore worktree/scratch code that targets I: must move to `F:\AgentCore\staging`. Generated IDE rules derive the drive boundary from `contracts/global-agent-policy.yaml`. Application migrations require exact process ownership, loopback binding, verified backup/restore, and a reversible source-path transition.

## Rollback

Restore protected authority files from the task's timestamped `E:\AgentCore\rollback` bundle. For Odysseus, stop only the verified Odysseus/Chroma processes, remove only the exact junction, restore the verified cold backup to `D:\odysseus\data`, and restart through the project launcher.
