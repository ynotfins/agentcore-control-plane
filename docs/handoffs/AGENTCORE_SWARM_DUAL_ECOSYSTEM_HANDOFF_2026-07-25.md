---
document: AGENTCORE_SWARM_DUAL_ECOSYSTEM_HANDOFF_2026-07-25.md
purpose: New-ChatGPT continuity handoff for AgentCore and the separate local Swarm ecosystem
status: current-until-reconciled
created_at: 2026-07-25
operator: Tony Valentine (ynotf)
machine: CHAOSCENTRAL
scope:
  - non-Swarm AgentCore platform
  - Cursor/IDE alignment and Bifrost closeout
  - autonomous LangGraph developer workflow
  - separate SwarmClaw/SwarmRecall/SwarmVault local ecosystem
not_architecture_authority: true
---

# AgentCore + Local Swarm Dual-Ecosystem Handoff — 2026-07-25

## 0. Purpose and authority

This handoff lets a new ChatGPT project chat resume the current work without reconstructing the million-character conversation.

It records:

- the verified AgentCore architecture and recent implementation state;
- the current Bifrost/ChatGPT tunnel issue that still needs remediation;
- the lean Cursor context and Stage B integrity harness;
- the durable LangGraph autonomous-development workflow;
- the separate SwarmClaw/SwarmRecall/SwarmVault ecosystem;
- the correct sequence for completing both ecosystems without cross-contamination;
- the required operating relationship between ChatGPT, Cursor, Codex, and the autonomous workflow.

This document is **current-state evidence and an execution map**. It does not override either ecosystem's locked authority.

For AgentCore, the authority chain is:

1. `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`
2. `@D:\github\agentcore-control-plane\DOC_AUTHORITY.md`
3. `@D:\github\agentcore-control-plane\BLUEPRINT.md`
4. `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`
5. `@D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md`
6. current contracts, runbooks, audits, projections, and handoffs
7. `@D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md` for classified machine facts

For the new Swarm integration-control repository, the future authority chain is expected to be:

1. `@D:\github\swarm-ecosystem-control\SWARM_PROJECT_ANCHOR.md`
2. `@D:\github\swarm-ecosystem-control\SWARM_DOC_AUTHORITY.md`
3. `@D:\github\swarm-ecosystem-control\SWARM_BLUEPRINT.md`
4. `@D:\github\swarm-ecosystem-control\SWARM_CONTEXT_BLOCK.md`
5. `@D:\github\swarm-ecosystem-control\SWARM_MILESTONES.md`
6. each upstream repository's own current source, docs, tests, and release evidence

Until the Swarm control documents are created and accepted, the current Cursor Swarm plan is a proposal, not authority.

---

# 1. Instructions for the new ChatGPT chat

## 1.1 First action: connect to AgentCore memory when available

A custom ChatGPT app named `agentcore-gateway` is connected through OpenAI Secure MCP Tunnel. In a new ordinary ChatGPT project chat, explicitly select or mention:

```text
@agentcore-gateway
```

Do not assume the app is available merely because it exists at account level. Prove the current chat can call it.

Start read-only:

1. `memory_status`
2. `project_list`
3. `project_status` for `agentcore-control-plane`
4. `startup_context` or bounded context retrieval for the active task
5. `retrieve_context` and `expand_source` when exact evidence matters

Do not initially call `project_clear`, filesystem writes, shell tools, raw database tools, Bifrost administration, Firebase, Sheets, or Swarm tools.

The dedicated Windows User environment variable is:

```text
BIFROST_MCP_VK_CHATGPT
```

The operator has confirmed it now exists and validates as present/format-correct. Never print or request its value.

## 1.2 Required diagnostic questions before creating a Cursor plan or prompt

The new ChatGPT must not immediately emit a large Cursor prompt from this handoff alone. At the start of a new phase or scope shift, ask 3–7 implementation-changing questions, then use AgentCore memory and live repository evidence before planning.

Minimum questions for the next turn:

1. Which workstream is active now: Bifrost remediation, AgentCore hardening/IDE alignment, or Swarm S0/S1?
2. Which repository/workspace is currently open in Cursor?
3. What is the current branch, HEAD, and dirty-worktree state?
4. Has the targeted Bifrost independent-verification remediation already run?
5. Are any other write-capable agents currently modifying the same repository or live configuration?
6. Does the operator want a read-only Plan pass or immediate execution of an already accepted plan?
7. Are there any new screenshots, audit reports, or runtime failures newer than this handoff?

For an ongoing task, ask 1–3 specific questions on each operator response whenever an answer could alter written code, runtime state, or architecture.

## 1.3 Division of responsibility

### ChatGPT

ChatGPT is the human-in-the-middle coach, workflow navigator, authority/drift reviewer, and prompt architect. It should:

- reconstruct current state from AgentCore memory and exact sources;
- expose missing decisions and contradictions;
- protect locked architecture and ecosystem boundaries;
- produce bounded production-grade prompts for Cursor/Codex;
- review Cursor outputs for drift, missing evidence, unsafe assumptions, and incomplete gates;
- avoid micromanaging implementation details that Cursor can decide from full-repo evidence.

### Cursor

Cursor is the primary repo-aware implementer. Every Cursor prompt must:

