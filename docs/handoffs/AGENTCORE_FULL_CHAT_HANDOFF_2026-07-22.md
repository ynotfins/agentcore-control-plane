---
document: AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md
project: AgentCore Global Memory, Context, Database, Governance, and IDE Enrollment
authority: current-state handoff and execution map
status: current-until-reconciled
created_at: 2026-07-22
canonical_repository: D:\github\agentcore-control-plane
operator: Tony Valentine (ynotf)
scope: non-Swarm AgentCore platform, managed IDE enrollment, LangGraph workflow, local runtime operations
supersedes: this ChatGPT conversation as the working continuity source
does_not_override:
  - PROJECT_ANCHOR.md
  - DOC_AUTHORITY.md
  - BLUEPRINT.md
---

# AgentCore Full Chat Handoff — 2026-07-22

## 0. Purpose

This handoff captures the complete operational state, decisions, artifacts, unresolved failures, acceptance gates, Milestones, and next Macro/Micro steps from the long AgentCore development chat.

Use it to start a new ChatGPT or Cursor session without reconstructing the project from chat history.

This document is a **current-state handoff**, not a new architecture authority. If it conflicts with the locked authority chain, the higher document wins and this handoff must be reconciled.

Recommended repository destination:

```text
@D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md
```

After adding it, classify it as a current handoff in:

```text
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
```

Do not edit `PROJECT_ANCHOR.md` or `BLUEPRINT.md` merely to mirror mutable status.

---

# 1. Mandatory authority and read order

Read these files in this exact order:

1. `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`
2. `@D:\github\agentcore-control-plane\DOC_AUTHORITY.md`
3. `@D:\github\agentcore-control-plane\BLUEPRINT.md`
4. `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`
5. `@D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md`
6. `@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`
7. `@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json`
8. `@D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml`
9. `@D:\github\agentcore-control-plane\docs\current\CURRENT_PROJECT_RECONSTRUCTION.md`
10. `@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md`
11. This handoff.

For project execution also read:

- `@D:\github\agentcore-control-plane\AGENTS.md`
- `@D:\github\agentcore-control-plane\MILESTONES.md`
- `@D:\github\agentcore-control-plane\docs\agent-policy\DOCUMENTATION_READ_ORDER.md`
- `@D:\github\agentcore-control-plane\docs\agent-policy\NEW_PROJECT_BOOTSTRAP.md`
- `@D:\github\agentcore-control-plane\docs\agent-policy\MILESTONE_EXECUTION_STANDARD.md`
- `@D:\github\agentcore-control-plane\docs\agent-policy\CHECKLIST_STANDARD.md`
- `@D:\github\agentcore-control-plane\docs\agent-policy\TOOL_LIFECYCLE_POLICY.md`

Machine facts are classified by:

```text
@D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md
```

Historical Swarm context is evidence only:

```text
@D:\github\agentcore-control-plane\CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md
```

Never execute its Swarm-first non-Swarm IDE baseline.

---

# 2. Locked architecture

## 2.1 Normal non-Swarm IDE route

```text
Managed IDE or agent
    -> one logical MCP entry: agentcore-gateway
    -> http://127.0.0.1:8080/mcp
    -> Bifrost
    -> approved upstream MCP servers
```

Normal IDEs must not receive the full upstream registry.

## 2.2 Canonical memory route

```text
IDE
    -> agentcore-gateway
    -> agentcore-memory
    -> PostgreSQL 18 canonical state and immutable evidence
```

Exact `agentcore-memory` surface:

1. `memory_status`
2. `startup_context`
3. `retrieve_context`
4. `append_event`
5. `propose_fact`
6. `expand_source`
7. `session_open`
8. `session_close`
9. `build_handoff`
10. `docs_search`

Project-router surface:

1. `project_list`
2. `project_activate`
3. `project_status`
4. `project_clear`

## 2.3 Canonical authority boundaries

- PostgreSQL is canonical.
- Cognee is curated semantic/relationship memory, not canonical.
- Generated Markdown projections are reproducible views, not writable authority.
- Deep Agents is a bounded worker harness inside LangGraph nodes, not memory, policy, workflow, or IDE authority.
- Bifrost is the sole normal non-Swarm MCP front door.
- SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, and ClawX remain a separate ecosystem.
- No normal IDE gets raw PostgreSQL credentials, SQL, DDL, database-admin, backup-admin, or Bifrost-admin tools.
- No `.env` files. Secrets use Windows User-scope environment variables or approved protected app storage.
- Every native IDE acceptance must be performed from the IDE itself. Raw HTTP proves the gateway only; it does not prove native client enrollment.

---

# 3. Current verified machine/runtime snapshot

## 3.1 PostgreSQL 18

Verified during the operator session:

```text
Service: AgentCore-PostgreSQL18
State: Running
Startup type: Automatic
Service identity: NT AUTHORITY\NetworkService
Binary: F:\PostgreSQL18\bin\pg_ctl.exe
Data: F:\PostgreSQL18\data
Endpoint: 127.0.0.1:55433
Database checked: agent_core
Service PID at verification: 18360
```

The previous `pg_ctl`-owned process was gracefully stopped and ownership was transferred to the Windows service. `pg_isready` returned accepting connections.

The PID is point-in-time evidence only. Do not encode it as permanent authority.

## 3.2 Bifrost

```text
Scheduled task: \AgentCore\AgentCore-Bifrost-Gateway
Launcher:
  D:\github\agentcore-control-plane\ops\bifrost\Launch-AgentCoreBifrostGateway.ps1
Runtime:
  H:\AgentRuntime\bifrost
Binary:
  H:\AgentRuntime\bifrost\bin\bifrost-http.exe
Endpoint:
  http://127.0.0.1:8080/mcp
Health:
  http://127.0.0.1:8080/health
```

