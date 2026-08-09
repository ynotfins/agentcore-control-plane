# Next Goal Execution Plan - AgentCore, Bifrost, Swarm Health, MCP Placement

**Created:** 2026-08-09
**Companion handoff:** `@D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_NEXT_GOAL_HANDOFF_2026-08-09.md`
**Authority chain:** `PROJECT_ANCHOR.md` -> `DOC_AUTHORITY.md` -> `BLUEPRINT.md` -> `CONTEXT_BLOCK.md` -> `docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md`
**Scope:** AgentCore production hardening, Swarm health coordination through Sally, MCP placement certification, and runtime acceptance.

## Outcome

Bring the workstation to a production-ready operating baseline:

- `agentcore-gateway` remains the sole ordinary IDE MCP entry.
- Bifrost is reliable, recoverable, least-privilege, and observable.
- SwarmClaw/Sally is back online and owns Swarm runtime health.
- Neutral SwarmRecall is validated as the PC-native semantic memory/context plane through bounded adapters.
- AgentCore PG18 remains exact evidence, recovery, policy, and LangGraph checkpoint authority.
- LangGraph and SwarmClaw runtimes are independently healthy and ready for comparison on a real project.
- Temporary project-level MCP indexers are either removed after use or formally classified before any promotion.

## Non-Negotiable Boundaries

- Do not replace `agentcore-memory`; it is the governed AgentCore memory facade behind Bifrost.
- Do not expose raw SwarmRecall, SwarmVault, Meilisearch, PostgreSQL, or direct SQL credentials to ordinary IDEs.
- Do not make SwarmClaw a LangGraph runtime or LangGraph a SwarmClaw runtime.
- Do not mutate Swarm internals from AgentCore. Sally/SwarmClaw owns Swarm service lifecycle and SwarmVault/Recall operation.
- Do not promote temporary codebase indexers into global Cursor or permanent Bifrost without official-source, pin, identity, storage, security, and rollback review.
- Do not activate OmniRoute, Graphify, Hindsight, CrewAI, or context-cache experiments during this goal.

## Phase 0 - Baseline And Drift Lock

**Purpose:** Prove the current state before changing anything.

Checks:

1. Read the authority chain and the companion handoff.
2. Verify Git status in:
   - `@D:\github\agentcore-control-plane`
   - `@D:\github\agentcore-control-plane-bifrost-hardening`
   - `@D:\github\swarm-ecosystem-control`
   - `@D:\github\agentcore-context-engine`
3. Preserve inherited dirty and untracked files. Do not clean or stage unrelated work.
4. Verify Cursor global MCP:
   - exactly one server;
   - server name `agentcore-gateway`;
   - endpoint `http://127.0.0.1:8080/mcp`;
   - auth through `${env:BIFROST_MCP_VIRTUAL_KEY}`;
   - no direct project indexers, command-runner, memory-bank, raw Recall, or raw database entries.
5. Verify Bifrost:
   - process path;
   - scheduled task state;
   - `/health`;
   - authenticated MCP initialize;
   - initialized notification where applicable;
   - `tools/list`;
   - expected ordinary profile surface.
6. Verify loopback listeners:
   - Bifrost `:8080`;
   - PG18 `:55433`;
   - SwarmRecall `:3300`;
   - Meilisearch `:7700`;
   - SwarmClaw `:3456`;
   - Swarm PG `:65432` if expected by current Swarm authority.

Exit evidence:

- current status matrix;
- inherited-dirty inventory;
- live service/listener evidence;
- no mutation yet except writing evidence if approved.

## Phase 1 - Sally And Swarm Health

**Purpose:** Get Sally/SwarmClaw back to a reliable starting point without AgentCore taking Swarm ownership.

Steps:

1. Give Sally the Swarm prompt from the current operator response.
2. Sally verifies, not redesigns:
   - SwarmClaw UI/runtime;
   - SwarmRecall health;
   - Meilisearch health;
   - SwarmVault workspace and corpus;
   - Swarm PG if required;
   - H-drive dirty bit and filesystem health;
   - backup path and last successful backup;
   - agent roster and disabled duplicate extensions.