- state the macro outcome and locked constraints;
- use `@` plus full absolute Windows paths;
- tell Cursor to inspect the entire relevant codebase and current runtime before choosing implementation details;
- authorize Cursor to add, remove, split, combine, or reorder Macro/Micro steps inside the fixed Milestone outcome;
- require current official docs through Arabold before dependency/API work;
- require Serena/Depwire/Sequential Thinking/Playwright when the task class requires them;
- require Cursor to stop and ask the operator if an assumption would materially change written code, runtime state, locked architecture, or an irreversible boundary;
- finish with deterministic tests, evidence, rollback, commit/push, and a `CURSOR CONTINUATION PROMPT` when more work remains.

### Codex

Codex is preferred as an independent verifier, code reviewer, or bounded secondary implementation agent when its desktop/CLI route is healthy. It should not validate its own implementation in the same context. It can also serve as a supervisory decision proxy in the LangGraph workflow, subject to the approval matrix below.

---

# 2. Stable machine and storage facts

Machine:

```text
Host: CHAOSCENTRAL
OS: Windows 11 Pro 10.0.26200 x64
CPU: Intel Core i9-14900KF, 24 cores / 32 threads
RAM: 128 GB DDR5
GPU: NVIDIA RTX 4070 SUPER, 12 GB VRAM
```

Drive roles:

```text
C: Windows, applications, user profile, IDE-owned live config
D: source repositories, worktrees, builds, tests
E: cold evidence, docs, archives, primary backups, WAL archive
F: PostgreSQL/hot indexes/canonical databases
G: second backup copy
H: Bifrost and AgentRuntime, hot artifacts, caches, models, logs
I: disposable staging and caches only
J: portable transfer only
```

No `.env` files are permitted in AgentCore. Secrets use Windows User-scope environment variables or approved protected app storage.

---

# 3. The two ecosystems

## 3.1 Ecosystem A — AgentCore non-Swarm platform

AgentCore is the global memory, context, database, governance, IDE-tooling, and autonomous-development platform for non-Swarm work.

Locked route:

```text
Cursor / Codex / Claude / MiniMax / Open Interpreter / Cherry / LangGraph
        |
        v
one logical MCP entry: agentcore-gateway
http://127.0.0.1:8080/mcp
        |
        v
Bifrost native gateway
        |
        +-- agentcore-memory
        +-- agentcore-project-router
        +-- approved task-class MCP upstreams
        |
        v
PostgreSQL 18 at 127.0.0.1:55433
agent_core + cognee_core
```

Canonical rules:

- PostgreSQL 18 is canonical.
- `agentcore-memory` is the stable memory identity.
- Bifrost is the one normal non-Swarm MCP front door.
- Generated Markdown is projection, not writable authority.
- Cognee contains curated promoted knowledge only; it is not canonical.
- Deep Agents is a bounded worker harness inside LangGraph nodes only.
- Normal agents receive no raw SQL, DDL, DB-admin, backup-admin, or Bifrost-admin tools.
- Durable history is effectively unbounded; one model request remains bounded by the selected context profile.
- Compaction never deletes or replaces accepted originals.

Exact AgentCore memory surface:

```text
memory_status
startup_context
retrieve_context
append_event
propose_fact
expand_source
session_open
session_close
build_handoff
docs_search
```

Exact project-router surface:

```text
project_list
project_activate
project_status
project_clear
```

Generated projections:

```text
@C:\Users\ynotf\.agentcore\GLOBAL_STATE.md
<project>\.agentcore\STATE.md
<project>\.agentcore\DECISIONS.md
<project>\.agentcore\CONTEXT_INDEX.md
```

Agents never edit these directly.

## 3.2 Ecosystem B — local Swarm ecosystem

Swarm is an independent runtime/data ecosystem composed of:

```text
SwarmClaw   — local agent runtime, orchestration, tasks, schedules, approvals, evals
SwarmRecall — local long-term agent memory, pools, learnings, semantic retrieval
SwarmVault  — local source corpus, wiki, knowledge graph, RAG, context packs
```

Managed source repositories:

```text
@D:\github\vendor\swarm\swarmclaw
@D:\github\vendor\swarm\swarmrecall
@D:\github\vendor\swarm\swarmvault
```

Integration-control repository/workspace:

```text
@D:\github\swarm-ecosystem-control
@D:\github\swarm-ecosystem-control\swarm-ecosystem.code-workspace
```

Deferred and dormant:

```text
@D:\github\vendor\swarm\swarmdock
@D:\github\vendor\swarm\swarmrelay
@D:\github\vendor\swarm\swarmfeed
```

Reference-only unless dependency tracing proves otherwise:

```text
@D:\github\vendor\memory\lossless-claw
@D:\github\vendor\memory\lossless-memory4agent
```

Swarm runtime must remain fully local and independent of AgentCore at runtime.

## 3.3 Hard no-cross-contamination boundary

Swarm runtime processes and Swarm agents must not consume:

```text
agentcore-gateway
BIFROST_MCP_VIRTUAL_KEY or AgentCore virtual keys
agentcore-memory or project-router
PostgreSQL 18 at 127.0.0.1:55433
agent_core or cognee_core
AgentCore STATE/GLOBAL_STATE/DECISIONS/CONTEXT_INDEX
AgentCore hooks, rules, capability leases, or LangGraph checkpoints
```