Important operational observation:

- Bifrost bootstrap took about 31 seconds because unavailable upstreams exhausted retries.
- A 10-second health probe was too early.
- Use at least a 45-second startup allowance before declaring failure.
- Task Scheduler result `267009` means the scheduled task is running; it is not an application failure.
- After startup, `Test-NetConnection 127.0.0.1 -Port 8080` passed.

Latest verified surface after Obsidian disablement:

```text
Bifrost /health: 200 OK
agentcore_memory tools: exactly 10
agentcore_project_router tools: exactly 4
playwright tools: 24
obsidian_vault tools: 0
```

## 3.3 Obsidian

Obsidian is no longer needed as an AgentCore MCP upstream.

Final state:

- Obsidian application preserved.
- Vault preserved at `@D:\Obsidian\Dungeon Vault`.
- Vault remained unchanged at 211 files and approximately 147 MB.
- `obsidian_vault` removed from Bifrost runtime configuration and all four virtual-key profiles.
- Source registry entry disabled.
- Reconnect errors eliminated.
- Backup:
  `@E:\AgentCore-Backups\bifrost-obsidian-disable-20260722T222237Z`
- Commit:
  `80f3219`, pushed to `origin/main`.

Do not re-enable Obsidian as canonical or default AgentCore memory. It remains an optional human-facing Markdown application.

## 3.4 Serena

Serena still timed out during Bifrost initialization and reconnect attempts.

Current posture:

- Do not disable Serena merely because Obsidian was disabled.
- Serena is important for project-scoped semantic navigation.
- Investigate separately after higher-priority client acceptance work.
- Confirm project-router launch parameters, active project identity, startup duration, and process cleanup.
- Do not combine Serena repair with unrelated IDE configuration tasks.

## 3.5 OpenRouter provider warning

Bifrost logs showed an OpenRouter-style key being tested under an `openai` provider record. The server fell back to static model data and continued.

This is not the Bifrost listener failure, but it is configuration debt.

Required future action:

- Audit provider identity, endpoint, and key mapping.
- Do not expose or rotate the key during an unrelated task.
- Do not confuse OpenRouter API inference with OpenRouter MCP.
- OpenRouter MCP remains gateway-only and dormant unless a capability lease activates exact tools.

---

# 4. LangGraph/autonomous workflow status

## 4.1 Implemented and verified

Cursor completed the autonomous workflow work on `main`.

Point-in-time commits:

```text
a78222a  fix IDE enrollment
220cca1  feat workflow/Deep Agents/Studio
c4865b8  test Studio/recovery
```

Reported acceptance:

```text
agentcore-memory upstream: PASS
ten-tool lifecycle: PASS
autonomous workflow fixture: PASS 17/17
Deep Agents workers: PASS
deterministic gates: PASS
critic/scorer/judge: PASS
rework loop: PASS
production PostgresSaver recovery: PASS
local Agent Server: PASS
tracing disabled: PASS
project isolation: PASS
exact source recovery: PASS
```

Production operator root:

```text
@D:\github\agentcore-control-plane
```

Never launch production workflow commands from:

```text
@D:\github\deepagents
```

Deep Agents package pin:

```text
deepagents==0.6.12
```

Topology fingerprint:

```text
a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32
```

Runbooks:

- `@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_QUICKSTART.md`
- `@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_AND_STUDIO.md`

## 4.2 Still pending

### Cursor automatic fresh-chat recovery

Stage A hooks are installed:

- `sessionStart`
- `beforeSubmitPrompt`

`preToolUse` is not registered.

Final operator hard gate remains:

1. Fully close Cursor.
2. Reopen `@D:\github\agentcore-control-plane`.
3. Start a new Agent chat.
4. Send only:

```text
Continue.
```

Pass criteria:

- project/worktree recovered;
- prior `session_key` resumed;
- current task recovered;
- blocker and next action recovered;
- AgentCore source IDs included;
- prompt appended exactly once;
- no pasted recap required.

Runbook:

```text
@D:\github\agentcore-control-plane\docs\operations\AUTOMATIC_NEW_CHAT_RECOVERY.md
```

### LangSmith Studio browser validation

Local Agent Server is working on:

```text
http://127.0.0.1:2024
```

Tracing is forced off.

Pending operator steps:

1. Create/set Windows User environment variable `LANGSMITH_API_KEY`.
2. Open a new PowerShell process.
3. Launch:
   `python -m agentcore workflow studio --port 2024 --no-browser`
4. Verify:
   `http://127.0.0.1:2024/docs`
5. Open:
   `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`
6. If hosted Studio cannot reach localhost while `/docs` works, allow Local Network Access for `smith.langchain.com`.
7. Validate graph, state, thread, interrupt, and resume with the disposable fixture.

Missing `LANGSMITH_API_KEY` is a browser credential gate, not a failure of the local workflow engine.

---

# 5. MiniMax family status

## 5.1 Product identity map

### MiniMax Code

```text
Product: MiniMax Code
Version: 3.0.53.91
Executable:
  C:\Users\ynotf\AppData\Local\Programs\MiniMax Code\MiniMax Code.exe
Active root:
  C:\Users\ynotf\.minimax
MCP config:
  C:\Users\ynotf\.minimax\mcp\mcp.json
Global rules:
  C:\Users\ynotf\.minimax\AGENT.md
Persona:
  C:\Users\ynotf\.minimax\agents\mavis\agent.md
```

### `.mavis`

```text
C:\Users\ynotf\.mavis
```

is a junction to:

```text
C:\Users\ynotf\.minimax
```

It is not a separate Mavis application installation.