3. Sally reports:
   - which services are running;
   - which are intentionally stopped;
   - which need restart;
   - which settings must be changed manually in the UI;
   - exact residuals before autonomous task execution.
4. AgentCore records only boundary-level evidence. Do not write Swarm runtime state from AgentCore.

Exit evidence:

- Sally final report;
- H-drive health proof;
- SwarmRecall/Meili/Vault/Claw status;
- explicit status of `:65432`.

## Phase 2 - Temporary Codebase Indexer Handling

**Purpose:** Allow useful one-time project indexing without polluting global MCP or memory authority.

Policy:

- Project-level temporary MCP indexers are allowed only for the active project and only until indexing is done.
- Generated artifacts are data, not authority.
- Keep only non-secret, useful artifacts. Remove project-level MCP entries afterward unless formally admitted.

Specific handling:

- `mcp-codebase-search`: currently failed under Node 24 because LanceDB native addon is incompatible. Do not patch the app repo. Use a Node 22 LTS sandbox if the tool is still needed.
- `code-search`: acceptable if it is workspace-bounded with `--allowed-workspace ${workspaceFolder}`.
- `codebase-memory-mcp`: acceptable only as temporary project-local memory/index output, not as a canonical memory store.
- `claude-context`: acceptable only if Milvus/OpenAI env vars are intentionally configured and its storage location is known and accepted.

Exit evidence:

- list of temporary MCPs present/removed;
- generated artifact locations;
- secret scan of kept artifacts;
- note if a tool failed and was skipped.

## Phase 3 - Bifrost Production Hardening

**Purpose:** Remove known operational fragility before production projects start.

Required changes:

1. Integrate or re-review the hardening worktree:
   - `@D:\github\agentcore-control-plane-bifrost-hardening`
   - branch `codex/bifrost-production-hardening`
2. Per-child STDIO environment isolation:
   - Bifrost itself may receive required Windows User env vars.
   - Each upstream child receives only minimal OS vars plus declared env names.
   - `agentcore-memory` gets the complete declared set it actually needs, including neutral Recall and optional Cognee controls.
3. Watchdog/self-recovery:
   - detect externally terminated gateway wrapper;
   - restart dead/Ready scheduled task;
   - debounce unhealthy-running recycle;
   - honor maintenance marker;
   - enable Task Scheduler Operational logging for attribution.
4. Prompt optimizer path pin:
   - replace bare `uv` with a validated absolute runtime path or repo wrapper.
5. Log policy:
   - cap or rotate oversized Bifrost stdout/stderr logs;
   - keep enough evidence for diagnosis without unbounded growth.
6. Readiness:
   - use correct MCP lifecycle for readiness checks;
   - avoid claiming readiness from initialize-only stubs.

Exit evidence:

- repo tests;
- Bifrost contract validators;
- live rollout evidence;
- gateway restart proof;
- failure/recovery proof;
- rollback instructions.

## Phase 4 - MCP Placement Certification

**Purpose:** Decide what belongs in Bifrost, what is JIT/local, and what is rejected.

Classify every discovered MCP into one of:

- active global;
- active global but Code Mode hidden;
- dormant/JIT;
- project-local explicit-cwd;
- host-local only;
- operator-only;
- forbidden/rejected.

Required foundational decisions:

- `sequential-thinking`: global active, read-only, one-tool planning surface.
- `arabold-docs`: global active, official-doc cache route, Code Mode acceptable.
- `agentcore-memory`: global active ten-tool facade.
- `mcp-prompt-optimizer`: global active only after path pin and behavior metrics.
- `serena`: not shared-global until trusted per-session project identity exists; use host-local/project-owned process.
- `depwire`: local explicit-cwd unless project identity gate is solved.
- `tentra`: local explicit-project only.
- `context-fabric`: repo-local CLI/hook only.
- `filesystem`: dormant/project-scoped only; no whole-drive roots.
- `github-mcp`: deferred until auth, health, named tools, and write boundary are proven.
- `mcp-debugger`: disabled/operator lease only.

