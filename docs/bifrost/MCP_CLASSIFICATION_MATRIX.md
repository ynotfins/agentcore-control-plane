# MCP Classification Matrix — Bifrost Upstream

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`
**Updated:** 2026-07-20
**Scope:** Non-Swarm AgentCore gateway only. Swarm* excluded.
**Dormant catalog:** `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md`
**Architecture authority:** `BLUEPRINT.md` (this matrix must not invent alternate memory identities or Swarm wiring)

| Canonical ID | Bifrost client name | Connection | Scope | Write class | Status | Profiles |
| -- | -- | -- | -- | -- | -- | -- |
| arabold-docs | arabold_docs | stdio | global | read_only | active | builder, reviewer, docs-knowledge, database-validator, operator |
| serena | serena | router | project | bounded_write | active | builder, reviewer |
| sequential-thinking | sequential_thinking | stdio | global | read_only | active | builder, reviewer, docs-knowledge |
| cursor-agent-mcp | cursor_agent_mcp | stdio | global | write_capable | active | builder |
| context-fabric | context_fabric | router | project | bounded_write | active | builder, reviewer |
| mcp-debugger | mcp_debugger | stdio | project | admin | **disabled** | builder (when enabled; attach denied for reviewer) |
| artiforge | artiforge | http | global | bounded_write | **disabled** | builder, operator (when enabled) |
| depwire | depwire | router | project | write_capable | active | builder, reviewer, operator |
| depwire-cloud | depwire_cloud | http | global | read_only | **disabled/deferred** | builder, operator (when enabled) |
| tentra | tentra | router | project | bounded_write | active | builder |
| obsidian-vault | obsidian_vault | stdio | global | bounded_write | active | builder, reviewer, docs-knowledge, operator |
| playwright | playwright | stdio | global | bounded_write | active | builder |
| filesystem | filesystem | router | project | bounded_write | active | builder, reviewer |
| github-mcp | github_mcp | stdio | global | write_capable | **deferred/disabled** | builder, operator (when enabled) |
| agentcore-memory | agentcore_memory | stdio | global | read_only | active (10-tool surface live) | builder, reviewer, database-validator, operator |
| agentcore-project-router | agentcore_project_router | stdio | global | bounded_write | active | all profiles |

## OpenRouter MCP — registered dormant

| Canonical ID | Bifrost client name | Connection | Auth | Scope | Write class | Status | Profiles (JIT-eligible) |
| -- | -- | -- | -- | -- | -- | -- | -- |
| openrouter | openrouter | http | oauth | global | bounded_write | **dormant** (lifecycle: authenticated_dormant) | operator (JIT only; zero tools without M6 lease + bridge) |

### OpenRouter tool groups

| Group | Access policy | Tools |
| -- | -- | -- |
| openrouter-discovery-read | jit_short | list-models, get-model, list-model-endpoints, list-providers, list-daily-model-rankings, list-app-rankings, list-benchmarks, list-task-classifications, search-docs, view-skills, ping, **get-preset**, **list-presets** |
| openrouter-account | operator_scope | get-credits, get-generation, send-feedback |
| openrouter-media-generation | billable_approval | **generate-speech** (operator-approved JIT; raw_untrusted) |
| openrouter-transcription | billable_approval | **transcribe-audio** (operator-approved JIT; upload forbid repo/secrets; raw_untrusted) |
| openrouter-billable | billable_approval | send-message, generate-image (**denied by default** — never from discovery leases) |

## Explicit exclusions (must not appear in non-Swarm IDE baselines)

| Name / path | Reason |
| -- | -- |
| swarmrecall / SwarmRecall | Separate Swarm ecosystem |
| swarmvault / SwarmVault | Separate Swarm ecosystem |
| swarmclaw / SwarmClaw / AgentSwarm | Separate Swarm ecosystem |
| `F:\AgentCore\agentmemory` | Swarm memory root; rejected by project router |
| context7 | Forbidden route (`blocked_authority` — do not register dormant to weaken this) |
| Hostinger | Forbidden route (`blocked_authority`) |
| raw mem0 / direct composio | Forbidden route |
| whole-drive filesystem roots | Forbidden |
| direct Postgres credentials in IDE configs | Forbidden |

## Notes

- Bifrost MCP client names use underscores; AgentCore canonical IDs keep hyphens.
- Project-scoped servers must launch through `scripts/project_router` wrappers after `project_activate`.
- Counts implemented in registry: **13 enabled** (including openrouter dormant), **4 disabled/deferred** (`mcp-debugger`, `artiforge`, `depwire-cloud`, `github-mcp`) — as validated by `scripts/bifrost/validate_contracts.py` in-repo.
- OpenRouter is registered dormant: zero tools exposed without an active M6 capability lease + `scripts/bifrost/jit_vk_bridge.py`. See `docs/operations/OPENROUTER_MCP.md`. LangGraph clients use the same localhost gateway path (`docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`).
- Future GitLab/GitKraken/Firecrawl/Sheets/Cloudflare/AgentMail/Vercel/docs MCP entries remain catalogued pending official pin + named inventory; they are not live Bifrost clients until an enablement gate passes.