### MiniMax Agent Classic

```text
Product: MiniMax Agent
Marketing label: MiniMax Agent Classic v1.0.0
Version: 1.0.0.5
Executable:
  D:\Apps\MiniMaxAgent-Classic\MiniMax Agent.exe
User data:
  C:\Users\ynotf\AppData\Roaming\MiniMaxAgent-Classic
Workspace root:
  C:\Users\ynotf\.minimax-agent
Global rules:
  C:\Users\ynotf\.minimax-agent\AGENT.md
```

Classic has no local `mcp.json`. It uses the Matrix/custom MCP UI.

### `.mmx`

```text
C:\Users\ynotf\.mmx
```

contains launcher/updater metadata. It is not an IDE root. It contains secret-bearing data and must not be printed or committed.

## 5.2 Completed MiniMax source/config work

Cursor completed MiniMax Code and Classic profile/rule work.

Commit:

```text
70f4aa6
```

Reported state:

- MiniMax Code `mcp.json` contains one `agentcore-gateway`.
- `enabled: true` and `configured: true`.
- Literal `${env:BIFROST_MCP_VIRTUAL_KEY}` placeholder preserved.
- Built-ins `matrix`, `cu`, and `trash` preserved.
- MiniMax Code global rules hash matches its canonical profile.
- Classic global rules hash matches its canonical profile.
- Mavis persona rewritten to AgentCore-aligned authority.
- No secret was materialized into MiniMax Code config.

Backups:

```text
@E:\AgentCore-Backups\minimax-repair-20260722T205648Z
@E:\AgentCore-Backups\minimax-classic-repair-20260722T210236Z
```

Audits:

```text
@D:\github\agentcore-control-plane\audits\MINIMAX_CODE_REPAIR_2026-07-22.md
@D:\github\agentcore-control-plane\audits\MINIMAX_CLASSIC_REPAIR_2026-07-22.md
```

## 5.3 MiniMax Code native acceptance blocker

The native acceptance did **not** run.

Broken wrappers:

```text
@C:\Users\ynotf\.minimax\bin\mavis.cmd
@C:\Users\ynotf\.minimax\bin\minimax.cmd
```

Both point to the nonexistent target:

```text
C:\Users\ynotf\AppData\Local\Programs\MiniMax Code\resources\resources\daemon\cli.js
```

Observed installed resources:

```text
C:\Users\ynotf\AppData\Local\Programs\MiniMax Code\resources\app.asar
C:\Users\ynotf\AppData\Local\Programs\MiniMax Code\resources\app.asar.unpacked\
```

There was no verified `daemon\cli.js`.

The in-session `mavis` function surface exposed only:

- agent
- cron
- session

No MCP invocation group was present.

Correct conclusion:

```text
READY_FOR_MINIMAX_NATIVE_ACCEPTANCE
blocked by missing supported native MCP invocation route
```

Do not:

- repoint wrappers to a guessed path;
- patch/extract `app.asar` solely to force a pass;
- use raw HTTP and call it native;
- invent session/event IDs;
- claim config presence proves native invocation.

Next task must determine whether:

1. the installation is corrupted;
2. wrappers are stale from an older version;
3. the supported CLI moved;
4. MiniMax Code supports MCP discovery but not native MCP invocation.

Allowed terminal state if current product lacks the feature:

```text
MINIMAX_CODE_NATIVE_MCP_UNSUPPORTED_WITH_REASON
```

## 5.4 MiniMax Classic pending steps

Classic must be enrolled through its custom MCP/Matrix UI.

Required logical server:

```text
server_name: agentcore-gateway
base_url: http://127.0.0.1:8080/mcp
mcp_server_type: UserCustomized
Authorization: Bearer <BIFROST_MCP_VIRTUAL_KEY>
```

Do not add individual upstreams.

After enrollment, run the full native lifecycle from Classic:

1. project list;
2. project activation;
3. session open;
4. startup context;
5. append event;
6. idempotent replay;
7. paginated retrieval;
8. exact source expansion;
9. handoff;
10. close;
11. resume;
12. second-project isolation;
13. return;
14. exact ten-tool count.

Then open a new Classic chat and send only `Continue.`.

Important stop condition:

- If Matrix cloud executes the connection remotely and cannot reach `127.0.0.1`, do not expose Bifrost publicly and do not create a tunnel. Record the exact product limitation.

---

# 6. `MASTER_CONFIG_AND_PROMPT.md` status

The current master file must **not** be assumed universally safe for new IDE self-enrollment until audited.

Known stale or disproven content includes:

- old July 12 handoff pointer;
- obsolete enabled/disabled upstream counts;
- Obsidian described as default/active despite commit `80f3219`;
- generic JSON handling for MiniMax/Mavis/Open Interpreter;
- MiniMax Code and Classic not clearly separated;
- Mavis treated as a separate client in renderer tables;
- Cherry shown as fully validated despite later operator evidence that the target Agent could not create a session;
- configuration presence treated too close to native validation;
- old disconnected-upstream caveats;
- embedded prompt file references without required `@` plus complete absolute paths;
- client-specific UI-only or unsupported modes not fully represented.

Required future outcome:

Attaching:

```text
@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
```

inside one supported IDE and running its embedded prompt must:

1. identify that exact IDE and version;
2. read the matching source-controlled profile;
3. modify only that IDE;
4. install complete AgentCore global rules;
5. add exactly one logical `agentcore-gateway`;
6. preserve account/model/sandbox/theme settings;
7. distinguish direct diagnostics from native validation;
8. stop accurately at manual UI or unsupported gates;
9. never modify another IDE;
10. generate `@`-prefixed absolute paths in all Cursor instructions.

