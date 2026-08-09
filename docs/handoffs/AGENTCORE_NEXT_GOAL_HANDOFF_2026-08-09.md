# AgentCore Next Goal Handoff - Bifrost, MCP Placement, SwarmRecall, And Runtime Finish

**Created:** 2026-08-09 03:24 -04:00
**Repository:** `@D:\github\agentcore-control-plane`
**Purpose:** Seed the next Codex/Cursor Goal Mode run with the current verified state, the correct authority model, the immediate MCP answer, and the ordered completion plan.

## Read Order

Read these before changing anything:

1. `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`
2. `@D:\github\agentcore-control-plane\DOC_AUTHORITY.md`
3. `@D:\github\agentcore-control-plane\BLUEPRINT.md`
4. `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`
5. `@D:\github\agentcore-control-plane\docs\current\PC_MEMORY_CONTEXT_WIRING_2026-08-05.md`
6. `@D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md`
7. `@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`
8. `@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json`
9. `@D:\github\agentcore-control-plane\docs\operations\DORMANT_MCP_CAPABILITY_CATALOG.md`
10. `@D:\github\agentcore-control-plane\SERENA.md`

## Non-Negotiable Mental Model

AgentCore and Swarm remain separate control planes. They share the machine and one neutral semantic memory plane only.

```text
AgentCore / enrolled IDEs
  -> one MCP entry: agentcore-gateway
  -> Bifrost on 127.0.0.1:8080/mcp
  -> agentcore-memory ten-tool facade
  -> PG18 for exact evidence, policy, recovery, and LangGraph checkpoints
  -> server-side projection to neutral SwarmRecall for semantic memory/context

SwarmClaw / Sally
  -> owns Swarm runtime, agents, tasks, sessions, recovery, SwarmVault, and Swarm lifecycle
  -> uses neutral SwarmRecall through Swarm's own bounded adapter
  -> does not use AgentCore PG18, Bifrost, LangGraph checkpoints, or AgentCore IDE profiles
```

`agentcore-memory` is not deprecated. It is the governed AgentCore facade and stable upstream identity behind `agentcore-gateway`. SwarmRecall is the PC-native semantic memory/context plane behind bounded adapters; it is not a raw MCP entry for ordinary IDEs and not the LangGraph checkpoint database.

## Verified Current Facts

- Cursor global MCP file is clean: `@C:\Users\ynotf\.cursor\mcp.json` contains exactly one server, `agentcore-gateway`.
- Bifrost direct health is good: `http://127.0.0.1:8080/health` returned `{"status":"ok","components":{"db_pings":"ok"}}`.
- `bifrost-http.exe` is running from `F:\AgentCore\runtime\bifrost\bin\bifrost-http.exe`.
- Bifrost status script passed ordinary profile checks: 10 `agentcore-memory` tools, 0 ordinary project-router tools, at least 3 Skills Hub tools, total visible tools 34.
- Loopback listeners observed with `netstat`: `:8080`, `:3300`, `:3456`, `:7700`, and `:55433`.
- Swarm PG on `:65432` was not observed listening in the quick probe. Treat this as a Swarm/Sally post-restart validation item before claiming full Swarm DB health.
- `H:\SwarmData` is readable and contains `backups`, `claw`, `logs`, `meilisearch`, `pids`, `postgres`, `postgres-native`, `recall`, `vault`, and `canary-payload.json`.
- `G:` is currently absent/unplugged.
- `@D:\github\agentcore-control-plane` has inherited dirty/untracked work. Preserve it; stage only task-owned files.
- `@D:\github\swarm-ecosystem-control` is on `master...origin/master` with untracked `evidence/`.
- `@D:\github\agentcore-context-engine` is on `main...origin/main` with untracked `.agentcore/runtime/`.
- Separate hardening worktree exists at `@D:\github\agentcore-control-plane-bifrost-hardening`, branch `codex/bifrost-production-hardening`.

## Immediate MCP Placement Answer

The four temporary project-level MCP servers from the operator's prompt are acceptable only as short-lived, project-local indexing tools for `@D:\github\nfa-alerts-enterprise` if the user explicitly wants that one-time indexing pass. They should not become global Cursor MCP entries and should not be permanently added to Bifrost until each passes official-source, pin, storage, security, tool-inventory, and rollback review.