AgentCore runtime must not consume:

```text
SwarmRecall memories or PostgreSQL database
SwarmVault wiki/graph/state as AgentCore memory
SwarmClaw sessions/tasks/prompts/skills
Swarm API keys or Swarm runtime credentials
```

Cursor may use AgentCore for **developer continuity while editing Swarm repositories**. That developer-side `.agentcore` metadata must never be packaged into, imported by, or required by the Swarm runtime.

Final isolation acceptance must prove:

1. AgentCore works with Swarm stopped.
2. Swarm works with AgentCore/Bifrost/PG18 stopped.
3. Both run simultaneously.
4. No port, process, database, environment variable, MCP, prompt, skill, projection, state, or backup crossover occurs.

---

# 4. AgentCore current implementation state

## 4.1 Cursor lean context and Stage B harness

Verified current Cursor posture:

```text
Cursor: 3.12.30 x64
Global AgentCore rules: exactly 1
Operator-managed skill: exactly 1 (agentcore-project-lifecycle)
Shared/plugin skill noise: 0 active
Third-party extensibility: OFF
Cursor MCP entries: exactly 1 (agentcore-gateway)
```

Stage B is implemented and accepted.

Registered hook events:

```text
sessionStart
beforeSubmitPrompt
preToolUse
beforeShellExecution
afterFileEdit
postToolUse
stop
```

The Stage B scope contract is:

```text
<project>\.agentcore\runtime\session-scope.json
```

It is generated, ignored, ephemeral, and noncanonical.

Stage B capabilities:

- exact-once prompt capture;
- automatic fresh-chat recovery;
- Step 0 intent/decomposition/acceptance/file-scope gate;
- projection freshness gate;
- out-of-worktree deny;
- dangerous shell deny;
- observed file footprint;
- undeclared-file detection;
- one structured final review;
- fail-open on internal hook crashes;
- one-command rollback to Stage A.

Accepted evidence:

```text
Commit: 1f7c077
Audit: @D:\github\agentcore-control-plane\audits\cursor-context\CURSOR_STAGE_B_INTEGRITY_HARNESS_ACCEPTANCE_2026-07-24.md
Rollback: python scripts/agentcore_cursor/rollback_stage_b.py
Backup: @E:\AgentCore-Backups\agentcore-control-plane\cursor-stage-b-20260724-233811
Tests: 26/26 PASS, including 100 protocol iterations
```

Custom Cursor subagents currently source-controlled:

```text
code-reviewer          — read-only changed-code reviewer
test-writer            — test-only bounded writer
reflective-optimizer   — proposal-only Milestone/deep-audit reflector
```

Superpowers methods were adapted into AgentCore policy without restoring the plugin's competing doctrine or fourteen active skills.

## 4.2 Lossless memory and rolling context

Current verified behavior includes:

- PostgreSQL-backed immutable evidence;
- idempotent event writes;
- L0 raw tail, L1 span summaries, L2 session summaries, L3 project chronology;
- stable pagination;
- exact source expansion;
- model-aware context profiles including one-million-context;
- atomic generated projections;
- backup/WAL/PITR evidence;
- project/worktree/session/thread isolation;
- restart-safe compaction and recovery.

The `Continue.` hard gate passed with the original one-word prompt captured exactly once. Projection revision 22 was reported during Stage B acceptance.

## 4.3 Tool-use policy

Task-class gates are encoded in:

```text
@D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml
@C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc
```

Required behavior:

- Arabold Docs before external dependency/SDK/API/schema/protocol work.
- Serena before high-risk semantic or cross-file structural edits; block such edits when Serena cannot verify them.
- Sequential Thinking before architecture, migration, concurrency, recovery, or major refactor decisions.
- Depwire before and after structural changes.
- Playwright for browser/UI/E2E acceptance.
- Skills-Hub for on-demand untrusted procedural knowledge.
- Context Fabric is optional, capability-gated, and noncanonical.

## 4.4 IDE enrollment package

Current universal package:

```text
@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
```

It was updated on 2026-07-25 to:

- identify the current IDE;
- modify only that IDE;
- install one `agentcore-gateway`;
- preserve native app/model/sandbox/UI settings;
- distinguish config presence from native lifecycle validation;
- represent direct-write/manual/UI-only/unsupported modes;
- separate MiniMax Code from MiniMax Classic;
- classify Open Interpreter GUI as unsupported and CLI separately;
- document the Swarm development/runtime boundary;
- require `@` plus full absolute paths in Cursor prompts.

Do not claim all IDEs are fully live-validated. Read the current profile/audit for each client.

---

# 5. Bifrost and ChatGPT tunnel — current state and immediate blocker

## 5.1 What is working

```text
Bifrost version: v2.0.0-prerelease1
Dashboard: http://127.0.0.1:8080
MCP: http://127.0.0.1:8080/mcp
Dashboard bind: loopback
Dashboard auth: disabled
Health: 200 / db_pings ok
```

The dashboard-auth-disabled posture is acceptable only while the dashboard stays loopback-only and is not exposed through the ChatGPT compatibility proxy/tunnel.