Do not run the old master file against more IDEs until the audit/rebuild task is complete.

The audit should occur after MiniMax Code product support and Open Interpreter’s real configuration mechanism are established.

---

# 7. Open Interpreter status

Operator reports:

- Open Interpreter previously showed `agentcore-gateway` connected and working.
- After reopening, it no longer looked configured.

No persistent root cause has been established.

Required dedicated Cursor task:

- identify GUI versus CLI installation;
- identify active profile and profile-selection mechanism;
- locate actual persistent MCP configuration;
- determine whether prior setup was session-only, wrong-profile, stale-path, update migration, or unsupported;
- back up active state;
- install exactly one gateway through the supported mechanism;
- install complete AgentCore global rules;
- preserve OpenRouter inference separately from OpenRouter MCP;
- ensure normal launch selects the correct profile;
- run native 14-step lifecycle and fresh-chat `Continue.` recovery;
- record `unsupported_with_reason` if the installed product lacks native MCP support.

Do not modify MiniMax, Cherry, Codex, Cursor, or Bifrost shared configuration during that task unless a direct diagnostic proves a shared defect.

---

# 8. Cherry Studio status and conflict warning

Current source docs include claims that Cherry Studio was fully repaired and lifecycle-validated.

Later direct operator evidence contradicted that claim:

- Agent record `agentcore-workspace-agent` existed.
- One gateway was mounted.
- Global Memory was reported off.
- Clicking **Create a session** did nothing.
- Diagnostic work occurred in `cherry-claw-default`, not the target Agent.
- Cherry Claw is not a substitute for AgentCore Workspace Agent.

Therefore:

```text
Cherry config records: present
Cherry target Agent session creation: unresolved/failed in later operator evidence
Native target-Agent lifecycle: not currently trusted
```

This contradiction must be reconciled in:

- `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`
- `@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md`
- Cherry audits/profile status

Do not mark Cherry live-validated until:

1. the real Agent creates a session;
2. the session appears in the session list;
3. the configured model is actually available;
4. native gateway tools appear;
5. the full memory lifecycle passes from that Agent;
6. Global Memory stays off.

## New API integration

Repository:

```text
https://github.com/QuantumNous/new-api
```

Purpose:

- New API is a model/API gateway.
- Bifrost remains the MCP/tool gateway.

Required separation:

```text
Cherry model traffic
    -> New API
    -> model providers

Cherry tool traffic
    -> agentcore-gateway
    -> Bifrost MCP upstreams
```

Do not add New API as an MCP server.

Recommended deployment remains gated on Docker storage verification.

---

# 9. Codex/ChatGPT desktop status

Codex desktop remains unresolved.

Observed prior behavior:

- Windows application would not open correctly.
- Launch could fall back to Chrome/browser.
- Codex is heavily used by the operator.

Required dedicated task:

- inventory standalone Codex, unified ChatGPT desktop, Store/MSIX packages, shortcuts, protocols, logs, and versions;
- identify stale shortcut/PWA/incomplete update;
- preserve `@C:\Users\ynotf\.codex`;
- validate `@C:\Users\ynotf\.codex\config.toml`;
- repair through the current official supported desktop path;
- preserve projects and account state;
- validate native AgentCore gateway and lifecycle;
- do not use browser/PWA as the final replacement;
- stop before deleting account/history state.

Use official current OpenAI sources during execution.

---

# 10. Docker and New API status

## 10.1 Docker location

Docker has not been conclusively proven moved off C:.

The core AgentCore platform has no Docker dependency, but the operator’s no-Docker policy is **soft**, not absolute:

- prefer native/local services when equally reliable;
- use Docker when the upstream-supported Docker deployment is materially stronger;
- keep high-volume Docker storage off C:.

Required precondition before New API:

1. inventory Docker Desktop backend;
2. identify disk-image/VHDX location;
3. inventory containers, images, volumes, Compose projects, and dependencies;
4. create verified backups;
5. use Docker Desktop’s supported disk-image relocation mechanism;
6. target an approved H: root;
7. validate containers/volumes and restart recovery;
8. do not manually move a running VHDX;
9. do not prune or delete data.

## 10.2 New API deployment target

Suggested layout:

```text
Deployment source:
  @D:\github\new-api-deployment

Upstream reference clone:
  @D:\github\vendor\model-gateways\new-api

Runtime:
  @H:\AgentRuntime\new-api

Cold backups:
  @E:\DatabaseBackups\new-api
  @G:\DatabaseBackups\new-api
```

Starting recommendation:

- Docker Compose;
- pinned New API, PostgreSQL, and Redis versions/digests;
- localhost-only bind;
- app-owned database and Redis;
- no use of `agent_core` or `cognee_core`;
- no exposed PostgreSQL/Redis host ports;
- no `.env` committed;
- Windows User variables or approved secret store;
- backup/restore acceptance;
- least-privilege Cherry token;
- preserve existing direct model providers until the operator approves consolidation.

---

# 11. Context Steward requirement

The operator considers context management a top priority.

Required future AgentCore component:

```text
Context Steward
```

It should be a bounded LangGraph/Deep Agents worker, not a free-running IDE agent and not dependent on the Codex desktop app being open.

## 11.1 Responsibilities

- verify prompt/event capture;
- verify rolling context quality;
- verify project/session/thread identity;
- detect projection lag;
- detect milestone/scope drift;
- verify drive placement and resource registration;
- detect unregistered durable paths;
- detect tool-policy violations;
- detect project/worktree boundary violations;
- measure retrieval/compaction quality;
- measure exact-source recovery;
- verify power-loss recovery;
- store findings in PostgreSQL;
- generate operator proposals instead of silently rewriting architecture.

## 11.2 Cadence

