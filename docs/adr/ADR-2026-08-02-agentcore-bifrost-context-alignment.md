# ADR-2026-08-02 — AgentCore Bifrost and Context Alignment

**Status:** Accepted
**Approval:** `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`
**Decision date:** 2026-08-02
**Owners:** Tony Valentine (operator) and AgentCore authority-maintainer

## Context

The accepted Context Engine and neutral SwarmRecall rollout changed the platform from isolated per-client memory toward one governed cross-host context system, but several authority/current-state documents still contained pre-cutover storage, SwarmRecall, Context Fabric, and Cursor-ownership language. Separately, OmniRoute, Graphify, Hindsight, and CrewAI were being evaluated conceptually, creating a risk that an agent would install or wire them before their distinct roles and admission gates were clear.

## Decision

Adopt the following stable responsibility model:

- AgentCore owns canonical truth, immutable evidence, exact recovery, policy state, and generated projections.
- Bifrost owns the sole normal IDE MCP front door, MCP aggregation, authentication, capability policy, leases, audit, and upstream lifecycle.
- The portable Context Engine owns rolling-context orchestration above the stable `agentcore-memory` facade.
- Neutral shared SwarmRecall is a machine-level semantic projection reached server-side through `agentcore-memory`, not a canonical ledger or raw IDE MCP.
- Context Fabric is adopted as a project-local committed-snapshot and drift-warning plane. It is rebuildable and subordinate to the authority chain and PG18.
- Arabold Docs is the local version-labelled official-document cache for external implementation decisions.
- Cursor is a bounded implementation/review surface. The AgentCore authority-maintainer owns architecture, protected contracts, live runtime wiring, security decisions, final validation, and Git integration.

MCP traffic and model inference traffic are separate. `agentcore-gateway` does not make Cursor model prompts traverse Bifrost. A future OmniRoute experiment must be placed on an explicitly governed inference route, not assumed to compress MCP traffic automatically.

OmniRoute, Graphify, Hindsight, and CrewAI remain disabled evaluation candidates with the roles and gates recorded in `docs/superpowers/specs/2026-08-02-agentcore-bifrost-context-alignment-design.md`. They do not become dependencies of the Context Engine or the IDE baseline through this ADR.

## Consequences

- All managed IDEs keep exactly one MCP entry named `agentcore-gateway`.
- Context Fabric runs through its repository-local hook/CLI. Its shared Bifrost upstream is dormant because Bifrost does not forward trustworthy caller/project identity to a shared STDIO child.
- Serena, Depwire, Tentra, filesystem, and Context Fabric remain dormant in shared profiles when their calls lack explicit project/worktree identity. Native IDE tools and explicit-cwd local processes are the safe interim route.
- The four machine-global project-router controls are operator-only maintenance and are not a concurrent-session security boundary.
- One governed Bifrost recycle applied the corrected profile and upstream disposition; no IDE configuration changed.
- Context Fabric can expose stale committed context immediately without becoming a second memory authority.
- Future inference compression, code-atlas, learning/reflection, and worker experiments can be evaluated independently and rolled back independently.
- The portable Context Engine may later expose optional adapter manifests, but only accepted integrations ship enabled.
- Swarm execution, vaults, credentials, and runtime remain isolated. The neutral Recall service is the sole shared semantic exception and is reached through bounded adapters on each side.

## Rejected alternatives

1. Make OmniRoute the MCP aggregator: rejected because Bifrost already owns the governed MCP contract, and current OmniRoute documentation does not establish arbitrary external MCP aggregation as the required production role.
2. Make Hindsight canonical memory: rejected because its retain/learning model is derived memory and does not preserve AgentCore's immutable exact-evidence guarantees.
3. Make Graphify replace source inspection or Serena: rejected because a structural graph is an index and must retain exact-source fallback and freshness evidence.
4. Make CrewAI a second top-level orchestrator: rejected because LangGraph already owns durable workflow/checkpoint authority.
5. Continue assigning the entire build to Cursor: rejected because protected authority, live runtime, and cross-system integration need one accountable AgentCore authority-maintainer; Cursor remains valuable for bounded code work and independent review.

## Validation and rollback

Acceptance requires protected-file hashes, deterministic repository validators, authenticated builder/operator Bifrost probes, successful memory health, Arabold retrieval proof, Context Fabric committed-state capture/drift proof, current-schema Cursor agents, independent review, and scoped Git push evidence.

Rollback restores the protected/source files from `E:\AgentCore-Backups\agentcore-control-plane\context-alignment-20260802-232010` and the immediately pre-remediation Bifrost runtime config/database backup from `E:\AgentCore-Backups\agentcore-control-plane\project-isolation-20260803-003135`, rerenders, performs one governed scheduled-task recycle, reruns validators and live probes, and records a dedicated rollback commit.
