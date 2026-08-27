# AgentCore Feature Freeze Note — MAF Recall Realignment

## Freeze

Freeze **net-new AgentCore feature work** that expands memory planes, MCP surface area, or database topology until MAF and Recall are correctly seated behind the existing Bifrost gateway.

## Keep

- Keep **Bifrost** / `agentcore-gateway` at `http://127.0.0.1:8080/mcp` as the common MCP entry.
- Keep **SwarmRecall** as the semantic store via **agentcore-memory** (adapter only).
- Keep **LangGraph** checkpoints on **PG18** `:55433` on **F:**.
- Keep Swarm hot runtime on **H:** operationally isolated.

## Do not

- Do **not** wipe `F:` or `H:` as cleanup, migration shortcuts, or disk reclaim during this realignment.
- Do **not** stand up a new MAF Postgres on `F:` or `postgres://localhost:5432/agent_memory`.
- Do **not** paste raw Recall MCP / Recall keys / OpenRouter MCP into IDE baselines.
- Do **not** replace Bifrost with a MAF-hosted MCP aggregator in this phase.

## Unfreeze condition

Resume broader AgentCore feature work only after:

1. Common MCP policy is enforced on enrolled IDEs
2. Recall remains adapter-only behind `:8080`
3. MAF host (pin 1.15.0) is documented to bind behind the gateway without conflicting listeners
4. Post-build audit items for this package are completed or explicitly deferred with operator ACCEPT