During active workflows:

- event-driven checks after append, checkpoint, test, commit, approval, handoff, and close;
- watchdog every 30 minutes.

When stable:

- deep optimization audit every 48 hours.

Do not run noisy 30-minute audits when no relevant workflow is active.

## 11.3 Authority rule

Do not automatically edit:

- `PROJECT_ANCHOR.md`
- `BLUEPRINT.md`
- locked Milestone definitions

Add a generated noncanonical projection:

```text
<project>\.agentcore\MILESTONE_DELTA.md
```

It should record verified changes since the last accepted Milestone while PostgreSQL remains canonical.

---

# 12. Locked Milestones M0–M8 and current posture

The Milestone outcomes and order remain locked by `BLUEPRINT.md`.

## M0 — Authority and execution foundation

**Outcome:** one architecture and execution policy.

Current posture:

- largely implemented;
- authority chain established;
- per-IDE profiles exist;
- historical Swarm boundary established;
- remaining alignment debt: rebuild `MASTER_CONFIG_AND_PROMPT.md` and reconcile stale client-status claims.

Immediate Macro:

1. complete client reality audits;
2. rebuild master self-enrollment package;
3. update mutable current-state docs;
4. rerun authority and prompt-format validators.

## M1 — Storage and PostgreSQL 18 safety foundation

**Outcome:** recoverable PG18 + pgvector platform beside preserved legacy cluster.

Current posture:

- PG18 canonical on `127.0.0.1:55433`;
- service ownership fixed and automatic;
- old cluster remains legacy/rollback/Swarm;
- point-in-time source docs claim backup/restore acceptance;
- current chat did not independently rerun full backup/restore/PITR validation.

Immediate Micro checks:

1. verify service after Windows reboot;
2. verify `agent_core` and `cognee_core`;
3. verify backup freshness on E: and second copy on G:;
4. verify restore-test evidence;
5. verify I: allocation-unit status before any storage mutation;
6. do not reformat H: or F:.

## M2 — Canonical identity and immutable evidence

**Outcome:** separate identities and append-only evidence.

Current posture:

- implemented according to source and lifecycle tests;
- idempotency and project isolation passed through gateway diagnostics/fixture;
- client-native acceptance remains incomplete for several IDEs.

Immediate Micro checks:

1. complete native lifecycle per client;
2. verify client/agent/session keys;
3. verify project isolation;
4. verify no direct DB credentials in IDE configs.

## M3 — Lossless context and projections

**Outcome:** compact without losing exact recovery.

Current posture:

- source reports exact expansion and model-aware recovery pass;
- durable history effectively unbounded;
- active request context remains model-limit-aware;
- Cursor automatic recovery hard gate remains pending;
- Context Steward not yet implemented.

Immediate Macro:

1. run Cursor `Continue.` hard gate;
2. add Context Steward;
3. add generated `MILESTONE_DELTA.md`;
4. test power-loss replay and projection regeneration.

## M4 — AgentCore memory gateway

**Outcome:** all non-Swarm IDEs use ten-tool memory through Bifrost.

Current posture:

- gateway live;
- exact ten tools verified;
- project router verified;
- Obsidian removed without affecting required surface;
- not all clients are native-validated.

Immediate Macro:

1. MiniMax Code support determination;
2. MiniMax Classic enrollment;
3. Open Interpreter persistence repair;
4. Cherry target-Agent repair;
5. Codex desktop repair;
6. update IDE validation matrix.

## M5 — hybrid retrieval and curated Cognee

**Outcome:** efficient retrieval without a second source of truth.

Current posture:

- source docs claim PG full-text/pgvector/Cognee architecture landed;
- current chat did not revalidate the live Cognee service or curated-promotion path.

Immediate Micro checks:

1. verify Cognee service/process;
2. verify `cognee_core`;
3. verify curated-only promotion;
4. test degraded mode with Cognee unavailable;
5. verify exact expansion remains PostgreSQL/artifact-backed.

## M6 — durable LangGraph workflow

**Outcome:** resumable autonomous development with gates, critics, judge, and leases.

Current posture:

- implemented;
- fixture E2E 17/17;
- PostgresSaver kill/resume pass;
- production CLI ready for a controlled real project;
- Studio browser UI pending operator validation.

Immediate Macro:

1. complete Studio browser gate;
2. complete Cursor recovery gate;
3. run a low-risk pilot project;
4. inspect evidence, pause/resume, rework, and restart behavior;
5. do not begin with AgentCore, EMU, or Swarm as the first unattended production run.

## M7 — engineering knowledge and templates

**Outcome:** trusted standards and repeatable foundations.

Current posture:

- Engineering Constitution and dependency catalog are referenced in source;
- this chat did not independently revalidate both Copier-template admission suites.

Immediate Micro checks:

1. verify constitution/catalog paths;
2. verify template build/test/lint/type/security evidence;
3. verify licenses/checksums/provenance;
4. verify templates are distinct from reference implementations.

## M8 — operations, recovery, performance, and cutover

**Outcome:** reliable operation without expert intervention.

Current posture:

- point-in-time M8 release acceptance exists in repo;
- PG18 service ownership now fixed;
- Bifrost scheduled task works;
- Obsidian reconnect noise removed;
- workstation-wide client cutover remains incomplete;
- Docker placement, Studio browser, client-native lifecycle, and some restart tests remain operator work.

Immediate Macro:

1. finish all client acceptance;
2. verify reboot recovery;
3. verify backup/restore freshness;
4. investigate Serena;
5. fix OpenRouter provider mapping;
6. run controlled project pilot;
7. implement Context Steward;
8. produce final mutable M8 cutover report.

---

# 13. Detailed execution roadmap