The MCP catalog currently reports all 13 upstream clients connected, including Serena through a prewarm proxy. AgentCore memory remains 10 tools; project router remains 4 tools; Skills-Hub exposes 3 read-only tools to the normal profile.

The ChatGPT custom app is connected through:

```text
OpenAI Secure MCP Tunnel
  -> local tunnel-client
  -> local compatibility proxy
  -> Bifrost
```

The proxy allowlist should expose only:

```text
/mcp
/.well-known/oauth-protected-resource
/healthz
/readyz
```

and deny dashboard/API/model-provider paths.

## 5.2 Bifrost closeout commit and independent failure

Cursor reported a Bifrost closeout at:

```text
Commit: 2309e10
Audit: @D:\github\agentcore-control-plane\audits\bifrost\BIFROST_COMPLETE_CONFIGURATION_ACCEPTANCE_2026-07-24.md
```

Independent dashboard verification **failed** and found material drift:

- dedicated ChatGPT virtual key existed in Bifrost's DB but had wildcard access to all MCP servers;
- source/runtime JSON had five virtual-key profiles while the DB/dashboard had six;
- the Windows env variable was absent at verification time;
- only OpenAI and OpenRouter were live despite source claims for additional providers;
- OpenAI model listing failed with an invalid-key condition;
- Ollama model count was zero;
- third-party MCP tool counts drifted from the point-in-time audit;
- `outputSchema` is present upstream but stripped by this Bifrost prerelease;
- ChatGPT's wildcard profile could reach filesystem, Serena mutations, Depwire mutations, OpenRouter generation, and possibly skill installation.

The operator has since created and confirmed this User-scope environment variable:

```text
BIFROST_MCP_VK_CHATGPT
```

No value should ever enter docs, Git, chat, or logs.

## 5.3 Immediate AgentCore blocker

Before normal ChatGPT AgentCore use or Swarm source implementation, execute a **targeted Bifrost independent-verification remediation** in:

```text
@D:\github\agentcore-control-plane
```

Required outcomes:

1. Replace ChatGPT wildcard access with an explicit narrow allowlist.
2. Use the dedicated ChatGPT key only; never fall back to builder/operator.
3. Reconcile source renderer, runtime config, Bifrost DB, and dashboard state.
4. Reconcile actual live providers through supported Bifrost APIs/DB ownership.
5. Disable or accurately classify invalid OpenAI provider credentials.
6. Verify Ollama from live health/model discovery.
7. Keep only AgentCore-owned exact tool counts hardcoded; treat third-party counts as dated evidence.
8. Keep the proxy path allowlist and deny dashboard/API/model endpoints.
9. Restart Bifrost, proxy, and tunnel-client in dependency order.
10. Validate MCP `tools/list` using the actual ChatGPT key.
11. Keep outputSchema passthrough as a documented Bifrost limitation; do not fabricate it in the proxy.
12. Run Stage B 26/26, LangGraph 17/17, memory lifecycle, projections, isolation, and secret scans.

Do not refresh the ChatGPT custom-app action snapshot until the narrow profile and parity pass independent verification.

---

# 6. Autonomous LangGraph developer workflow

## 6.1 Current production wiring

Production commands run only from:

```text
@D:\github\agentcore-control-plane
```

Never launch the production workflow from `D:\github\deepagents`.

Operator CLI:

```text
python -m agentcore workflow init
python -m agentcore workflow start
python -m agentcore workflow status
python -m agentcore workflow pause
python -m agentcore workflow approve
python -m agentcore workflow reject
python -m agentcore workflow resume
python -m agentcore workflow cancel
python -m agentcore workflow logs
python -m agentcore workflow evidence
python -m agentcore workflow topology
python -m agentcore workflow studio
```

Production architecture:

```text
Project Charter + locked Milestones
        |
        v
LangGraph orchestration
        |
        +-- PostgresSaver in agent_core / PostgreSQL 18
        +-- deterministic entry/exit and scope gates
        +-- bounded Deep Agents worker nodes
        +-- builder/research/test/reviewer roles
        +-- critic
        +-- deterministic scorer
        +-- independent judge
        +-- risk-based rework loop
        +-- capability profiles and JIT leases
        +-- human pause/resume
        +-- evidence, handoff, projection, restart recovery
```

Accepted evidence:

```text
LangGraph fixture: 17/17 PASS
Topology fingerprint: a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32
Deep Agents: deepagents==0.6.12, bounded worker harness only
Production checkpointing: PostgreSQL PostgresSaver
```

Studio is development-only:

```text
http://127.0.0.1:2024
```

Studio uses the Agent Server's dev checkpointer, not the production PostgresSaver. It is not a persistent Windows service. `LANGSMITH_TRACING=false` and `LANGGRAPH_CLI_NO_ANALYTICS=1` remain the privacy posture.

## 6.2 Replacing the human in the middle as closely as practical

The target is not to remove every operator gate. It is to replace routine human review/approval with a governed **Supervisor Proxy** while preserving Tony for genuine irreversible decisions.

Recommended decision path:

```text
LangGraph reaches a pause/decision node
        |
        v
Decision classifier
        |
        +-- deterministic / low risk
        |      policy + tests + independent judge auto-resolve
        |
        +-- medium risk / bounded ambiguity
        |      ChatGPT or Codex Supervisor Proxy
        |      receives evidence packet, diff, tests, risks, rollback
        |      returns structured decision + confidence + evidence references
        |
        +-- high risk / irreversible / authority-changing
               Tony approval required
```

