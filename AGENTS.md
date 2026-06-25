# CHAOSCENTRAL MCP Control Plane Agent Contract

This repository, `D:\MCP-Control-Plane`, is the single source of truth for MCP governance, renderer candidates, and repo validators.

## Operating Rules

- Work only in this repository unless the user explicitly authorizes live rollout.
- Do not edit live client configs during repo-only phases.
- Create a timestamped rollback copy before editing existing managed files.
- Use unlock -> edit -> validate -> re-lock for managed files.
- Patch `scripts/mcp_control_plane.py` first when generated outputs would otherwise drift.
- Keep supervisor JSON, supervisor YAML, registry, renderers, and validators aligned.
- Use deterministic validators before reporting completion.
- Agents must read `AGENT_DATABASE_BOOTSTRAP.md` and `contracts/global-memory-database-contract.json` before persistent memory writes or database ingestion.

## Tool Routing

- Planning: use `sequential-thinking` for ambiguous multi-step strategy.
- Repo code work: use Serena first for project activation, symbol discovery, and targeted refactors.
- Current software, SDK, CLI, API, cloud, and package docs: use `arabold-docs` first. Keep docs indexed/current before answering implementation guidance.
- Project continuity and drift context: use `context-fabric` only for approved Git-managed workspaces; do not initialize it in global infrastructure directories.
- Memory: use `global-memory-gateway` as the governed PostgreSQL/pgvector primary path. Do not route normal agents to raw Mem0 or ad hoc direct SQL.
- Embeddings: use the gateway-owned provider contract (`text-embedding-3-small` at 1536 dimensions when `OPENAI_API_KEY` is available; `local_hash_v1` only as offline fallback).
- Architecture scans: use `artiforge` only for high-leverage scans and refactor strategy.
- Connected app workflows: keep Composio quarantined until explicitly re-enabled.

## Stop Policy

For `global-memory-gateway`, `arabold-docs`, `artiforge`, and `sequential-thinking`, do not silently downgrade. If the primary fails and no high-quality fallback exists, stop and notify the user.

## Database Contract

- Control-plane authority: `D:\MCP-Control-Plane`
- Bootstrap contract: `D:\MCP-Control-Plane\AGENT_DATABASE_BOOTSTRAP.md`
- Machine contract: `D:\MCP-Control-Plane\contracts\global-memory-database-contract.json`
- Database: PostgreSQL `agent_core` on `127.0.0.1:55432`
- Vector store: `global_vector_memory_store` with pgvector `VECTOR(1536)`
- Normal write path: `global-memory-gateway` tools only
- Trusted direct SQL path: explicit ingest/admin runners approved by the control plane