## Workstream A — preserve the current known-good runtime

### Entry gate

- PG18 service running/automatic.
- Bifrost health 200.
- ten memory tools;
- four router tools;
- 24 Playwright tools;
- zero Obsidian tools.

### Macro A1 — create current health evidence

Micro steps:

1. record current Git HEAD and status;
2. record PG18 service state;
3. wait at least 45 seconds after Bifrost start;
4. record Bifrost health;
5. record tool counts;
6. record current scheduled-task result;
7. secret-scan evidence;
8. do not store resolved keys.

### Exit gate

A current sanitized health audit exists and no runtime mutation was needed.

---

## Workstream B — MiniMax Code supported native-route investigation

### Entry gate

- MiniMax Code closed;
- backups present;
- Bifrost healthy;
- current official product documentation available;
- no raw-HTTP substitution.

### Macro B1 — identify wrapper provenance

Micro steps:

1. inspect wrapper creation/modified times;
2. inspect installer/update metadata;
3. search installed package for CLI entry points;
4. inspect source maps/package metadata;
5. compare current official Windows release;
6. identify whether wrappers are installer-owned or locally generated;
7. identify whether MCP discovery and invocation are separate capabilities.

### Macro B2 — choose a supported outcome

Allowed outcomes:

- supported repair/update/reinstall;
- regenerate official wrappers;
- quarantine stale wrappers and use another supported native route;
- record `unsupported_with_reason`.

### Macro B3 — native acceptance

Run the 14-step lifecycle only from the actual supported MiniMax Code surface.

### Exit gate

Either:

```text
MiniMax Code live_validated
```

or:

```text
MINIMAX_CODE_NATIVE_MCP_UNSUPPORTED_WITH_REASON
```

with evidence and no fabricated pass.

---

## Workstream C — MiniMax Classic enrollment and native validation

### Entry gate

- MiniMax Code test finished;
- Classic closed before configuration;
- Bifrost healthy;
- protected bearer available through Windows User environment variable.

### Macro C1 — enroll one custom MCP server

Micro steps:

1. open Classic custom MCP/Matrix UI;
2. add one `agentcore-gateway`;
3. set localhost URL;
4. materialize protected bearer only in the protected UI if required;
5. do not add individual upstreams;
6. restart Classic;
7. confirm connection.

### Macro C2 — lifecycle

Run all 14 steps, then a fresh-chat `Continue.` test.

### Exit gate

- native lifecycle pass;
- fresh-chat recovery pass;
- no public tunnel;
- no one-client-validates-another claim.

---

## Workstream D — Open Interpreter persistence repair

### Macro D1 — installation and profile audit

Micro steps:

1. locate GUI and CLI installs;
2. identify versions;
3. identify active profile and profile root;
4. identify launcher arguments;
5. identify persistent MCP mechanism;
6. identify model provider;
7. identify logs and settings DB;
8. determine why prior connection disappeared.

### Macro D2 — persistent alignment

Micro steps:

1. back up active state;
2. install one gateway;
3. install global AgentCore rules;
4. preserve OpenRouter inference;
5. separate OpenRouter inference from MCP;
6. make normal launcher select the correct profile;
7. close/reopen test.

### Macro D3 — native lifecycle

Run the 14-step lifecycle and fresh-chat recovery.

### Exit gate

`live_validated` or `unsupported_with_reason`.

---

## Workstream E — repair Cherry target Agent

### Macro E1 — session creation root cause

Micro steps:

1. back up Cherry data;
2. verify x64 app/runtime;
3. inspect Agent schema and required relationships;
4. inspect renderer/main-process errors;
5. verify provider and model availability;
6. repair through supported schema/API;
7. avoid app.asar patching;
8. prove **Create a session** works.

### Macro E2 — native lifecycle

Run from the actual AgentCore Workspace Agent, not Cherry Claw.

### Exit gate

- target Agent creates session;
- one gateway;
- Global Memory off;
- model works;
- lifecycle and isolation pass.

---

## Workstream F — repair Codex/ChatGPT desktop

### Macro F1 — application identity

Micro steps:

1. inventory standalone Codex and ChatGPT desktop;
2. inspect Store/MSIX registrations;
3. inspect shortcuts and protocols;
4. inspect crash logs;
5. identify stale PWA/browser launch;
6. preserve account/project state.

### Macro F2 — supported repair

Micro steps:

1. repair/update official package;
2. repair shortcut/protocol;
3. validate desktop opens;
4. validate Codex view;
5. validate `config.toml`;
6. validate native gateway and lifecycle.

### Exit gate

Desktop app works and native lifecycle passes without browser substitution.

---

## Workstream G — rebuild the universal master enrollment package

Start only after MiniMax Code and Open Interpreter mechanisms are known; preferably include Cherry/Codex final realities.

### Macro G1 — client matrix

Classify each client:

- direct write;
- generated prompt;
- manual import;
- UI only;
- unsupported with reason;
- unverified.

### Macro G2 — master rebuild

Micro steps:

1. remove stale counts and historical statuses;
2. remove Obsidian as default;
3. separate MiniMax Code and Classic;
4. remove separate Mavis executable assumption;
5. correct Cherry status;
6. add client-local execution scope;
7. require native validation;
8. add UI/unsupported stop states;
9. add `@` plus absolute path rule;
10. add deterministic validators;
11. secret scan;
12. commit/push.

### Exit gate

Attaching the final master file to a supported IDE safely configures only that IDE.

---

## Workstream H — Cursor and Studio operator gates

### Macro H1 — Cursor recovery

Run the real `Continue.` hard gate and record exact-once append evidence.

### Macro H2 — Studio browser

Set `LANGSMITH_API_KEY`, allow local network access if needed, inspect the fixture, and prove interrupt/resume.