Supervisor Proxy duties:

- use exact AgentCore evidence IDs, not chat summaries alone;
- review the current diff, tests, scope contract, acceptance, and rollback;
- reject undocumented assumptions;
- append its decision through AgentCore memory;
- resume the same LangGraph thread only after the decision is durably recorded;
- never edit locked authority or widen capabilities by itself.

Potential implementations:

1. **ChatGPT custom app supervisor** — useful for interactive operator-style review after the ChatGPT VK is narrowed and independently verified.
2. **Codex verifier/supervisor** — useful as a fresh-context code reviewer or structured decision agent.
3. **API-backed supervisor node** — the most autonomous option; LangGraph invokes an approved model directly and stores the structured decision, with ChatGPT/Codex UI as fallback.

Tony remains mandatory for:

- locked architecture/Milestone changes;
- secret rotation or disclosure;
- live DDL/migrations;
- destructive filesystem/drive operations;
- force-push or history rewrite;
- external spending or public exposure;
- weakening security/isolation/lossless guarantees;
- combining AgentCore with Swarm runtime.

The workflow is not considered fully autonomous until a low-risk real project passes start, pause, proxy decision, resume, rework, process-kill recovery, independent review, commit, handoff, and restart acceptance.

---

# 7. Swarm current reconstruction

## 7.1 Current source repositories

```text
SwarmClaw:  @D:\github\vendor\swarm\swarmclaw
SwarmRecall:@D:\github\vendor\swarm\swarmrecall
SwarmVault: @D:\github\vendor\swarm\swarmvault
Control:    @D:\github\swarm-ecosystem-control
```

The saved Cursor plan is named:

```text
local_swarmclaw_ecosystem_completion_82d98268.plan.md
```

Verify its actual live path before using it as a Cursor `@` reference. Plans under `.cursor\plans` are not architecture authority.

## 7.2 Upstream facts and local-plan drift

Current upstream evidence at handoff creation:

```text
SwarmClaw package: 1.9.40
SwarmRecall: 0.3.0, self-host-only
SwarmVault repository: 3.21.0
```

The saved plan recorded older local versions for SwarmClaw and SwarmVault. Current local branches/HEADs and upstream divergence must be reverified before edits.

SwarmRecall official local architecture uses:

```text
API: 3300
Dashboard: 3400
PostgreSQL 16 + pgvector
Meilisearch: 7700
local embeddings
optional in-memory cache when hosted Redis is absent
```

AgentCore authority records an existing Swarm-owned PostgreSQL 16 endpoint at:

```text
127.0.0.1:55432
```

Do **not** create a second SwarmRecall database at the upstream example port `65432` until live cluster ownership and consumers are audited. `pnpm db:push` is an operator-gated live schema action requiring exact target proof, backup, restore proof, and schema diff.

## 7.3 Latest SwarmClaw gap audit

Cursor found:

### Deferred hosted products

SwarmDock and SwarmFeed are soft-disabled by default at runtime, but hosted URLs, UI surfaces, presets, and dependencies remain reachable. SwarmRelay has no code integration in SwarmClaw.

### Memory and knowledge

SwarmClaw currently uses local SQLite memory and local knowledge sources. It has:

- no `@swarmrecall/sdk` integration;
- no SwarmRecall health/degraded adapter;
- only a SwarmVault MCP preset, not a programmatic context-pack integration;
- no Vault-unavailable → file-search fallback wiring.

### Local providers

- Ollama currently defaults to native local behavior around `localhost:11434` and `/api/chat`.
- LM Studio already uses `http://127.0.0.1:1234/v1`.
- Do not force Ollama to `/v1` when its native provider path is the accepted implementation; normalize to `127.0.0.1` without breaking native protocol.

### Agent kit

Existing starter kits include several relevant roles but no single five-agent local team containing:

```text
Operator
Builder
Researcher
QA / Tester
Reviewer
```

### Bind posture

- Electron already uses `127.0.0.1`.
- dev scripts and CLI server default to `0.0.0.0`.
- local acceptance requires loopback by default with explicit opt-in for LAN bind.

## 7.4 Recommended answers to Cursor's three clarifying questions

Use these defaults unless Tony changes them:

### R1 — hosted Dock/Feed UI and network behavior

**Use a hard local-mode gate for the accepted local baseline.**

- Hide Dock/Feed marketplace/social nav, connector setup, and hosted MCP presets when local-only mode is active.
- Block channel/marketplace polling, auto-registration, and connector start.
- Preserve the code and an explicit future operator-controlled enable path.
- Do not delete `@swarmdock/sdk` in the first pass if removal would create unnecessary breakage; ensure it is never initialized in local-only mode.

### R2 — SwarmRecall integration dependency

**Use a pinned published `@swarmrecall/sdk` for runtime integration.**

- Point it at `http://127.0.0.1:3300`.
- Use the local monorepo/workspace package only for contract tests and upstream-development work.
- Do not create a production `file:` cross-repo dependency that couples SwarmClaw runtime packaging to the local SwarmRecall checkout.