Exit evidence:

- MCP placement matrix;
- active gateway tool inventory;
- no direct duplicate IDE entries;
- rejected/direct-risk list;
- fallbacks and alerting requirements.

## Phase 5 - Memory, Context, And Semantic Isolation

**Purpose:** Prove the exact-evidence plane and semantic plane are working together without contamination.

Checks:

1. `agentcore-memory` still exposes exactly:
   - `memory_status`
   - `startup_context`
   - `retrieve_context`
   - `append_event`
   - `propose_fact`
   - `expand_source`
   - `session_open`
   - `session_close`
   - `build_handoff`
   - `docs_search`
2. AgentCore memory cycle:
   - session open;
   - append;
   - retrieve;
   - compact or bounded retrieval;
   - expand exact source;
   - build handoff.
3. Neutral SwarmRecall:
   - global pool and project pool provisioning;
   - project isolation;
   - idempotent writes;
   - query/read proof;
   - degraded behavior when Recall or Meili is down.
4. Confirm no ordinary IDE has raw memory/database credentials.

Exit evidence:

- successful memory lifecycle;
- Recall pool isolation proof;
- outage/degraded-mode proof;
- no raw credential route proof.

## Phase 6 - Runtime Acceptance

**Purpose:** Prove both autonomous runtimes are ready to start real work.

LangGraph acceptance:

- Use `@D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe`.
- Run topology from `@D:\github\agentcore-control-plane\scripts`.
- Run one production canary through PG18 PostgresSaver.
- Verify checkpoints, evidence, critic/scorer/judge result, and no Swarm writes.

SwarmClaw acceptance:

- Sally runs the Swarm-owned canary.
- Verify agent roster, task delegation, memory/Recall usage, Vault/RAG use if expected, and recovery behavior.
- Prove no AgentCore PG18, Bifrost, LangGraph checkpoint, or IDE profile writes.

Exit evidence:

- LangGraph canary report;
- SwarmClaw canary report;
- cross-contamination negative checks;
- readiness decision for first real project.

## Phase 7 - Metrics, Alerts, Task List, And Restore Point

**Purpose:** Make the system maintainable after this run.

Required outcomes:

- Global task checklist/work queue for unfinished loops.
- Health checks and alerts for:
  - Bifrost;
  - `agentcore-memory`;
  - PG18;
  - SwarmRecall;
  - Meilisearch;
  - SwarmClaw;
  - foundational MCP availability.
- Prompt optimizer/context-cost metrics:
  - token reduction;
  - latency;
  - quality/fidelity;
  - failure rate.
- Restore point:
  - source commits pushed;
  - runtime evidence captured;
  - backup/restore paths documented;
  - residuals explicitly accepted or assigned.

Exit evidence:

- final status matrix;
- restore point report;
- committed and pushed task-owned source changes;
- exact remaining risks.

## Sally Prompt

