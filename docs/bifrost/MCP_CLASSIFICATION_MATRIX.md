# MCP Classification Matrix — Bifrost Upstream

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`
**Updated:** 2026-07-12
**Scope:** Non-Swarm AgentCore gateway only. Swarm* excluded.

| Canonical ID | Bifrost client name | Connection | Scope | Write class | Status | Profiles |
|--------------|---------------------|------------|-------|-------------|--------|----------|
| arabold-docs | arabold_docs | stdio | global | read_only | active | builder, reviewer, docs-knowledge, database-validator, operator |
| serena | serena | router | project | bounded_write | active | builder, reviewer |
| sequential-thinking | sequential_thinking | stdio | global | read_only | active | builder, reviewer, docs-knowledge |
| cursor-agent-mcp | cursor_agent_mcp | stdio | global | write_capable | active | builder |
| context-fabric | context_fabric | router | project | bounded_write | active | builder, reviewer |
| mcp-debugger | mcp_debugger | stdio | project | admin | active | builder (attach denied for reviewer) |
| artiforge | artiforge | http | global | bounded_write | active | builder, operator |
| depwire | depwire | router | project | write_capable | active | builder, reviewer, operator |
| depwire-cloud | depwire_cloud | http | global | read_only | **disabled/deferred** | builder, operator (when enabled) |
| tentra | tentra | router | project | bounded_write | active | builder |
| obsidian-vault | obsidian_vault | stdio | global | bounded_write | active | builder, reviewer, docs-knowledge, operator |
| playwright | playwright | stdio | global | bounded_write | active | builder |
| filesystem | filesystem | router | project | bounded_write | active | builder, reviewer |
| github-mcp | github_mcp | stdio | global | write_capable | **deferred/disabled** | builder, operator (when enabled) |
| agentcore-memory | agentcore_memory | stdio | global | read_only | active (may be degraded) | builder, reviewer, database-validator, operator |
| agentcore-project-router | agentcore_project_router | stdio | global | bounded_write | active | all profiles |

## Explicit exclusions (must not appear in non-Swarm IDE baselines)

| Name / path | Reason |
|-------------|--------|
| swarmrecall / SwarmRecall | Separate Swarm ecosystem |
| swarmvault / SwarmVault | Separate Swarm ecosystem |
| swarmclaw / SwarmClaw / AgentSwarm | Separate Swarm ecosystem |
| `F:\AgentCore\agentmemory` | Swarm memory root; rejected by project router |
| context7 | Forbidden route |
| raw mem0 / direct composio | Forbidden route |
| whole-drive filesystem roots | Forbidden |
| direct Postgres credentials in IDE configs | Forbidden |

## Notes

- Bifrost MCP client names use underscores; AgentCore canonical IDs keep hyphens.
- Project-scoped servers must launch through `scripts/project_router` wrappers after `project_activate`.
- Counts implemented in registry: **14 enabled**, **2 disabled/deferred** (`depwire-cloud`, `github-mcp`) — as validated by `scripts/bifrost/validate_contracts.py` in-repo.