### R3 — five-agent kit placement

**Add a secondary `Local Swarm Team` starter kit.**

- Make it the recommended/default kit only when the local-only ecosystem profile is selected.
- Do not replace upstream defaults for every SwarmClaw user.
- Use existing role/prompt/tool patterns; add only the missing QA role and required composition.

Additional default decisions:

- `127.0.0.1` is the default bind; `0.0.0.0` remains explicit opt-in.
- SwarmVault integration uses the official local MCP/CLI boundary and explicit token budgets.
- Vault ingest/compile is operator-approved or scheduled by explicit policy; query/read may be automatic.
- SwarmRecall failure degrades to existing SQLite session memory.
- SwarmVault failure degrades to bounded workspace file/knowledge search.
- Resource limits are benchmark-derived, not hardcoded from the original plan.

---

# 8. Correct Swarm execution order

Do not execute the saved plan's original repository order unchanged.

Correct order:

```text
1. @D:\github\swarm-ecosystem-control
   S0/S1 only: authority, evidence, live runtime inventory, port/storage/memory contracts,
   upstream comparison, backup roots, isolation tests.

2. @D:\github\vendor\swarm\swarmrecall
   S1/S2/S3 after S0 contracts are accepted.

3. @D:\github\vendor\swarm\swarmvault
   S1/S4.

4. @D:\github\vendor\swarm\swarmclaw
   S1/S5 plus source-local portions of S6/S7.

5. @D:\github\swarm-ecosystem-control
   S6/S7/S8/S9 integration, Windows lifecycle, backup/restore, performance,
   power-loss, and independent isolation acceptance.
```

Backups must live outside Git:

```text
@E:\SwarmBackups\<timestamp>
@G:\SwarmBackups\<timestamp>
```

Source control stores only sanitized manifests, hashes, and restore evidence.

The control repository should use branch `main`, not `master`.

No `.env` or `.env.local` secrets. Use Windows User-scope environment variables and source-controlled wrappers that name variables but never contain values.

---

# 9. Swarm fixed Milestones

```text
S0 — Evidence and Isolation
S1 — Source and Dependency Health
S2 — Local Data and Runtime Foundation
S3 — SwarmRecall Completion
S4 — SwarmVault Completion
S5 — SwarmClaw Runtime Completion
S6 — Inter-Service Integration
S7 — Bounded Autonomous Agent Team
S8 — Security, Performance, Recovery, Windows Lifecycle
S9 — Independent Acceptance and Simultaneous Isolation
```

Cursor may optimize Macro/Micro steps within each outcome after inspecting live code and runtime. It may not weaken the local-only, independent-runtime, no-cross-contamination, backup/restore, or acceptance outcomes without explicit operator approval.

---

# 10. Proper workflow for every implementation task

## 10.1 ChatGPT phase-start loop

1. Connect to AgentCore memory when available.
2. Read the locked authority chain.
3. Ask the required diagnostic questions.
4. Resolve current branch/HEAD/worktree/runtime evidence.
5. Identify the fixed outcome and hard boundaries.
6. Produce a Cursor prompt that gives Cursor implementation freedom inside those boundaries.
7. Review Cursor's plan/output only for substantive drift, not style preferences.

## 10.2 Cursor phase execution

1. Fresh chat for each bounded phase.
2. One write-capable agent unless a proven isolated worktree plan authorizes more.
3. Complete Stage B Step 0 contract before edits.
4. Read exact-version official docs through Arabold.
5. Use Sequential Thinking for architecture/recovery decisions.
6. Use Serena for high-risk semantic/cross-file edits.
7. Use Depwire before/after structural changes.
8. Use Playwright for browser/E2E acceptance.
9. Use AgentCore memory lifecycle and projections.
10. Run deterministic tests before model critics.
11. Fresh different-model read-only verifier after each high-risk repository/track.
12. Secret/junk scan, stage only intended files, commit, and push.
13. Build handoff and close the session.

## 10.3 Model/context economy

- Use 1M/Max only for genuinely repository-wide planning or final release review.
- Use normal context for bounded implementation chats.
- Start a fresh chat per phase; rely on AgentCore recovery instead of carrying giant conversations.
- Keep Auto model routing off when model identity matters.
- Use a different model/fresh context for independent review.

---

# 11. Artifact inventory

## 11.1 AgentCore root authority

```text
@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\BLUEPRINT.md
@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md
@D:\github\agentcore-control-plane\MILESTONES.md
@D:\github\agentcore-control-plane\AGENTS.md
@D:\github\agentcore-control-plane\CLAUDE.md
@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
@D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml
@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json
@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json
```

Historical Swarm-first evidence only:

```text
@D:\github\agentcore-control-plane\CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md
@D:\github\agentcore-control-plane\VALIDATION_REPORT.md
@D:\github\agentcore-control-plane\ECOSYSTEM_ARCHITECTURE.md
```

## 11.2 Current AgentCore handoffs and runbooks

