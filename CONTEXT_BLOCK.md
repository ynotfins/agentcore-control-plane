---
document: CONTEXT_BLOCK.md
project: AgentCore Global Memory, Context, Database, and Governance Platform
authority: current-state-and-implementation-progress (level 4 in DOC_AUTHORITY.md hierarchy)
status: current
verified_at: 2026-08-02
canonical_repository: D:\github\agentcore-control-plane
locked_blueprint: BLUEPRINT.md
implementation_authority: docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md
current_acceptance: audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md
current_alignment_approval: AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT
---

# AgentCore Canonical Context Block

Read `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `BLUEPRINT.md` before this file. `BLUEPRINT.md` owns stable architecture and locked outcomes. This file owns mutable current posture. Generated `.agentcore/STATE.md`, `.agentcore/DECISIONS.md`, and `.agentcore/CONTEXT_INDEX.md` are subordinate projections and must not be edited directly.

## 0. Current platform posture — VERIFIED 2026-08-02

| Area | Current fact | Evidence/status |
| --- | --- | --- |
| Repository | `D:\github\agentcore-control-plane`, branch `main`, pre-alignment HEAD `da9f6ccd4e4b9f646f213a4faecf95ba1586a75c` | Git; inherited Langfuse/M6-M8 WIP remains unstaged and outside this alignment |
| Bifrost | Native `2.0.0-prerelease1` under `F:\AgentCore\runtime\bifrost`; scheduled owner `\AgentCore\AgentCore-Bifrost-Gateway`; `127.0.0.1:8080/health` healthy | Live status and gateway acceptance pass |
| IDE MCP front door | Exactly one `agentcore-gateway` at `http://127.0.0.1:8080/mcp` | Cursor live config: one entry, environment-backed bearer, no MCP_DOCKER |
| Gateway surface | 161 discovered tools in the builder profile; exact 10 memory tools, 4 project-router tools, and at least 3 skills-hub tools | Live authenticated `tools/list`; no Swarm/raw SQL/whole-drive/Bifrost-admin tools |
| AgentCore memory | `agentcore-memory` `0.7.0`; PG18 reachable at `127.0.0.1:55433` | `memory_status: healthy` |
| Device identity | `legacy_compat`; writes require signed device assertion; unsigned reads remain temporarily permitted | `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md`; migration window ends 2026-08-09 |
| Cognee | `degraded_unavailable` / `ModuleNotFoundError` | Truthful degradation; canonical evidence/recovery remains healthy |
| Neutral Recall | Machine-level neutral semantic plane healthy at `127.0.0.1:3300`; hot data under `H:\SwarmData\recall` | `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`; server-side AgentCore adapter only |
| Context Engine | Portable repo `D:\github\agentcore-context-engine`, accepted HEAD `b7fa0a4285a93d36bf12f36bb27a5b3c38d4e835` | Final acceptance report; native host adapters certified |
| LangGraph production | PG18 PostgresSaver; RUN11 live cloud worker completed with 23 checkpoints, 6 evidence rows, judge `proceed`, critic `1.0` | Run `c376e23d-a2c5-4844-b8a9-f02cd905f690`; thread `034a28db-a7b4-4c9f-a967-a3ea00091130` |
| LangGraph Studio | Dev-only `127.0.0.1:2024`; Agent Server dev checkpointer; never production thread IDs | `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md` |
| Context Fabric | Correctly rebound through the project router to `agentcore-control-plane`; DB schema/search-index 2, integrity ok, hook installed/ready, latest successful capture `#122` at `da9f6ccd4e4b`; six historical failed-capture records remain | Live `project_activate` returned `project_scoped_reconnect.status=reconnected`; `cf_query` identifies the correct project; post-alignment capture pending |
| Arabold Docs | Required corpus indexed and retrieval-proven for Context Fabric, Cursor, Hindsight/cookbook, OmniRoute compression, Graphify, and CrewAI; Bifrost official corpus refreshed but remains unversioned in Arabold metadata | Live `list_libraries`, `find_version`, and targeted `search_docs`; installed Bifrost binary remains `2.0.0-prerelease1` |

