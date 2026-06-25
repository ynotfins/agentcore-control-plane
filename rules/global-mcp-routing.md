# Global MCP Routing Rules

## Enforced Order

1. Planning and strategy: `sequential-thinking`.
2. Repository code exploration and refactors: Serena.
3. Current software, SDK, CLI, API, cloud, and package docs: `arabold-docs`.
4. Governed PostgreSQL/pgvector memory: `global-memory-gateway`.
5. Project continuity, commit context, and drift briefings: `context-fabric`, only inside approved Git-managed target repos.
6. Architecture or codebase quality scan: `artiforge`.
7. Browser/UI validation: Browser or Playwright, only when a UI target exists.
8. External web content: Firecrawl search or scrape when current web evidence is required.
9. Connected accounts and SaaS workflows: app connectors only when the user explicitly asks.

## Fallback Policy

Critical tools are `global-memory-gateway`, `arabold-docs`, `artiforge`, and `sequential-thinking`.

If a critical primary fails:

- Use a fallback only when it preserves output quality and governance.
- Do not replace `global-memory-gateway` with raw Mem0 for normal memory work.
- Do not bypass `global-memory-gateway` with ad hoc direct SQL for normal memory work.
- Do not choose ad hoc embedding models; the gateway owns the embedding provider contract.
- Do not replace `arabold-docs` with stale model memory for current library/API guidance.
- Do not use `context-fabric` as a general memory layer; it is for project continuity and drift tracking.
- Do not replace `sequential-thinking` with `thinking-patterns`; `thinking-patterns` is retired.
- If no high-quality fallback exists, stop and notify the user with the failing tool, evidence, and next repair step.

## Quarantine

- `composio` is quarantined by default.
- `mem0_mcp_server` is quarantined for normal-agent memory use.
- `context7` is retired and must not be emitted into generated client renderers.
- `artiforge__codebase_scanner` is retired in favor of `artiforge`.
- Quarantined tools must not be emitted into client renderers unless a later approved rollout changes the lifecycle.
