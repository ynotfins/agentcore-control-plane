---
document: CONTEXT_BLOCK.md
project: AgentCore Global Memory, Context, Database, and Governance Platform
authority: current-state-and-implementation-progress (level 4 in DOC_AUTHORITY.md hierarchy)
status: current
verified_at: 2026-08-04
canonical_repository: D:\github\agentcore-control-plane
locked_blueprint: BLUEPRINT.md
implementation_authority: docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md
current_acceptance: audits/AGENTCORE_LANGGRAPH_AUTHORITY_RECONCILIATION_2026-08-04.md
current_alignment_approval: AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION
---

# AgentCore Canonical Context Block

Read `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `BLUEPRINT.md` before this file. `BLUEPRINT.md` owns stable architecture and locked outcomes. This file owns mutable current posture. Generated `.agentcore/STATE.md`, `.agentcore/DECISIONS.md`, and `.agentcore/CONTEXT_INDEX.md` are subordinate projections and must not be edited directly.

## 0. Current platform posture — VERIFIED 2026-08-04

| Area | Current fact | Evidence/status |
| --- | --- | --- |
| Repository | `D:\github\agentcore-control-plane`, branch `main`, pre-change HEAD `4b4c507` | Git; inherited Langfuse/M6-M8/IDE-rule/registry WIP remains unstaged and is excluded from this reconciliation |
| Bifrost | Native `2.0.0-prerelease1` under `F:\AgentCore\runtime\bifrost`; scheduled owner `\AgentCore\AgentCore-Bifrost-Gateway`; `127.0.0.1:8080/health` healthy | Live status and gateway acceptance pass |
| IDE MCP front door | Exactly one `agentcore-gateway` at `http://127.0.0.1:8080/mcp` | Cursor live config: one entry, environment-backed bearer, no MCP_DOCKER |
| Gateway surface | Exact ten-tool `agentcore-memory` identity retained; ordinary profiles exclude the operator router | Live authenticated probes are required for mutable totals; do not copy a point-in-time aggregate tool count into client configuration |
| AgentCore memory | source and live `agentcore-memory` `0.9.1`; PG18 reachable at `127.0.0.1:55433` | Every scoped call requires exact enrolled `project_key` + `project_root`; task sessions are also bound to client, agent, device, user, canonical repository, and worktree; ten-tool identity unchanged |
| Project enrollment | `contracts/agentcore-project-enrollment.json`; default deny; exact key + exact repository/worktree path | Shared by Cursor bootstrap, memory facade, operator router, and child launcher; ordinary IDEs cannot mutate enrollment/router state |
| Device identity | `legacy_compat`; writes require signed device assertion; unsigned reads remain temporarily permitted | `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md`; migration window ends 2026-08-09 |
| Cognee | `available`, version `1.3.0`, isolated native Windows venv under `F:\AgentCore\runtime\agentcore-memory\cognee` | Live `memory_status` after governed v0.9.1 promotion; canonical retrieval remains PostgreSQL-backed |
| Neutral Recall | Machine-level neutral semantic plane healthy at `127.0.0.1:3300`; hot data under `H:\SwarmData\recall` | `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`; server-side AgentCore adapter only |
| Context Engine | Source repo `D:\github\agentcore-context-engine` at v0.2.1 release-candidate commit `2faa91a9fff6dc82fb9e3862c5ceb811a5cb4bd3`; machine package/manifest still reports v0.2.0 | `agentcore-context validate --live` fails `engine_version`; v0.2.1 is **not accepted** until exact installation, full live lifecycle proof, and independent exact-SHA review pass |
| LangGraph production | PG18 PostgresSaver is live; RUN11 remains valid point-in-time evidence with 23 checkpoints | Repo venv repaired; locked topology `a86e40e8…` and 88 workflow unit/boundary tests passed on 2026-08-04; a new post-v0.2.1 production canary is still required |
| LangGraph Studio | Dev-only `127.0.0.1:2024`; Agent Server dev checkpointer; never production thread IDs | `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md` |
| Context Fabric | Repo-local hook/CLI; DB schema/search-index 2, integrity ok, hook installed/ready, capture `#123` at `97c872cd98e8`; shared Bifrost upstream is dormant because caller/project identity is not forwarded | Raw Windows drift is falsely HIGH under `core.autocrlf=true`; 683/709 mismatches are CRLF-only; final accepted-HEAD capture pending |
| Arabold Docs | Required corpus indexed and retrieval-proven for Context Fabric, Cursor, Hindsight/cookbook, OmniRoute compression, Graphify, and CrewAI; Bifrost official corpus refreshed but remains unversioned in Arabold metadata | Live `list_libraries`, `find_version`, and targeted `search_docs`; installed Bifrost binary remains `2.0.0-prerelease1` |

The Bifrost process is healthy now. Prior Cursor “Not connected” incidents with a healthy direct gateway are classified as intermittent IDE MCP discovery/session state, not evidence that the Bifrost server was down. Do not restart or redesign Bifrost until gateway and upstream probes fail.

## 1. Accepted architecture

