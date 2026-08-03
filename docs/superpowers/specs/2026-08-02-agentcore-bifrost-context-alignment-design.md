# AgentCore Bifrost and Context Alignment Design

**Approval:** `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`
**Status:** Approved for authority reconciliation and drift-control rollout
**Scope:** AgentCore authority, current-state documentation, local documentation indexing, project-local Context Fabric, and Cursor specialist subagents
**Excluded from this rollout:** OmniRoute inference routing, Hindsight runtime, Graphify runtime, CrewAI runtime, new MCP upstreams, new databases, and Swarm runtime changes

## Outcome

Establish one unambiguous operating model for the PC so every managed AgentCore agent reads the same architecture, current facts are captured from verified evidence, external behavior is resolved from locally indexed official documentation, and Cursor is used only for bounded specialist work that benefits from a separate context window.

## Responsibility model

| Plane | Owner | Binding role |
| --- | --- | --- |
| Canonical truth and recovery | AgentCore | PG18 immutable evidence, exact expansion, workflow/checkpoint state, governed projections, and recovery |
| MCP aggregation and governance | Bifrost | Sole normal IDE MCP front door, authentication, tool policy, progressive disclosure, leases, audit, and upstream lifecycle |
| Rolling context | Portable Context Engine above `agentcore-memory` | Cross-host session lifecycle, model-budgeted assembly, compaction orchestration, and handoff portability |
| Shared semantic projection | Neutral SwarmRecall | Machine-level global/per-project semantic projection, reached server-side through `agentcore-memory`; never canonical evidence or a raw IDE MCP |
| Project commit context and drift | Context Fabric | Repo-local committed snapshot, decision log, query briefing, and drift warning; not global memory or an immutable ledger |
| Current external documentation | Arabold Docs | Local, version-labelled index of official upstream documentation used before version-sensitive decisions |
| Semantic code intelligence | Native IDE/project-local tools; Serena optional | Explicit-project symbol navigation and safe refactor evidence; shared Bifrost Serena is dormant |
| Autonomous production workflow | LangGraph | Durable, checkpointed AgentCore workflow with bounded workers, critic, scorer, judge, and human gates |
| Bounded implementation and review | Cursor subagents | Focused code review, runtime diagnosis, contract implementation, and verification; never architecture authority |

## Two transport planes

MCP tool traffic and model inference traffic are different paths.

```text
MCP tools:
IDE -> agentcore-gateway (Bifrost :8080/mcp) -> approved MCP upstreams

Model inference today:
host/application -> approved provider path

Possible future inference experiment:
host/application -> Bifrost inference governance -> OmniRoute compression/routing -> OpenRouter -> model
```

An IDE using `agentcore-gateway` for MCP does not imply that its model prompts pass through Bifrost or OmniRoute. Any future OmniRoute benefit must be proven on the model request path without changing the single MCP gateway contract.

## Optional intelligence extensions

The following are evaluation candidates, not current dependencies:

| Candidate | Proposed future role | Admission gate |
| --- | --- | --- |
| OmniRoute | Inference-path RTK + Caveman compression and provider routing behind Bifrost governance | Official-version pin, request/response fidelity tests, quality/cost/latency benchmark, failure bypass, and rollback |
| Graphify | Project-local structural code atlas exposed as a governed Bifrost upstream | Exact-source fallback, freshness proof, token benchmark, project isolation, and no authority promotion |
| Hindsight | Derived learning/reflection plane using isolated per-project/per-agent banks | Async retain/recall policy, provenance links, poisoning tests, no raw canonical ownership, and measured quality gain |
| CrewAI | Bounded worker implementation inside selected LangGraph nodes | A/B benchmark against existing workers, checkpoint compatibility, deterministic evidence, and no orchestration authority |

These candidates may be represented in the portable Context Engine as disabled adapter interfaces or capability manifests only after their individual admission tests pass. They are not bundled as mandatory runtimes and do not change AgentCore, Bifrost, LangGraph, or neutral Recall ownership.

## Context Fabric disposition

Adopt Context Fabric behind AgentCore as the project-local committed-state and drift plane.

- Its root is exactly the Git repository root.
- Its shared Bifrost client is dormant. Use the repository-local hook/CLI so the Git root is explicit and concurrent IDE sessions cannot redirect one shared child.
- It captures committed Git objects; uncommitted files are drift, not a new snapshot.
- Its SQLite database and runtime remain under `.context-fabric/` and are non-canonical/rebuildable.
- `cf_capture` and `cf_drift` run at Milestone entry/exit and after an accepted authority commit.
- `cf_query` may provide a bounded briefing, but the authority read order still wins.
- `cf_log_decision` records a convenience projection of accepted decisions; approved ADRs and PG18 evidence remain authoritative.
- Context Fabric never scans Swarm-owned roots through an AgentCore session.

## Cursor execution model

Codex/AgentCore authority-maintainer owns architecture, contracts/renderers, runtime wiring, security boundaries, live rollout, final validation, and Git integration. Cursor receives only focused work packages after the relevant authority and acceptance contract are already explicit.

Project-owned Cursor subagents must be few, focused, version-controlled, and default to `model: inherit` so the operator controls cost from the parent model. Read-only reviewers must declare `readonly: true`. Subagents must read the authority chain and return evidence; they cannot authorize a protected change or certify their own implementation.

## Acceptance

This alignment is accepted when:

1. `BLUEPRINT.md`, `CONTEXT_BLOCK.md`, `DOC_AUTHORITY.md`, and `MASTER_CONFIG_AND_PROMPT.md` describe the same responsibility model and current neutral-memory exception.
2. The current Context Engine acceptance, RUN11, Bifrost health, memory health, and true residuals are represented without overstating client or optional-component status.
3. Arabold contains retrieval-proven official documentation for current production components and the four future candidates; any source without version metadata (currently Bifrost) is recorded as an explicit limitation rather than assigned a false documentation version.
4. Context Fabric captures the accepted Git state after commit and reports a bounded, explainable drift status.
5. Two or three focused Cursor subagents use the current official `.cursor/agents/*.md` schema and are discoverable from the project.
6. Authority, Bifrost, prompt-format, ecosystem-separation, and narrow test validators pass; ordinary profiles expose no machine-global project mutation, and operator exposes exactly four maintenance controls.
7. Rollback files, before/after hashes, independent review, scoped commit, and push evidence exist.