```text
@D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md
@D:\github\agentcore-control-plane\docs\operations\AUTOMATIC_NEW_CHAT_RECOVERY.md
@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_AND_STUDIO.md
@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_QUICKSTART.md
@D:\github\agentcore-control-plane\docs\operations\OPENROUTER_MCP.md
@D:\github\agentcore-control-plane\docs\operations\DORMANT_MCP_CAPABILITY_CATALOG.md
@D:\github\agentcore-control-plane\docs\bifrost\BIFROST_OPERATOR_RUNBOOK.md
@D:\github\agentcore-control-plane\docs\bifrost\BIFROST_PROVIDER_RUNBOOK.md
@D:\github\agentcore-control-plane\docs\bifrost\BIFROST_CODE_MODE_RUNBOOK.md
@D:\github\agentcore-control-plane\docs\bifrost\CHATGPT_SECURE_MCP_TUNNEL.md
```

## 11.3 Current acceptance evidence

```text
@D:\github\agentcore-control-plane\audits\cursor-context\CURSOR_STAGE_B_INTEGRITY_HARNESS_ACCEPTANCE_2026-07-24.md
@D:\github\agentcore-control-plane\audits\cursor-context\CURSOR_NATIVE_SKILL_SURFACE_2026-07-24.md
@D:\github\agentcore-control-plane\audits\skills-hub\SKILLS_HUB_BIFROST_ACCEPTANCE_2026-07-23.md
@D:\github\agentcore-control-plane\audits\skills-hub\PROJECT_LIFECYCLE_SKILL_ACCEPTANCE_2026-07-24.md
@D:\github\agentcore-control-plane\audits\bifrost\BIFROST_COMPLETE_CONFIGURATION_ACCEPTANCE_2026-07-24.md
@D:\github\agentcore-control-plane\audits\LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json
@D:\github\agentcore-control-plane\audits\LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md
@D:\github\agentcore-control-plane\audits\MEMORY_GATEWAY_HEALTH_2026-07-22.md
```

Pending new evidence after remediation:

```text
@D:\github\agentcore-control-plane\audits\bifrost\BIFROST_INDEPENDENT_VERIFICATION_REMEDIATION_2026-07-25.md
```

## 11.4 Recent point-in-time commits

Always verify current HEAD; these are milestones, not guaranteed latest HEAD.

```text
c751083  memory lifecycle/projection/foundation staging
59c0ab8  lean foundation cutover
0757c26  initial Skills-Hub/Google phase
696542d  Skills-Hub isolated read-only Bifrost integration
fd58c4b  project lifecycle skill
d1b5884  native skill normalization and lifecycle acceptance
c65e8e1  final lean-surface/version verification
1f7c077  Cursor Stage B integrity harness
2309e10  Bifrost closeout (independent verification later failed)
```

## 11.5 AgentCore backups

```text
@E:\AgentCore-Backups\agentcore-control-plane\cursor-stage-b-20260724-233811
@E:\AgentCore-Backups\agentcore-control-plane\bifrost-closeout-20260724-2112
@E:\AgentCore-Backups\agentcore-control-plane\lean-cursor-foundation-20260723-224300
```

Treat backup roots as secret-bearing.

## 11.6 Swarm plan and source

```text
Uploaded/saved plan: local_swarmclaw_ecosystem_completion_82d98268.plan.md
@D:\github\swarm-ecosystem-control
@D:\github\vendor\swarm\swarmclaw
@D:\github\vendor\swarm\swarmrecall
@D:\github\vendor\swarm\swarmvault
```

Official upstreams:

```text
https://github.com/swarmclawai/swarmclaw
https://github.com/swarmclawai/swarmrecall
https://github.com/swarmclawai/swarmvault
```

---

# 12. Current drift and risk register

| ID | Risk | Current treatment |
|---|---|---|
| A-01 | ChatGPT Bifrost VK profile was wildcard | Targeted remediation must replace with explicit allowlist |
| A-02 | Bifrost source/runtime/DB/dashboard profile drift | Reconcile through supported Bifrost ownership/API path |
| A-03 | Claimed provider set differs from live providers | Validate each provider through runtime/model/request evidence |
| A-04 | OpenAI provider key invalid | Disable/defer or operator rotates correct OpenAI key; never substitute OpenRouter |
| A-05 | Bifrost strips `outputSchema` | Known prerelease limitation; annotations pass; do not fabricate in proxy |
| A-06 | Serena long calls can be interrupted | Treat connected-degraded until a real long-call/reconnect fix passes |
| A-07 | Not all IDEs are native live-validated | Read current profile/audit; do not infer from config presence |
| S-01 | Saved Swarm plan used PG port 65432 | Audit and preserve existing Swarm PG16 at 55432 when healthy |
| S-02 | Saved Swarm plan put backups inside Git | Use E:/G: external backup roots |
| S-03 | Saved Swarm plan used `.env` examples | Use Windows User-scope variables and wrappers |
| S-04 | SwarmClaw/SwarmVault local versions lag upstream | Fetch/diff in isolated branches before edits |
| S-05 | `pnpm db:push` could target wrong DB | Require target proof, backup, restore, diff, operator approval |
| S-06 | Local auth design may duplicate existing support | Audit existing source/emulator support before custom auth |
| S-07 | Resource caps were speculative | Benchmark on actual workstation before making defaults |
| S-08 | Dock/Feed are soft-disabled but still reachable | Local-only gate must hide/block network while preserving future opt-in |
| S-09 | SwarmClaw lacks Recall/Vault wiring and 5-agent kit | Implement by reusing official SDK/MCP and existing role patterns |