```text
AgentCore / enrolled non-Swarm IDE or workflow
  |
  +-- MCP tools --> agentcore-gateway / Bifrost :8080
  |                  +-- agentcore-memory (10-tool facade)
  |                  +-- operator-only project-router maintenance
  |                  +-- other governed upstreams by profile/lease
  |                  +-- no implicit-project filesystem/semantic/drift upstreams
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
| Rolling context and host portability | Context Engine | v0.2.0 point-in-time accepted; v0.2.1 release recertification pending |
| Shared semantic projection | Neutral SwarmRecall | Live/healthy |
| Project committed context and drift | Context Fabric | Adopted repo-locally; shared Bifrost exposure dormant |
| Current upstream documentation | Arabold Docs | Required candidate corpus indexed and retrieval-proven; Bifrost corpus has an explicit metadata limitation |
| Semantic code intelligence | Native IDE/project-local tools; Serena catalogued | Shared Bifrost Serena dormant until explicit per-session routing exists |
| Production autonomy | LangGraph | Live baseline; commercial launch recertification pending final Context Engine and lifecycle gates |
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

1. Context Engine v0.2.1 source and the installed v0.2.0 package/manifest disagree; current live validation fails `engine_version`.
2. `AgentCore-PostgreSQL18` is registered `Automatic` but stopped while a separate launcher owns the healthy PG18 process. Do not restart the database during another worker's canary; reconcile to one governed owner and prove reboot recovery.
3. Neutral Recall has no live-proven global/per-project pool provisioning in the current acceptance evidence, and AgentCore projection calls must consistently carry the intended pool identity before project-pool isolation is claimed.
4. `agentcore.wf_runs.completed_at` can remain null when `status=completed`; status is authoritative until the metadata bug is fixed.
5. RUN11's builder used the project root rather than its intended isolated worktree path.
6. Full `required` device enforcement for reads is deferred; signed writes are enforced.
7. Cursor IDE MCP discovery has been intermittent even while direct Bifrost health and authenticated tools/list pass.
8. The ChatGPT compatibility proxy expected on `127.0.0.1:18081` has no governed lifecycle owner and is currently down. Direct Bifrost remains the authoritative health surface.
9. Context Fabric retains six historical failed-capture records. Its Windows drift metric is unusable under `core.autocrlf=true` until upstream/fork comparison uses Git clean-filter/object semantics; repo-local capture/query/health remain usable.
10. Shared Bifrost project-bound developer upstreams are dormant until a per-session project identity can be injected. Native IDE tools and explicit-cwd local CLIs are the safe interim path.

## 4. Context Fabric disposition — ADOPTED

Context Fabric is the project-local committed-state/drift plane, not memory authority.

- One `.context-fabric` root exists at the Git repository root.
- Captures represent committed Git objects. Uncommitted files are reported as drift and never promoted as the accepted snapshot.
- Its SQLite/runtime state is rebuildable and subordinate to PG18, protected authority documents, Git, and accepted audits.
- Run repo-local `cf_drift` and bounded `cf_query` at architecture-sensitive task/Milestone entry; do not use the shared gateway route.
- Run repo-local `cf_capture` after accepted commits and rerun `cf_drift` at exit.
- `cf_log_decision` is a convenience projection; approved ADRs and AgentCore evidence remain authoritative.
- Do not initialize or capture Swarm-owned repositories through AgentCore continuity.
- Treat raw Windows drift severity as advisory until the CRLF/Git-blob defect is fixed; preserve the measured classification in acceptance evidence.

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

- Production commands run from `D:\github\agentcore-control-plane\scripts` with `D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe -m agentcore workflow ...`.
- `scripts\bootstrap-runtime.ps1` is the supported create/repair path for that runtime. System Python is the bootstrap source or an explicit diagnostic fallback, not the production operator default.
- Production uses PG18 PostgresSaver and durable `agentcore.wf_*` metadata.
- Studio is interactive development only. It binds to loopback, uses the dev checkpointer, and cannot open production threads.
- Deep Agents remains a bounded LangGraph worker harness.
- CrewAI is not present in the production topology. Any future CrewAI node is an A/B-tested bounded worker.
- Critic, deterministic scorer, judge, drift gates, human pause/resume, and JIT capability leases remain governed by LangGraph/AgentCore.

## 10. Active alignment workstream

Approval: `AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION`.

1. Reconcile current authority, runbooks, and operator commands without rewriting point-in-time evidence.
2. Repair and verify the repository-owned Python runtime.
3. Complete and independently certify Context Engine v0.2.1 in its own repository.
4. Reconcile PG18 to one governed lifecycle owner after parallel canaries finish.
5. Prove neutral Recall pool/project isolation and run new LangGraph and SwarmClaw canaries.
6. Run protected-file, Bifrost, prompt, rule-render, IDE-scope, ecosystem-separation, documentation-drift, secret/junk, and diff validators.
7. Obtain a fresh-context independent review, commit only task-owned files, push, and capture final state.

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
- `audits/AGENTCORE_LANGGRAPH_AUTHORITY_RECONCILIATION_2026-08-04.md`
- `audits/CONTEXT_ENGINE_LANGGRAPH_RUN11_LIVE_2026-08-02.json`
- `audits/INDEPENDENT_REVIEW_CONTEXT_ENGINE_2026-08-02.md`
- `docs/adr/ADR-2026-08-01-neutral-shared-swarmrecall-context-engine.md`
- `docs/adr/ADR-2026-08-02-agentcore-bifrost-context-alignment.md`
- `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-02.md`
- `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
- `docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md`
