# Memory Contract — MAF Recall Realignment

## Canonical semantic store

**SwarmRecall** is the PC-native semantic memory / context plane.

- Reach it only through agentcore-gateway (http://127.0.0.1:8080/mcp) then **agentcore-memory** (server-side adapter).
- Recall REST listens on **127.0.0.1:3300** (adapter/service use).
- Recall Postgres is service-owned on **127.0.0.1:65432** — never wire AgentCore workers or IDE clients to it directly.
- Do not install raw SwarmRecall MCP or Recall keys into non-Swarm IDE baselines.

## Long rolling context for large human prompts

This workstation must support very large natural-language operator prompts without forcing the
operator to restate them every session.

- Durable memory is the long-context authority, not the current chat window.
- Compaction must be **non-destructive**. Summaries may help the active model, but they do not replace originals.
- Agents should preserve accepted operator prompts, decisions, evidence, validations, and handoffs with provenance.
- Before asking the operator to repeat prior context, agents should recover from memory, current handoffs, audit files, and repo-local state.
- Large prompts should be paired with strong retrieval and handoff behavior, not with ad-hoc second databases or bigger random caches.

## LangGraph checkpoints stay on PG18

- Production LangGraph checkpointer remains **PostgresSaver** on PostgreSQL **18** at **127.0.0.1:55433**.
- Databases: agent_core (and cognee_core as applicable).
- Checkpoint tables live in public (checkpoints, checkpoint_blobs, checkpoint_writes) created by PostgresSaver.setup().
- Hot data stays on **F:** (F:/PostgreSQL18/data and AgentCore runtime paths).

## No new MAF Postgres on F:

- Microsoft Agent Framework (when pinned later at agent-framework==1.15.0) is an SDK / host concern.
- MAF must **not** create a second memory database, must **not** use postgres://localhost:5432/agent_memory, and must **not** allocate a new Postgres cluster on F: for agent memory.
- MAF context providers should call the existing Recall path (placeholder: http://127.0.0.1:3300) behind the gateway adapter strategy — not open competing stores.

## Vault

- SwarmVault remains on **H:** under Swarm ownership.
- AgentCore may project via adapter only; no IDE raw Vault MCP requirement for non-Swarm baselines.

## Isolation summary

| Plane | Store | Port / path | Owner |
|-------|-------|-------------|-------|
| Semantic memory | SwarmRecall | :3300 / :65432 | Neutral Recall (via agentcore-memory) |
| Workflow checkpoints | PG18 | :55433 on F: | AgentCore / LangGraph |
| Swarm execution files | Vault / Claw | H: | swarm-ecosystem-control |
| MCP aggregation | Bifrost | :8080 | AgentCore gateway |