The Bifrost process is healthy now. Prior Cursor “Not connected” incidents with a healthy direct gateway are classified as intermittent IDE MCP discovery/session state, not evidence that the Bifrost server was down. Do not restart or redesign Bifrost until gateway and upstream probes fail.

## 1. Accepted architecture

```text
AgentCore / enrolled non-Swarm IDE or workflow
  |
  +-- MCP tools --> agentcore-gateway / Bifrost :8080
  |                  +-- agentcore-memory (10-tool facade)
  |                  +-- project router -> project-scoped developer tools
  |                  +-- other governed upstreams by profile/lease
  |
  +-- host lifecycle adapter --> portable Context Engine
                                 +-- rolling context / handoff orchestration
                                 +-- agentcore-memory facade
                                 +-- no canonical database ownership

agentcore-memory
  +-- PG18 agent_core: canonical identity, evidence, summaries, policy, workflow metadata
  +-- PG18 LangGraph checkpoint tables: canonical production checkpoints
  +-- Cognee adapter: optional curated graph processing, currently degraded
  +-- neutral Recall adapter: semantic projection only
  +-- generated read-only STATE/DECISIONS/CONTEXT_INDEX projections
```

### Responsibility model

| Plane | Owner | Current state |
| --- | --- | --- |
| Canonical truth and recovery | AgentCore | Live |
| MCP aggregation and governance | Bifrost | Live |
| Rolling context and host portability | Context Engine | Accepted/current |
| Shared semantic projection | Neutral SwarmRecall | Live/healthy |
| Project committed context and drift | Context Fabric | Adopted and live project-bound; final post-commit capture pending this pass |
| Current upstream documentation | Arabold Docs | Required candidate corpus indexed and retrieval-proven; Bifrost corpus has an explicit metadata limitation |
| Semantic code intelligence | Serena through project router | Live project-scoped tool |
| Production autonomy | LangGraph | RUN11 live accepted |
| Bounded implementation/review | Cursor project subagents | Seven project roles present with current frontmatter, including authority-drift, Bifrost diagnosis, and MCP-contract roles |

### Separate MCP and inference planes

```text
MCP tools:
IDE -> Bifrost -> approved MCP upstreams

Model inference today:
host/application -> approved model provider path

Future experiment only:
host/application -> Bifrost inference governance -> OmniRoute -> OpenRouter -> model
```

The single `agentcore-gateway` MCP entry does not make Cursor model prompts traverse Bifrost or OmniRoute. RTK/Caveman savings apply only after an explicit model inference route is implemented and fidelity-tested.

## 2. Memory, context, and project isolation

- PG18 is the canonical exact-evidence and workflow authority.
- The Context Engine orchestrates rolling context above the stable `agentcore-memory` surface; it does not expose a second IDE gateway.
- Neutral Recall holds global/per-project semantic projections. It does not hold the only copy of raw prompts, LangGraph checkpoints, policy, or workflow state.
- SwarmClaw and LangGraph may use the same neutral Recall service through different bounded adapters, while execution state, databases, drives, credentials, and control planes remain separate.
- Every memory/session write includes project and session identity, idempotency, trust, and provenance. Cross-project writes and foreign-session writes are rejected.
- Originals remain recoverable through `retrieve_context` and `expand_source`; compaction never deletes canonical evidence.
- Multiple IDEs may work concurrently, including multiple projects. Each active session remains bound to one project/worktree identity; that does not prevent separate simultaneous sessions for other projects.
- If two IDEs work in one project, separate session identities share project-level accepted memory while preserving event ordering, idempotency, and provenance.

## 3. Host acceptance and true residuals

### Host certification