```text
SALLY / SWARMCLAW RECOVERY AND READINESS - SWARM AUTHORITY ONLY

You are Sally, the SwarmClaw orchestrator. Your scope is the Swarm ecosystem only. Do not mutate AgentCore, Bifrost, AgentCore PG18, LangGraph checkpoints, AgentCore IDE profiles, or AgentCore source repositories.

Goal:
Bring the Swarm runtime back to a verified ready state so SwarmClaw can run autonomous development work using Swarm's native best-practice setup.

Authority model:
- SwarmClaw/Sally owns Swarm runtime orchestration, agents, sessions, tasks, recovery, lifecycle, and Swarm-owned settings.
- SwarmRecall is the neutral PC-native semantic memory/context service. Use it through Swarm's supported bounded adapter only.
- SwarmVault owns Swarm document/wiki/graph/RAG corpus.
- AgentCore owns Bifrost, agentcore-gateway, AgentCore PG18, Context Engine, exact IDE evidence/recovery, and LangGraph checkpoints.
- Do not use AgentCore PG18, Bifrost, LangGraph checkpoints, AgentCore IDE configs, or AgentCore memory as Swarm runtime authority.
- Do not write to C: or unrelated project folders. Only access Swarm-owned roots and explicit evidence/read-only machine checks needed for this validation.

Start read-only:
1. Verify the current SwarmClaw process/UI state.
2. Verify H:\SwarmData is readable and contains expected Swarm roots.
3. Verify SwarmRecall health on 127.0.0.1:3300.
4. Verify Meilisearch health on 127.0.0.1:7700.
5. Verify SwarmClaw health/UI on 127.0.0.1:3456.
6. Verify whether Swarm PG on 127.0.0.1:65432 is expected and, if expected, whether it is listening and healthy.
7. Verify SwarmVault workspace path, corpus/search/context-pack status, and backup policy.
8. Verify Sally's agent roster, disabled duplicate agents/extensions, wake/session lifecycle, provider model, memory settings, reflection settings, and backup settings.
9. Report any required UI/manual setting that cannot be changed safely by automation.

Then, if safe and inside Swarm authority:
1. Restart only Swarm-owned services that are expected to be running but are stopped.
2. Run a Swarm-owned memory canary: write/read/search through SwarmRecall with project/session identity and no AgentCore writes.
3. Run a SwarmVault canary: search and context-pack proof.
4. Run one tiny autonomous SwarmClaw canary task through the approved agent team with evidence gates.
5. Confirm no writes occurred to AgentCore PG18, Bifrost, LangGraph checkpoints, or AgentCore IDE profiles.

Deliver:
- Service status table.
- Exact health results.
- Agent/team readiness table.
- Memory/Recall/Vault canary evidence.
- SwarmClaw autonomous canary result.
- Remaining blockers.
- Whether a new Sally chat is required.

Stop gates:
- Do not reinstall Swarm unless current evidence proves the native H:\SwarmData install is unrecoverable or materially miswired.
- Do not change AgentCore files or configs.
- Do not expose or print secret values.
- Do not edit protected docs or unrelated repos.
- Do not broaden listeners beyond loopback without explicit operator approval.
```

Complexity: 7/10
Context size: 6/10

## Cursor Prompt For The LanceDB MCP Failure

Use this only if the operator wants Cursor to continue the temporary project-local indexing attempt.

```text
TEMPORARY PROJECT-LOCAL MCP INDEXER TRIAGE - DO NOT TOUCH GLOBAL MCP OR BIFROST

The temporary project-level MCP `mcp-codebase-search` failed with:
LanceDB native crash: lancedb.win32-x64-msvc.node is not a valid Win32 application (Node 24 / native addon mismatch).

Scope:
- Work only inside the current project and its project-level MCP config.
- Do not edit Cursor global MCP.
- Do not edit Bifrost.
- Do not edit AgentCore authority docs.
- Do not patch vendor package source unless there is no supported runtime workaround.

Task:
1. Confirm the active Node runtime used by Cursor for this project MCP.
2. Confirm the package's supported Node versions and LanceDB native addon compatibility from official/package metadata.
3. Try the safest runtime workaround first: run this temporary MCP under Node 22 LTS, isolated to the project-level command path.
4. If Node 22 works, document the exact project-level MCP command and mark it temporary.
5. If Node 22 does not work, disable/remove `mcp-codebase-search` and continue with the other project-local indexers that do not crash.
6. Preserve generated artifacts only if non-secret and useful.

Deliver:
- root cause;
- exact Node version(s) tested;
- whether Node 22 fixed it;
- final project-level MCP config;
- generated artifact paths;
- confirmation no global Cursor MCP or Bifrost config changed.
```

Complexity: 4/10
Context size: 3/10
