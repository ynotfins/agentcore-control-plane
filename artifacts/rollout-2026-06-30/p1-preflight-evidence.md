# P1 Preflight Evidence — AgentCore Swarm Rollout (2026-06-30)

Read-only proofs captured before P2 mutation. Source authority: `D:\github\agentcore-control-plane`.

## Listeners (netstat)
| Port | Service | Result |
|------|---------|--------|
| 55432 | PostgreSQL `agent_core` | LISTENING (pid 97876) |
| 3300 | SwarmRecall API | LISTENING |
| 7700 | Meilisearch | LISTENING |
| 27124 | Obsidian REST | LISTENING |
| 65432 | (forbidden) | none ✓ |
| 6333 / 6334 | Qdrant | none (out of core scope) ✓ |
| 5432 | n8n Postgres | none (not for agents) ✓ |
| 11434 | Ollama | none (optional; WARN) |
| 18789 | OpenClaw gateway | none (not running at preflight) |

## Health
- SwarmRecall `http://127.0.0.1:3300/api/v1/health` → `{"status":"ok","services":{"database":true}}` ✓
- Meilisearch `http://127.0.0.1:7700/health` → `{"status":"available"}` ✓
- Ollama `http://127.0.0.1:11434/api/tags` → not listening → tier **WARN** (optional layer; installed at `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`; no auto-pull)

## Paths
- Created (reversible): `E:\CodexMemory`, `E:\CodexMemory\markdown-vault` (env `CODEX_MEMORY_ROOT` / `CODEX_MEMORY_MARKDOWN_VAULT`).
- Reported MISSING (not created this pass; referenced by spool/backup contracts): `E:\AgentCoreArchive\{backups_cold,raw-corpora,cache,exports,memory-spool\pending}`.

## Git baseline
- Branch: `codex/agentcore-swarm-automation`; HEAD `823f032`.
- `database-plan.md`, handoff doc, `contracts/master-mcp-server-config.json` are UNTRACKED (commit deferred — hard gate).

## Backups (before mutation)
- `artifacts/backups/20260630-042231-p2-baseline/` — copies of master contract, supervisor json/yaml, generator, validator, registry, all renderers, operational installer.

## Env var names referenced (values never read/printed)
`AGENT_CORE_AGENT_INGEST_PASSWORD`, `AGENT_CORE_AGENT_READ_PASSWORD`, `AGENT_CORE_SWARMRECALL_API_KEY`, `AGENT_CORE_SWARMRECALL_DB_PASSWORD`, `AGENT_CORE_SWARMRECALL_MEILI_MASTER_KEY`, `OPENAI_API_KEY`, `ARTIFORGE_PAT`, `OBSIDIAN_API_KEY`, `OBSIDIAN_LOCAL_REST_API`, `CURSOR_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`.