Temporary project-local use is reasonable for:

- `mcp-codebase-search`
- `code-search` with `--allowed-workspace ${workspaceFolder}`
- `codebase-memory-mcp`
- `@zilliz/claude-context-mcp@latest`, only if its OpenAI/Milvus env variables are intentionally configured and the data path is accepted

After the indexing pass:

1. preserve generated index/memory artifacts inside the project if they are useful and non-secret;
2. remove or disable the temporary project-level MCP entries;
3. do not promote any generated memory-bank/index output into AgentCore or SwarmRecall as authority without review;
4. document the tool, artifact path, version, and reason in a project-local note if the result is kept.

Do not add `command-runner` globally. It is arbitrary command execution. Do not add project-bound memory-bank/codebase-memory globally. They compete with the governed memory model and depend on project path/cwd.

## Current MCP Classification

Active through Bifrost today:

- `agentcore-memory`
- `agentcore-project-router` operator-only
- `arabold-docs`
- `cursor-agent-mcp`
- `mcp-prompt-optimizer`
- `openrouter` connected but zero-default/JIT-only
- `playwright`
- `sequential-thinking`
- `skills-hub`

Foundational but not globally active:

- `serena`: dormant project-scoped; use native IDE tools or an explicit project-owned local Serena process until trusted per-session project identity exists.
- `depwire`: dormant project-scoped; use local CLI with explicit cwd for structural verification.
- `tentra`: dormant project-scoped; use explicit-project local mode only when a milestone requires it.
- `context-fabric`: dormant shared route; use repo-local hook/CLI.
- `filesystem`: dormant project-scoped; never expose whole-drive roots.
- `github-mcp`: deferred; requires health gate, auth review, named tool inventory, and no wildcard exposure.
- `mcp-debugger`: disabled; operator/lease only.

## Why Not "Install Everything In Bifrost"

Bifrost can manage STDIO children and HTTP/SSE upstreams, but optimal placement depends on identity and risk:

- Global Bifrost is correct for machine-global, identity-safe tools with narrow named tools.
- Bifrost STDIO is correct for local tools that do not need an implicit current project or broad filesystem access.
- Bifrost HTTP/SSE is correct for already-running local/remote services with clear auth and lifecycle.
- Project-scoped code scanners belong in project-local/JIT mode until Bifrost can inject trustworthy project identity per call.
- Arbitrary shell, whole-drive filesystem, raw databases, raw Recall/Vault, and competing memory stores must not be global.

## Open Questions To Resolve In The Next Goal

1. Is Swarm PG on `:65432` expected to be stopped after the latest restart, or should Sally start/own it?
2. Are the four temporary codebase indexer MCPs still present in the `nfa-alerts-enterprise` project config, and did they generate useful non-secret artifacts?
3. Which exact foundational tools must be continuously active versus JIT-leased versus local explicit-cwd only?
4. Should the Bifrost hardening branch be integrated into `main` now, or should it be re-reviewed first against the current live gateway?
5. What exact health/metrics dashboard is required for always-on visibility before production projects begin?

## Ordered Completion Plan

### Phase 0 - No-Drift Baseline

- Re-read the authority chain and this handoff.
- Verify Git state in:
  - `@D:\github\agentcore-control-plane`
  - `@D:\github\agentcore-control-plane-bifrost-hardening`
  - `@D:\github\swarm-ecosystem-control`
  - `@D:\github\agentcore-context-engine`
- Preserve inherited dirty state; do not clean, reset, or stage unrelated WIP.
- Re-run live checks:
  - Cursor global MCP exactly one entry.
  - Bifrost `/health` ok.
  - authenticated MCP initialize, initialized notification, and tools/list.
  - loopback listeners for Bifrost, PG18, SwarmRecall, Meili, SwarmClaw, and Swarm PG if expected.
  - H-drive read/write canary only in approved Swarm-owned canary path.

### Phase 1 - H Drive And Swarm Health

- Let SwarmClaw/Sally own Swarm service lifecycle and native configuration.
- Verify `H:\SwarmData` is stable after restart:
  - `chkdsk H: /scan`
  - `fsutil dirty query H:`
  - readable directory inventory
  - SwarmRecall health on `:3300`
  - Meilisearch health on `:7700`
  - SwarmClaw health/UI on `:3456`
  - Swarm PG on `:65432` if current Swarm architecture expects it live