| Host | Context lifecycle certification | Important boundary |
| --- | --- | --- |
| Cursor | `live_validated_native_hooks_signed_gateway` | IDE MCP discovery can still require reconnect independently of Bifrost health |
| Claude Code | `live_validated_native_hooks` | MCP enrollment/discovery is a separate client proof |
| Codex | `live_validated_native_hooks` | MCP enrollment/discovery is a separate client proof |
| Generic MCP client | `companion_only_not_automatic` | No transparent lifecycle without a compatible hook/plugin/bridge |

### True residuals

1. `agentcore.wf_runs.completed_at` can remain null when `status=completed`; status is authoritative until the metadata bug is fixed.
2. RUN11's builder used the project root rather than its intended isolated worktree path.
3. Full `required` device enforcement for reads is deferred; signed writes are enforced.
4. Cursor IDE MCP discovery has been intermittent even while direct Bifrost health and authenticated tools/list pass.
5. Cognee import is degraded; canonical memory, exact recovery, checkpoints, and neutral Recall remain usable.
6. Context Fabric retains six historical failed-capture records. The current hook is installed/ready and the latest successful capture is healthy; this alignment still requires its own post-commit capture.

## 4. Context Fabric disposition — ADOPTED

Context Fabric is the project-local committed-state/drift plane, not memory authority.

- One `.context-fabric` root exists at the Git repository root.
- Captures represent committed Git objects. Uncommitted files are reported as drift and never promoted as the accepted snapshot.
- Its SQLite/runtime state is rebuildable and subordinate to PG18, protected authority documents, Git, and accepted audits.
- Run `cf_drift` and bounded `cf_query` at architecture-sensitive task/Milestone entry.
- Run `cf_capture` after accepted commits and rerun `cf_drift` at exit.
- `cf_log_decision` is a convenience projection; approved ADRs and AgentCore evidence remain authoritative.
- Do not initialize or capture Swarm-owned repositories through AgentCore continuity.

Current alignment acceptance requires: post-commit `cf_capture`, decision log, `cf_drift`, `cf_query(include_drift=true)`, and `cf_health` evidence.

## 5. Arabold documentation posture

Arabold is the first source for version-sensitive external behavior. If the required official version is not indexed, refresh/index it or stop and record the documentation gap; do not answer from model memory.

Required alignment corpus:

| Library | Required version/status | Role |
| --- | --- | --- |
| Bifrost | installed `2.0.0-prerelease1`; official corpus unversioned | Current production gateway contract |
| Cursor | `3.14.7` | Subagents, hooks, rules, MCP lifecycle |
| Context Fabric | `1.0.7` | Capture/drift behavior |
| Hindsight | `0.7.0` | Future learning/reflection evaluation only |
| OmniRoute | `3.8.49` | Future inference compression/routing evaluation only |
| Graphify | `0.9.22` | Future structural code-atlas evaluation only |
| CrewAI | `1.15.10` | Future bounded LangGraph worker evaluation only |

Only successfully indexed official sources may be marked current in `DOC_AUTHORITY.md`.

## 6. Future intelligence extensions — DISABLED / BENCHMARK-GATED

| Candidate | Permitted future role | Forbidden assumption |
| --- | --- | --- |
| OmniRoute | Inference-path RTK + Caveman compression/provider routing behind Bifrost governance | It is not the current MCP aggregator and does not automatically see Cursor model prompts |
| Graphify | Project-local structural code atlas via a governed Bifrost upstream | It cannot replace exact source reads, Serena, or Git freshness checks |
| Hindsight | Derived learning/reflection using isolated project/agent banks | It cannot become canonical/lossless memory or silently retain untrusted raw data |
| CrewAI | A/B-tested bounded worker inside selected LangGraph nodes | It cannot become a second top-level workflow/checkpoint authority |

No component above is installed, started, enrolled, or added to the Context Engine by this alignment. OmniRoute `3.8.49` is present as a global npm package but is not accepted as a production runtime route. Graphify and Hindsight commands were not found at preflight.

## 7. Execution ownership

