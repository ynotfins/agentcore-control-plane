# Global MCP Routing Rules

> **Bifrost-first (2026-07-14):** All tools below are reached through the single IDE MCP entry
> `agentcore-gateway` (`http://127.0.0.1:8080/mcp`, Bearer `${env:BIFROST_MCP_VIRTUAL_KEY}`).
> Do not paste direct per-tool MCP entries into IDE configs. Registry authority:
> `contracts/bifrost-upstream-mcp-registry.json`.

## Enforced Order

1. Planning and strategy: `sequential-thinking` (via gateway).
2. Repository code exploration and refactors: Serena (via gateway / project router).
3. Deterministic dependency graph, blast radius, structural simulation, and pre-action verification: `depwire` (via gateway).
4. Current software, SDK, CLI, API, cloud, and package docs: `arabold-docs` (via gateway).
5. Governed memory: `agentcore-memory` via `agentcore-gateway` (the retired `global-memory-gateway` identity must not be reintroduced).
6. Project continuity, commit context, and drift briefings: `context-fabric`, only inside approved Git-managed target repos.
7. Architecture or codebase quality scan: `artiforge` (currently disabled/deferred in the registry; use only when re-enabled).
8. Browser/UI validation: Browser or Playwright, only when a UI target exists.
9. External web content: Firecrawl search or scrape when current web evidence is required.
10. Connected accounts and SaaS workflows: app connectors only when the user explicitly asks.

## DepWire Policy

- Primary route: `depwire` upstream through `agentcore-gateway`. The global `depwire-cli@1.8.2` at `C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd mcp` is a diagnostics-only fallback.
- Telemetry stays enabled. Do **not** set `DEPWIRE_NO_TELEMETRY` unless the operator explicitly requests it.
- The CLI/MCP server has no DepWire API/license-key variable. DepWire Pro applies only to the VS Code/Cursor extension setting `depwire.licenseKey`; never copy that key into MCP config.
- Connect verified local repository paths only. A remote URL can trigger clone/pull behavior and requires explicit operator approval.
- DepWire complements Serena: Serena owns semantic navigation and targeted edits; DepWire owns deterministic dependency edges, impact analysis, structural simulation, verification, architecture health, and graph-aware security.
- Before delete/move/rename/split/merge or risky multi-file refactors, use `impact_analysis` and `simulate_change`; before completion, use `verify_change` plus native project validators.
- Keep `connect_repo`, `visualize_graph`, `update_project_docs`, `claim_files`, `release_files`, and `record_decision` behind approval because they may perform remote or filesystem side effects.
- `connect_repo` creates `.depwire/cache.db`; keep the entire `.depwire/` directory and `depwire-output.json` in the global Git excludes file and never commit them.
- Do not treat DepWire decision logs as the normal durable memory path. Use claims only for explicitly authorized parallel work and release them when work ends.

## Serena Lifecycle Policy

- Serena is project-scoped code intelligence, not a cross-project global daemon.
- Managed IDE configs must use the installed Serena executable at `C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe`.
- Do not emit `uvx --from git+https://github.com/oraios/serena` in default renderers or live IDE configs.
- Default Serena transport is `stdio`; Streamable HTTP is allowed only for an explicit same-project multi-client session.
- Use `--project-from-cwd` only for CLI-style clients that Serena documents for this mode and that are launched from the target repository root.
- Historical 11-IDE rollout details are `D:\MCP-Control-Plane` evidence only (not authority); current Serena wiring lives in `contracts/bifrost-upstream-mcp-registry.json` and `docs/SERENA_CONFIGURATION.md`.

## Fallback Policy

Critical tools are `agentcore-gateway`/Bifrost, `agentcore-memory`, `arabold-docs`, and `sequential-thinking`.

If a critical primary fails:

- Use a fallback only when it preserves output quality and governance.
- Do not replace `agentcore-memory` with raw Mem0 for normal memory work (Mem0 is rejected and must not be installed).
- Do not bypass `agentcore-memory` with ad hoc direct SQL for normal memory work.
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
