# Global MCP Routing Rules

## Enforced Order

1. Planning and strategy: `sequential-thinking`.
2. Repository code exploration and refactors: Serena.
3. Deterministic dependency graph, blast radius, structural simulation, and pre-action verification: `depwire`.
4. Current software, SDK, CLI, API, cloud, and package docs: `arabold-docs`.
5. Governed PostgreSQL/pgvector memory: `global-memory-gateway`.
6. Project continuity, commit context, and drift briefings: `context-fabric`, only inside approved Git-managed target repos.
7. Architecture or codebase quality scan: `artiforge`.
8. Browser/UI validation: Browser or Playwright, only when a UI target exists.
9. External web content: Firecrawl search or scrape when current web evidence is required.
10. Connected accounts and SaaS workflows: app connectors only when the user explicitly asks.

## DepWire Policy

- Use global `depwire-cli@1.8.2` through `C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd mcp` with `DEPWIRE_NO_TELEMETRY=1`.
- The CLI/MCP server has no DepWire API/license-key variable. DepWire Pro applies only to the VS Code/Cursor extension setting `depwire.licenseKey`; never copy that key into MCP config.
- Connect verified local repository paths only. A remote URL can trigger clone/pull behavior and requires explicit operator approval.
- DepWire complements Serena: Serena owns semantic navigation and targeted edits; DepWire owns deterministic dependency edges, impact analysis, structural simulation, verification, architecture health, and graph-aware security.
- Before delete/move/rename/split/merge or risky multi-file refactors, use `impact_analysis` and `simulate_change`; before completion, use `verify_change` plus native project validators.
- Keep `connect_repo`, `visualize_graph`, `update_project_docs`, `claim_files`, `release_files`, and `record_decision` behind approval because they may perform remote or filesystem side effects.
- `connect_repo` creates `.depwire/cache.db`; keep the entire `.depwire/` directory and `depwire-output.json` in the global Git excludes file and never commit them.
- Do not treat DepWire decision logs as the normal durable memory path. Use claims only for explicitly authorized parallel work and release them when work ends.

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
