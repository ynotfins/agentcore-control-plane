# Memory and State

## Canonical ownership

| Information | Owner | Access path |
| --- | --- | --- |
| AgentCore exact prompts, evidence, decisions, identity, provenance, artifacts | PostgreSQL 18 | `agentcore-gateway` to `agentcore-memory` |
| AgentCore concise current state | generated `.agentcore/STATE.md`, `DECISIONS.md`, `CONTEXT_INDEX.md` | projection worker; read-only to ordinary agents |
| AgentCore rolling context and recovery orchestration | portable Context Engine | signed host adapter and ten-tool memory facade |
| AgentCore autonomous workflow checkpoints | PG18 PostgresSaver | AgentCore LangGraph workflow only |
| Cross-client semantic projection | neutral SwarmRecall PG plus rebuildable Meilisearch | server-side projection behind `agentcore-memory` |
| SwarmClaw operational state | Swarm-owned native store | Swarm control plane |
| SwarmVault content and retrieval | SwarmVault | Swarm control plane |

## Session loop

1. Resolve exact enrolled `project_key` and `project_root` without machine-global router mutation.
2. Open or resume a stable task session.
3. Run `startup_context` with the selected model profile.
4. Append the visible operator prompt through the signed host lifecycle using a deterministic idempotency key.
5. Append durable facts and evidence after meaningful completed steps.
6. Retrieve bounded context when needed; expand exact sources before relying on summarized claims.
7. Generate state projections only through the authorized worker.
8. Build the handoff and close the session after verification.

## Hard rules

- Do not write raw transcripts into Recall as authority.
- Do not use Recall, Meilisearch, Cognee, or a chat summary to repair canonical PG18 evidence.
- Do not create a database, schema, memory copy, or STATE file per IDE.
- Do not lower a model's configured hard context limit to match a compact profile.
- Compaction is non-destructive; summaries never replace canonical originals.
- If projections are stale, retrieve and expand canonical events, then run the governed projector. Never patch projection text.
- No IDE receives PostgreSQL credentials, Recall credentials, raw SQL, or direct Swarm memory MCP entries.