- Confirm SwarmVault workspace path and backup policy through Sally, not AgentCore.
- Do not reinstall Swarm unless current evidence proves the native H-drive install is unrecoverable or materially miswired.

### Phase 2 - Bifrost Production Hardening

- Reconcile the hardening branch/worktree into the current main only after review.
- Required hardening outcomes:
  - per-child STDIO environment isolation, with only declared env vars passed to each upstream;
  - Bifrost scheduled-task watchdog and self-recovery for externally terminated wrapper;
  - Task Scheduler Operational logging enabled for attribution;
  - `mcp-prompt-optimizer` runtime pinned to an absolute executable path, not bare `uv`;
  - logs rotated or capped;
  - direct and authenticated readiness checks use the correct MCP lifecycle;
  - all changes tested in repo first, then rolled out live through approved Bifrost ops scripts.

### Phase 3 - MCP Placement Audit And Certification

- Build a current matrix for every MCP in the registry and every direct MCP found in Cursor/Codex/Claude/Zed/Eigent/MiniMax/Mavis/etc.
- For each server, classify:
  - active global
  - dormant/JIT
  - project-local explicit-cwd
  - host-local only
  - rejected/forbidden
- For active/JIT Bifrost servers, require:
  - official source or accepted repo provenance;
  - version pin;
  - named permitted tools, no new wildcards;
  - env var names only, no secrets;
  - least-privilege profile/lease;
  - health proof;
  - rollback path;
  - metrics/logging classification.
- Do not expose Serena, Depwire, Tentra, Context Fabric, Filesystem, GitHub, or debugger globally until their project identity/security gates are satisfied.

### Phase 4 - Prompt Optimizer And Context Cost Controls

- Certify what `mcp-prompt-optimizer` actually does today:
  - callable via Bifrost;
  - no secrets;
  - no unintended writes;
  - latency and token reduction measured;
  - output quality checked against original intent.
- Record the important boundary: an MCP prompt optimizer does not automatically rewrite every IDE prompt unless the IDE/agent calls that tool or a host lifecycle hook invokes it.
- Keep provider-side context caching, local RAG/context assembly, and prompt compression as separate planes.
- Do not activate OmniRoute/Graphify/Hindsight until benchmark-gated ADR approval.

### Phase 5 - Memory And Recall Isolation

- Prove `agentcore-memory` facade remains exact 10 tools.
- Prove append, retrieve, compact, expand, and handoff through `agentcore-gateway`.
- Prove neutral SwarmRecall global/per-project pool provisioning and isolation.
- Confirm no ordinary IDE has raw SwarmRecall, SwarmVault, PostgreSQL, Meilisearch, or direct SQL credentials.
- Confirm Recall outage does not corrupt AgentCore PG18 evidence or LangGraph checkpoints.
- Confirm Meilisearch is rebuildable from Recall PG rows.

### Phase 6 - Runtime Acceptance

- LangGraph:
  - use only `@D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe`;
  - run topology, status, and a production canary through PG18 PostgresSaver;
  - prove checkpoints and evidence.
- SwarmClaw:
  - Sally owns setup, agents, tasks, sessions, recovery, and SwarmVault/Recall usage;
  - run a Swarm-owned autonomous canary;
  - prove it does not write AgentCore PG18, Bifrost, LangGraph checkpoint state, or AgentCore IDE profiles.
- Compare LangGraph vs SwarmClaw on one bounded project after both runtimes are independently healthy.

### Phase 7 - Documentation, Task List, And Restore Point

- Create or update a global task checklist/work queue so unfinished operational loops do not vanish.
- Documentation maintainer only updates current docs after evidence exists.
- Protected files require unlock, backup, edit, validation, independent review, and relock.
- Commit and push task-owned source changes.
- Create a restore point/evidence bundle after Bifrost, H-drive, Swarm, LangGraph, and MCP placement are accepted.

## Goal Mode Prompt For Next Chat