---

# 13. Immediate dependency-ordered next actions

## AgentCore first

1. Run targeted Bifrost independent-verification remediation in `@D:\github\agentcore-control-plane`.
2. Run a fresh GPT-5.6 Sol read-only Bifrost verification against the actual ChatGPT key.
3. Refresh the ChatGPT custom-app actions only after the narrow profile passes.
4. Run/finish the bounded AgentCore hardening and IDE alignment audit if current evidence does not already show accepted closeout.
5. Audit `MASTER_CONFIG_AND_PROMPT.md` after any Bifrost/profile changes and run its validators.

## Swarm second

6. Apply the mandatory corrections to the saved Swarm plan.
7. Execute S0/S1 in `@D:\github\swarm-ecosystem-control` first.
8. Independently verify the isolation/port/storage/backup/memory-ownership contracts.
9. Execute SwarmRecall, then SwarmVault, then SwarmClaw in fresh repository-local chats.
10. Return to the control repo for S6–S9 integration and independent simultaneous-operation acceptance.

Do not run source implementation in SwarmClaw before S0/S1 establishes the live database, port, storage, backup, environment, and isolation contracts.

---

# 14. Template for future Cursor prompts

Every new Cursor prompt should follow this structure:

```text
# ROLE / BOUNDED TASK NAME

Canonical repository:
@<full absolute repository path>

Macro outcome:
<fixed result>

Locked constraints:
<authority, security, ecosystem boundary, storage, no-cross-write>

Before planning or editing:
1. Read listed authority files using @ + full absolute paths.
2. Activate the project and recover AgentCore context.
3. Inspect current branch/HEAD/worktree and inherited WIP.
4. Use Arabold/Serena/Sequential Thinking/Depwire as required.
5. Ask the operator targeted questions if an unresolved assumption would change code or runtime.

Implementation freedom:
Use full repository awareness and dynamic tests to choose the best implementation.
You may optimize, add, remove, split, combine, or reorder Macro/Micro steps inside the fixed outcome.
Do not preserve a proposed implementation merely because it appeared in an earlier plan.

Execution controls:
- one writer unless isolated worktrees are explicitly approved;
- no unrelated repo/config edits;
- deterministic tests before model review;
- backup and rollback;
- secret/junk scan;
- commit and push intended source only.

Stop conditions:
<architecture change, destructive action, secret, live DDL, isolation failure, rollback failure>

Required final report:
<evidence, tests, hashes, commits, rollback, remaining blockers>

End with:
CURSOR CONTINUATION PROMPT
```

---

# 15. Bootstrap prompt for the next ChatGPT project chat

```text
Continue from the attached AGENTCORE_SWARM_DUAL_ECOSYSTEM_HANDOFF_2026-07-25.md.

Do not rely on the prior long chat.

First, explicitly connect to @agentcore-gateway and perform read-only AgentCore checks:
- memory_status
- project_list
- project_status for agentcore-control-plane
- bounded startup/retrieval context

Then read the AgentCore authority chain:
@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\BLUEPRINT.md
@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md
@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md

Treat AgentCore and Swarm as separate ecosystems.
AgentCore may support Cursor's developer continuity while editing Swarm code, but no AgentCore runtime dependency may enter Swarm runtime.

Before creating any Cursor plan or prompt, ask me 3–7 focused diagnostic questions about:
- the active workstream;
- the current repo/workspace;
- branch/HEAD/dirty state;
- whether Bifrost remediation has run;
- currently active writer agents;
- Plan versus execution intent;
- newer evidence since the handoff.

Current expected priority:
1. Complete Bifrost independent-verification remediation and narrow the ChatGPT virtual-key profile.
2. Independently verify Bifrost and refresh the ChatGPT app actions.
3. Confirm AgentCore hardening/IDE alignment and the master enrollment package.
4. Apply mandatory corrections to the Swarm plan.
5. Execute Swarm S0/S1 in swarm-ecosystem-control before any source-repo implementation.

When writing Cursor prompts:
- use @ + full absolute Windows paths;
- state the macro goal and locked boundaries;
- empower Cursor to inspect the full codebase and optimize Macro/Micro steps;
- require Cursor to ask the operator before assumptions that materially change written code or runtime;
- use current official docs and mandatory tool gates;
- end bounded tasks with tests, rollback, evidence, commit/push, and a continuation prompt.

Do not ask me to repeat project history before using AgentCore memory and the attached sources.
```

---

# 16. Retirement criteria for this handoff

This handoff can be archived when:

- Bifrost source/runtime/DB/dashboard parity passes independent verification;
- ChatGPT uses the dedicated narrow VK profile with no wildcard tools;
- provider status is accurately validated;
- the ChatGPT app action snapshot is refreshed;
- AgentCore final hardening and IDE alignment are accepted;
- Swarm S0/S1 authority and isolation contracts exist;
- SwarmRecall, SwarmVault, and SwarmClaw pass their repository-local Milestones;
- AgentCore-only, Swarm-only, and simultaneous-operation isolation all pass;
- the LangGraph supervisor proxy completes a controlled real-project pilot;
- ordinary continuation no longer depends on manual chat handoffs.