### Exit gate

Both pending M6/M8 operator fields are promoted with evidence.

---

## Workstream I — Docker relocation audit and New API

### Macro I1 — Docker storage

Micro steps:

1. inventory backend and VHDX;
2. inventory all containers/volumes;
3. back up databases/critical volumes;
4. test a representative restore;
5. use supported relocation to H:;
6. validate restart;
7. retain rollback.

### Macro I2 — New API deployment

Micro steps:

1. compare supported deployment modes;
2. select Docker Compose unless native is equally strong;
3. pin versions/digests;
4. use app-owned PostgreSQL/Redis;
5. bind localhost only;
6. configure health/log retention/backups;
7. create least-privilege Cherry token;
8. add Cherry OpenAI-compatible provider;
9. validate streaming, tool calling, reasoning, accounting, restart, and restore;
10. keep model and MCP traffic separate.

### Exit gate

New API is recoverable, localhost-only, off C: for high-volume data, and Cherry uses it successfully.

---

## Workstream J — Context Steward

### Macro J1 — schema/policy

Micro steps:

1. add context-steward policy contract;
2. add audit/evidence rows;
3. add proposal mechanism;
4. add generated `MILESTONE_DELTA.md`;
5. forbid direct locked-authority edits.

### Macro J2 — scheduling

Micro steps:

1. event-driven triggers;
2. active-workflow 30-minute watchdog;
3. stable-system 48-hour audit;
4. silent healthy runs;
5. alert only on meaningful failures.

### Macro J3 — acceptance

Micro steps:

1. inject missed event;
2. inject duplicate;
3. inject wrong-drive location;
4. create stale projection;
5. simulate restart;
6. verify recovery;
7. verify project isolation;
8. verify no Swarm interaction;
9. measure resource use.

### Exit gate

Context Steward improves observability without becoming a competing authority.

---

## Workstream K — first controlled real project

Use a low- or medium-risk repository.

Do not choose:

- AgentCore itself;
- EMU;
- Swarm repositories;
- a destructive database migration;
- a project with external spending.

Macro:

1. register project;
2. create/verify `AGENTS.md` and `CLAUDE.md`;
3. run M0 bootstrap;
4. define one clear goal;
5. create isolated worktree;
6. start workflow;
7. inspect status/logs/evidence;
8. exercise pause/resume;
9. simulate process kill/resume;
10. inspect final diff and evidence;
11. accept only after deterministic tests and review;
12. record pilot findings.

---

# 14. Artifact inventory

## 14.1 Root authority/source files

```text
@D:\github\agentcore-control-plane\AGENTS.md
@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\BLUEPRINT.md
@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md
@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
@D:\github\agentcore-control-plane\MILESTONES.md
@D:\github\agentcore-control-plane\DEPWIRE.md
```

Historical only:

```text
@D:\github\agentcore-control-plane\CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md
```

## 14.2 Workflow and recovery

```text
@D:\github\agentcore-control-plane\docs\operations\AUTOMATIC_NEW_CHAT_RECOVERY.md
@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_QUICKSTART.md
@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_AND_STUDIO.md
@D:\github\agentcore-control-plane\audits\LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json
@D:\github\agentcore-control-plane\audits\LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md
@D:\github\agentcore-control-plane\audits\MEMORY_GATEWAY_HEALTH_2026-07-22.md
@D:\github\agentcore-control-plane\audits\M6\fixture-e2e-summary.json
```

## 14.3 MiniMax

```text
@D:\github\agentcore-control-plane\audits\MINIMAX_CODE_REPAIR_2026-07-22.md
@D:\github\agentcore-control-plane\audits\MINIMAX_CLASSIC_REPAIR_2026-07-22.md
@D:\github\agentcore-control-plane\ide-profiles\minimax
@D:\github\agentcore-control-plane\ide-profiles\minimax-classic
@C:\Users\ynotf\.cursor\plans\minimax_code_repair_validation_ae94cbc5.plan.md
@C:\Users\ynotf\.cursor\plans\minimax_agentcore_repair_f2761413.plan.md
```

## 14.4 Bifrost/Obsidian

```text
@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json
@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json
@D:\github\agentcore-control-plane\ops\bifrost\Launch-AgentCoreBifrostGateway.ps1
@H:\AgentRuntime\bifrost\config.json
@H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log
@H:\AgentRuntime\bifrost\logs\bifrost-gateway.stderr.log
@E:\AgentCore-Backups\bifrost-obsidian-disable-20260722T222237Z
@D:\Obsidian\Dungeon Vault
```

## 14.5 Backups

```text
@E:\AgentCore-Backups\minimax-repair-20260722T205648Z
@E:\AgentCore-Backups\minimax-classic-repair-20260722T210236Z
@E:\AgentCore-Backups\bifrost-obsidian-disable-20260722T222237Z
@E:\AgentCore-Backups\cursor-hook-lockout-20260720-223737
```

Treat all marked backups as secret-bearing.

## 14.6 Point-in-time commits

```text
a78222a  IDE enrollment repair
220cca1  autonomous workflow/Deep Agents/Studio
c4865b8  Studio/recovery tests
70f4aa6  MiniMax Code and Classic profile/repair work
80f3219  Obsidian upstream disablement
```

Always verify current HEAD before acting:

```powershell
Set-Location "D:\github\agentcore-control-plane"
git status --short
git log -1 --oneline
```

Do not assume these are still HEAD.

---

# 15. Known contradiction and drift register