- The AgentCore authority-maintainer owns architecture, protected contracts, Bifrost/runtime integration, security, acceptance, and Git. Codex is the execution lead for this alignment and Bifrost production hardening.
- Cursor receives bounded tasks where full repository context or a fresh independent context is the advantage: contract implementation, targeted code changes, tests, and independent review.
- Cursor subagents do not determine architecture. They follow `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `BLUEPRINT.md`, this file, and current acceptance evidence.
- The parent task controls model/cost. Custom project subagents default to `model: inherit`; use high-cost models only where task complexity justifies them.

## 8. Storage and ecosystem boundaries

| Drive/path | Current role |
| --- | --- |
| `C:` | Windows, installed applications, user/IDE configuration |
| `D:\github\...` | Canonical source repositories and active development |
| `E:\AgentCore\...` | AgentCore cold/archive/backup target; transitional `E:\AgentCore-Backups` still exists |
| `F:\AgentCore\...` | AgentCore hot runtime including Bifrost; PG18 at `F:\PostgreSQL18\data` |
| `G:` | Independent backup copy |
| `H:\SwarmData\recall` | Neutral Recall hot physical data |
| `H:\SwarmData\claw` and other Swarm-owned H: roots | Swarm execution/runtime data; forbidden to AgentCore normal ops |
| `I:` | AgentCore disposable staging/cache only |
| `J:` | Portable transfer; outside normal AgentCore writes |

The neutral Recall physical placement on H: does not authorize AgentCore filesystem access to H:. AgentCore reaches it only over the bounded localhost service adapter.
AgentCore must never format H: or treat any H: path as an AgentCore canonical or rollback target.

## 9. Current autonomous workflow

- Production commands run from `D:\github\agentcore-control-plane` using `python -m agentcore workflow ...`; if `python` is not on PATH, use the verified installed Python executable rather than changing architecture.
- Production uses PG18 PostgresSaver and durable `agentcore.wf_*` metadata.
- Studio is interactive development only. It binds to loopback, uses the dev checkpointer, and cannot open production threads.
- Deep Agents remains a bounded LangGraph worker harness.
- CrewAI is not present in the production topology. Any future CrewAI node is an A/B-tested bounded worker.
- Critic, deterministic scorer, judge, drift gates, human pause/resume, and JIT capability leases remain governed by LangGraph/AgentCore.

## 10. Active alignment workstream

Approval: `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`.

1. Reconcile `BLUEPRINT.md`, this file, `DOC_AUTHORITY.md`, `MASTER_CONFIG_AND_PROMPT.md`, `MILESTONES.md`, and `AGENTS.md`.
2. Index/refresh the required official Arabold corpus and prove retrieval.
3. Add three focused Cursor project subagents using the current official schema.
4. Run protected-file, Bifrost, prompt, rule-render, IDE-scope, ecosystem-separation, secret/junk, and diff validators.
5. Obtain a fresh-context independent review.
6. Commit the authority/subagent change, capture the committed state in Context Fabric, record acceptance, create the final acceptance commit, push, and capture the final HEAD.

## 11. Hard stops

Stop and request operator review for:

- a change to the single `agentcore-gateway` MCP identity or endpoint;
- a new canonical database, vector store, graph store, workflow authority, or raw IDE memory route;
- any OmniRoute/Hindsight/Graphify/CrewAI runtime activation;
- any client model-inference reroute;
- a live IDE configuration write outside a separately approved enrollment task;
- a Swarm repository/runtime/database/credential/backup mutation;
- direct edits to generated AgentCore projections;
- failed rollback hash, authority validator, independent review, or secret scan;
- a conflict between protected authority and verified live evidence that cannot be reconciled inside the approval.

## 12. Primary evidence

- `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md`
- `audits/CONTEXT_ENGINE_LANGGRAPH_RUN11_LIVE_2026-08-02.json`
- `audits/INDEPENDENT_REVIEW_CONTEXT_ENGINE_2026-08-02.md`
- `docs/adr/ADR-2026-08-01-neutral-shared-swarmrecall-context-engine.md`
- `docs/adr/ADR-2026-08-02-agentcore-bifrost-context-alignment.md`
- `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-02.md`
- `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
- `docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md`
