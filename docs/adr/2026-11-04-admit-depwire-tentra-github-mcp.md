# ADR: Admit Depwire, Tentra, and GitHub MCP into Bifrost gateway

- Status: Proposed
- Date: 2026-11-04 (America/New_York)
- Context: Tony authorized installing and wiring Depwire, Tentra, GitHub MCP, Serena, Sequential Thinking, Arabold docs-mcp-server, and evaluating Context7 into agentcore-gateway (Bifrost MCP at 127.0.0.1:8080/mcp).

## Decision
1. Keep Serena, Sequential Thinking, Arabold docs, Context7, and Morph as already-active Bifrost clients.
2. Promote Depwire and Tentra from `dormant_project_scoped` to `active` with runtimes pinned under `I:\LocalApps\<App>`.
3. Promote GitHub MCP from `deferred` to `active` using the existing docker digest pin and `GITHUB_PERSONAL_ACCESS_TOKEN` (User scope present). Monitor first `tools/list` because prior admission marked tool inventory unresolved.
4. Keep both Arabold docs-mcp-server and Context7: Arabold owns local/custom indexing; Context7 owns hosted popular-library docs. They overlap only partially — both worth keeping.
5. Schema PR #8 must land (or be included) so registry validation accepts `admission_evidence` / extended status enums.

## Consequences
- Bifrost `client_configs` gain `depwire`, `tentra`, `github_mcp` and those names are attached to builder/operator/ide/openclaw virtual keys.
- Missing env for Tony: `CONTEXT7_API_KEY` (Context7 already wired), `ATLAS_CLOUD_API_KEY` (unrelated provider), `TENTRA_API_KEY` not required for local mode.
- Bifrost may need a process refresh to pick up config.json changes.