```text
GOAL MODE - FINISH AGENTCORE/SWARM MEMORY, BIFROST, MCP PLACEMENT, AND RUNTIME ACCEPTANCE

You are operating in @D:\github\agentcore-control-plane. Treat this as a production-hardening and acceptance task, not a redesign.

Read first:
@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\BLUEPRINT.md
@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md
@D:\github\agentcore-control-plane\docs\current\PC_MEMORY_CONTEXT_WIRING_2026-08-05.md
@D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md
@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json
@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json
@D:\github\agentcore-control-plane\docs\operations\DORMANT_MCP_CAPABILITY_CATALOG.md
@D:\github\agentcore-control-plane\SERENA.md
@D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_NEXT_GOAL_HANDOFF_2026-08-09.md

Current goal:
Finish the PC-wide AgentCore/Swarm memory-context/database setup and harden Bifrost so production work can start. Preserve the approved architecture:
- AgentCore owns Bifrost, the agentcore-gateway MCP front door, exact evidence/recovery, PG18, Context Engine, and LangGraph checkpoints.
- SwarmClaw/Sally owns Swarm runtime, agents, sessions, tasks, recovery, SwarmVault, and Swarm lifecycle.
- Neutral SwarmRecall is the PC-native semantic memory/context plane shared only through bounded server-side adapters.
- Ordinary IDEs use exactly one MCP entry, agentcore-gateway. No raw SwarmRecall, SwarmVault, Meilisearch, PostgreSQL, direct SQL, or duplicate memory MCP entries in ordinary IDE configs.
- LangGraph and SwarmClaw remain separate runtimes and must not write each other's state.

Start with read-only verification:
1. Verify Git state in agentcore-control-plane, agentcore-control-plane-bifrost-hardening, swarm-ecosystem-control, and agentcore-context-engine.
2. Verify Cursor global MCP has exactly one server: agentcore-gateway.
3. Verify Bifrost health, authenticated MCP lifecycle, and tools/list.
4. Verify H:\SwarmData readability and Swarm loopback services: Recall :3300, Meili :7700, SwarmClaw :3456, Swarm PG :65432 if expected by current Swarm authority.
5. Verify PG18 :55433 and LangGraph production runtime.
6. Report inherited dirty/untracked files without cleaning them.

Then execute in order:
1. H-drive and Swarm health with Sally as Swarm authority.
2. Bifrost hardening: per-child env isolation, watchdog/self-recovery, Task Scheduler attribution, prompt optimizer absolute path pinning, log policy.
3. MCP placement certification: active/global vs dormant/JIT vs project-local vs host-local vs forbidden. Do not globally expose Serena, Depwire, Tentra, Context Fabric, Filesystem, GitHub, or debugger until identity/security gates pass.
4. Prompt optimizer and context-cost measurement.
5. agentcore-memory plus neutral SwarmRecall isolation and outage/degraded-mode proof.
6. LangGraph production canary and SwarmClaw autonomous canary.
7. Documentation/task-list/restore-point closeout.

Stop gates:
- Do not mutate Swarm product source, H-drive Swarm runtime data, SwarmVault, or Swarm credentials from AgentCore.
- Do not edit protected authority files without explicit AUTH approval, rollback, validators, independent review, and relock.
- Do not add direct IDE MCP entries except short-lived project-local indexing tools explicitly approved by the operator.
- Do not expose arbitrary shell, whole-drive filesystem, raw database, raw Recall/Vault, or duplicate memory stores globally.
- Do not activate OmniRoute, Graphify, Hindsight, CrewAI, or context-cache experiments without approved ADR and benchmarks.

Deliver:
- A verified status matrix.
- Exact changes made.
- Exact validation commands/results.
- Remaining risk.
- Git commit/push result for task-owned source changes only.
```

Complexity: 9/10
Context size: 8/10

## Immediate Operator Guidance

If the operator needs to sleep before the full hardening run:

1. Keep Cursor global MCP as the single `agentcore-gateway` entry.
2. If the four codebase indexers are needed tonight, use them only in the `nfa-alerts-enterprise` project config and remove/disable them after indexing.
3. Do not add those indexers to global Cursor or permanent Bifrost tonight.
4. Do not change Swarm internals from AgentCore; ask Sally to validate Swarm health and restart SwarmClaw if needed.
5. Start the next Goal Mode run with the prompt above.