| ID | Contradiction/risk | Required treatment |
|---|---|---|
| DRIFT-01 | Source docs claim Cherry live validation, later operator evidence shows target session creation failure | Reconcile mutable docs/audits; do not edit locked architecture |
| DRIFT-02 | Master file says Obsidian default active; runtime/source registry now disabled | Rebuild master; preserve vault |
| DRIFT-03 | Master file treats MiniMax/Mavis generically | Separate Code, Classic, and `.mavis` junction |
| DRIFT-04 | MiniMax Code config exists but native MCP call path is absent/broken | Determine support; do not accept raw HTTP |
| DRIFT-05 | Bifrost starts slowly due failed upstream retries | Use >=45-second startup gate; investigate Serena |
| DRIFT-06 | OpenRouter-style key configured under OpenAI provider mapping | Isolate and repair in dedicated provider task |
| DRIFT-07 | `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` contains incompatible Swarm-first rules | Historical evidence only |
| DRIFT-08 | Point-in-time M8 release acceptance may be mistaken for full workstation client cutover | Track per-client native acceptance separately |
| DRIFT-09 | Docker location remains unverified | Audit before New API deployment |
| DRIFT-10 | AgentCore memory should eliminate handoffs, but client recovery gates are not all passed | Keep this handoff until automatic recovery is proven |
| DRIFT-11 | 1M model context may be treated as durable memory | Active context is bounded; PostgreSQL durable history is effectively unbounded |
| DRIFT-12 | Agents may try to auto-edit BLUEPRINT from runtime findings | Use proposals and generated MILESTONE_DELTA, not direct locked-authority edits |

---

# 16. Cost-controlled Cursor model policy

The operator incurred more than $100 in Cursor usage in one day.

Working policy from this chat:

```text
Routine coding/repair:
  Kimi K2.7 Code

Very large repository/authority scan that truly needs near-1M active context:
  Gemini 3.5 Flash

High-risk architecture or independent final review:
  Gemini 3.1 Pro

Avoid as default until tool-call reliability is proven:
  GLM 5.2
```

Use Fable/maximum context only when the task genuinely requires full-repository architectural synthesis.

Recommended workflow:

1. one bounded task per new chat;
2. Plan mode with large context only when needed;
3. review the plan;
4. switch to a cheaper capable coding model for deterministic execution;
5. return to a stronger model only for contradictions, architecture changes, security, migrations, or failed debugging;
6. use AgentCore recovery rather than carrying enormous chat histories;
7. monitor usage before allowing another long autonomous run.

Model names, prices, and availability are time-sensitive. Verify current Cursor UI/provider pricing before relying on this ranking.

---

# 17. Non-negotiable operating rules

1. Every Cursor file/folder read instruction uses `@` plus the full absolute Windows path.
2. C-drive user paths include `@C:\Users\ynotf\...`.
3. No shortened `docs\...` or `C:\Users\...\` path forms in Cursor prompts.
4. Every completed task requiring more Cursor work ends with `CURSOR CONTINUATION PROMPT`.
5. One logical `agentcore-gateway` per non-Swarm IDE.
6. No full upstream registry pasted into IDEs.
7. No raw SQL or database credentials in IDE configs.
8. No `.env` files.
9. No secrets printed or committed.
10. Back up live app state before edits.
11. Native client validation must be native.
12. Configuration presence is not native validation.
13. Do not use one client to validate another.
14. Do not silently downgrade required Bifrost/Arabold/Depwire/architecture checks.
15. Do not edit generated `.agentcore` projections directly.
16. Do not edit `PROJECT_ANCHOR.md` or `BLUEPRINT.md` without explicit operator approval.
17. Do not combine Swarm with non-Swarm AgentCore.
18. Keep inherited WIP unstaged.
19. Validate, secret-scan, stage intended files only, commit, and push after each completed task.
20. Do not pull/fetch/merge/rebase unless explicitly requested.

---

# 18. New-chat bootstrap prompt

Paste this into the next ChatGPT project chat after adding the handoff and authority files:

```text
Continue the AgentCore project from the attached source files.

Read the authority chain first:

@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\BLUEPRINT.md
@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md
@D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md

Treat the handoff as mutable current-state evidence. It does not override the locked authority chain.

Immediate priorities:

1. Verify current Git HEAD/status, PG18 service health, Bifrost health, and the exact 10/4/24/0 tool baseline.
2. Finish MiniMax Code supported native MCP-route investigation without raw-HTTP substitution.
3. Complete MiniMax Classic custom-MCP enrollment and native lifecycle.
4. Repair and native-validate Open Interpreter persistence.
5. Run the Cursor fresh-chat Continue. hard gate.
6. Complete LangSmith Studio browser validation.
7. Rebuild MASTER_CONFIG_AND_PROMPT.md only after current client mechanisms are known.
8. Keep Cherry, Codex, Docker/New API, Context Steward, and the first controlled LangGraph project as separate bounded workstreams.

Do not ask me to repeat project history before reading the handoff and using AgentCore memory where available.
```

---

# 19. Completion definition for this handoff

This handoff can be retired when all of the following are true:

- Cursor `Continue.` recovery passes.
- MiniMax Code is native-validated or accurately marked unsupported.
- MiniMax Classic is native-validated or accurately marked unsupported.
- Open Interpreter is persistent and native-validated or accurately marked unsupported.
- Cherry target-Agent session and lifecycle are reconciled.
- Codex desktop is repaired and validated.
- `MASTER_CONFIG_AND_PROMPT.md` is rebuilt and deterministically validated.
- LangSmith Studio browser acceptance passes.
- Docker storage location is known before New API deployment.
- Context Steward is implemented and restart-tested.
- A controlled real LangGraph project completes successfully.
- Current-state docs and IDE profiles match live evidence.
- AgentCore automatic recovery makes manual chat handoffs unnecessary for ordinary continuation.
