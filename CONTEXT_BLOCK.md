> **SUPERSEDED (historical context block, 2026-06-28).** For current grounding read, in order:
> `PROJECT_ANCHOR.md` (constitution) → `DOC_AUTHORITY.md` (hierarchy) → `database-plan.md` →
> `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` (current state) →
> `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md`. Use this file for historical planning context only.

# CONTEXT_BLOCK.md — AgentCore Swarm Full Automation Rollout

Generated for: Tony / CHAOSCENTRAL  
Generated on: 2026-06-28  
Purpose: Give a brand-new Codex Plan/Goal chat enough context to complete the AgentCore Swarm rollout without inheriting stale assumptions.

---

## 0. How Codex should use this file

You are Codex working on Tony's Windows PC `CHAOSCENTRAL`.

Start in **Plan Mode**. Do not mutate files during the first response. First produce a concrete completion plan that explicitly cross-checks this `CONTEXT_BLOCK.md` against the current live repo and current machine state.

After Tony approves the plan and switches you to Goal mode, execute the plan from the source authority.

Primary workspace:

```text
D:\github\agentcore-control-plane
```

Do **not** treat this as source authority:

```text
D:\MCP-Control-Plane
```

That folder is compatibility/live-ops evidence only until separately retired. If this chat was accidentally started in `D:\MCP-Control-Plane`, switch implementation work to `D:\github\agentcore-control-plane` before making changes.

---

## 1. Current user intent

The goal is to finish the **local-only AgentCore Swarm rollout** so every IDE agent on this PC automatically uses the same local memory/RAG stack without needing to be reminded in each prompt.

Mandatory high-level outcome:

1. All managed IDEs get the same foundation MCP baseline.
2. SwarmRecall and SwarmVault are mandatory surfaces for all managed IDEs.
3. All memory/knowledge flows are local only.
4. No Swarm cloud services are used.
5. No hosted SwarmRecall fallback is allowed.
6. No hosted SwarmVault/cloud persistence is allowed.
7. Rules/instructions in every IDE must enforce the same memory contract.
8. Old conflicting routes must be removed from active configs/rules.
9. Monitoring automations are removed for now to simplify the rollout.
10. Runtime startup, manual validators, backups, restore tests, and maintenance may remain.

Tony is tired and wants this set up correctly. Do not ask broad clarification questions. Make the best safe decisions from the repo, live configs, cloned Swarm docs, and this context block.

---

## 2. Source authority and conflict order

When facts conflict, use this order:

1. `D:\github\agentcore-control-plane` — source authority for AgentCore policy, runtime contracts, DB/memory governance, renderers, validators, docs.
2. Current live machine state — ports, config files, scheduled tasks, installed apps.
3. Cloned Swarm repos under `D:\github\vendor\swarm`.
4. Official current upstream docs for SwarmRecall, SwarmVault, SwarmClaw, SwarmRelay, SwarmFeed, SwarmDock.
5. Current conversation/user corrections.
6. `D:\MCP-Control-Plane` — compatibility/live-ops evidence only, not design authority.
7. Historical backups/transcripts — evidence only; do not rewrite.

Do not mutate backups, rollback trees, old transcripts, historical session logs, or archived evidence.

---

## 3. Machine identity and drive model

Hostname:

```text
CHAOSCENTRAL
```

Known hardware/software baseline:

```text
OS: Windows 11 Pro
CPU: Intel Core i9-14900KF, 24 cores / 32 threads
RAM: 128 GB DDR5
GPU: NVIDIA RTX 4070 SUPER, 12 GB VRAM
D: internal NVMe project/source tier
F: Samsung 990 PRO 4TB NVMe hot memory/RAG/database tier
E: 6 TB external archive/cache/large-file tier
G: backup target only
C: OS/apps/user config; do not add hot AgentCore data here
```

Drive roles:

```text
C:\ = OS, apps, user profile, app-owned configs only
D:\ = project folders, source repos, worktrees, build/run evidence
F:\ = active hot local memory/RAG/search/database tier
E:\ = archive, large files, raw corpora, cache, exports, backups, dumps, restore-test artifacts, cold storage
G:\ = backup target only
```

Important: `F:` has two different active meanings and must not be described vaguely.

### F: SwarmVault tier

```text
F:\AgentCore\agentmemory\swarmvault
```

Purpose:

```text
local-first RAG/wiki/graph/context packs/task ledger
```

Store type:

```text
raw\
wiki\
state\
state\graph.json
state\retrieval\
state\context-packs\
state\memory\tasks\
swarmvault.config.json
swarmvault.schema.md
```

Do not force SwarmVault primary state into Postgres.

### F: SwarmRecall/Postgres/search tier

SwarmRecall should use:

```text
PostgreSQL + pgvector
Meilisearch
SwarmRecall API / SDK / CLI / MCP
```

Expected local endpoints unless repo discovery proves a corrected local port:

```text
PostgreSQL / pgvector: 127.0.0.1:55432
SwarmRecall API:       http://127.0.0.1:3300
Meilisearch:           http://127.0.0.1:7700
```

### E: archive/cache tier

Use `E:` for:

```text
large files
raw corpora
archive
cache
exports
backups
dumps
restore-test artifacts
cold storage
```

Do not create a primary SQL system on `E:` during this pass.

---

## 4. SwarmRecall contract

SwarmRecall is the native local agent memory runtime.

Use SwarmRecall as upstream intends:

```text
agent/client -> SwarmRecall API/MCP/SDK/CLI -> local PostgreSQL + pgvector + local Meilisearch
```

SwarmRecall gives agents:

```text
memory
semantic search
knowledge graph
learnings
skills
shared pools
sessions/current memory where supported
dream/consolidation tools where local-only and safe
```

Normal IDE agents must not connect to Postgres and run ad hoc memory SQL. That does **not** mean memory avoids the database. It means memory reaches the database through SwarmRecall or through the governed gateway.

Correct interpretation:

```text
Allowed normal path:
  IDE agent -> global-memory-gateway and/or swarmrecall MCP/API -> local SwarmRecall service -> Postgres/pgvector + Meilisearch

Forbidden normal path:
  IDE agent -> raw SQL INSERT/SELECT/UPDATE into memory tables
```

Raw SQL is only for:

```text
admin
migration
repair
schema inspection
validator diagnostics
```

### global-memory-gateway relationship

Do not assume `global-memory-gateway` is already SwarmRecall MCP.

Verify implementation.

Target behavior:

```text
global-memory-gateway
  = governed cross-IDE memory policy broker
  = canonical normal memory write name used by IDE agents
  = enforces source attribution, dedupe, non-secret policy, project path, and write rules
  = routes durable memory to local SwarmRecall / local AgentCore persistence correctly
  = may preserve existing AgentCore audit/projection rows if already implemented
```

If `global-memory-gateway` does not route into local SwarmRecall correctly, fix the gateway or document the exact remaining adapter gap and fail acceptance.

### SwarmRecall MCP

SwarmRecall MCP is now mandatory for all managed IDEs. This is a correction from earlier plans that treated direct SwarmRecall MCP as out of scope.

Expected server name:

```text
swarmrecall
```

Expected launch style:

```text
swarmrecall mcp
```

or the equivalent source-controlled renderer command discovered in the local repo.

Use local-only configuration:

```text
SWARMRECALL_API_URL=http://127.0.0.1:3300
SWARMRECALL_API_KEY=<env/config reference, never literal>
MEILISEARCH=http://127.0.0.1:7700
Postgres local F: storage
```

No hosted fallback.

---

## 5. SwarmVault contract

SwarmVault is the local-first knowledge/RAG/wiki/graph/context-pack/task-ledger system.

It is **not** a Postgres database. It should not be moved into Postgres. It should use its upstream local-first design:

```text
raw/                 immutable ingested sources
wiki/                generated/human markdown, outputs, graph reports, context packs, task notes
state/graph.json     machine-readable graph
state/retrieval/     local search index
state/context-packs/ saved context packs
state/memory/tasks/  durable task ledger
```

Expected root:

```text
F:\AgentCore\agentmemory\swarmvault
```

Expected server name:

```text
swarmvault
```

Expected launch:

```text
swarmvault mcp
```

SwarmVault should be made automatic using:

```text
MCP exposure
agent rules/hooks where supported
managed sources
context packs
task ledger
local retrieval
graph-first guidance
```

### SwarmVault managed sources to register

Register real local managed sources:

```text
D:\github\agentcore-control-plane
D:\github\vendor\swarm\swarmrecall
D:\github\vendor\swarm\swarmvault
D:\github\vendor\swarm\swarmclaw
D:\github\vendor\swarm\swarmrelay
D:\github\vendor\swarm\swarmfeed
D:\github\vendor\swarm\swarmdock
```

Also register any local AgentCore runtime docs required by validators.

Acceptance:

```text
swarmvault doctor passes or only reports understood non-blocking warnings
managedSources is non-zero
retrieval status is healthy
graph stats are available
context pack build works
task ledger works
curated project knowledge can be queried locally
```

### SwarmVault tool surface policy

The `swarmvault` MCP server must be present in all managed IDEs, but not every IDE needs the full tool catalog.

Use a two-profile policy if the client/tooling supports it:

```text
swarmvault-admin:
  Codex and Cursor
  full or near-full tool surface

swarmvault-lite:
  OpenClaw, Open Interpreter, MiniMax new, MiniMax classic/Mavis, Antigravity, Claude Code unless full is explicitly needed
  read/query/context/task-health subset only
```

Suggested `swarmvault-lite` tools:

```text
workspace_info
search_pages
read_page
query_vault
build_context_pack
list_context_packs
read_context_pack
retrieval_status
doctor_vault
graph_stats
list_tasks
read_task
resume_task
```

Do not rely only on written rules to reduce tool bloat. If a client supports allowlists, use allowlists. If not, create/reuse a small wrapper/proxy if safe.

### SwarmVault agent installs

Run status checks first; then install where safe and source-controlled:

```powershell
cd F:\AgentCore\agentmemory\swarmvault
swarmvault install status --agent codex --hook
swarmvault install status --agent claude --hook
swarmvault install status --agent cursor
swarmvault install status --agent claw
swarmvault install status --agent antigravity
```

Recommended install targets:

```powershell
swarmvault install --agent codex --hook
swarmvault install --agent claude --hook --mcp --graph-first
swarmvault install --agent cursor
swarmvault install --agent claw
swarmvault install --agent antigravity
```

Preserve user-owned text in shared rule files. SwarmVault should only own its managed blocks.

---

## 6. Mandatory managed clients

Every rollout, renderer, validator, live adoption check, docs matrix, and rule audit must include:

```text
Codex
Cursor
OpenClaw
Open Interpreter
MiniMax new
MiniMax classic / Mavis
Antigravity
Claude Code
```

MiniMax new and MiniMax classic/Mavis are separate managed clients. Do not treat Mavis as covered by MiniMax new.

Each requires separate:

```text
renderer coverage
live config target
rule/skill cleanup
restart proof
live adoption validation
```

### Claude Code target

Tony corrected the Claude Code live target:

```text
C:\Users\ynotf\.claude\config.json
```

Also discover and reconcile:

```text
C:\Users\ynotf\.claude.json
project .mcp.json files
project/user .claude settings, skills, hooks
CLAUDE.md
```

If both `C:\Users\ynotf\.claude\config.json` and `C:\Users\ynotf\.claude.json` exist:

1. Treat `C:\Users\ynotf\.claude\config.json` as primary unless runtime discovery proves otherwise.
2. Back up both.
3. Remove active conflicting servers/rules from whichever file Claude Code actually reads.
4. Preserve auth/profile/session state.
5. Document the discovered reality.

Earlier evidence said `C:\Users\ynotf\.claude.json` contained context7 and Hostinger. Do not assume that is still true; verify.

---

## 7. Mandatory MCP baseline

Every managed IDE gets the foundation baseline below.

Mandatory foundation MCP servers:

```text
serena
sequential-thinking
cursor-agent-mcp
context-fabric
mcp-debugger
artiforge
global-memory-gateway
obsidian-vault
swarmrecall
swarmvault
```

Preserve unless explicitly retired:

```text
arabold-docs
```

Allowed additions:

```text
Codex: additional tools allowed because Codex can enable/disable tools.
Cursor: additional source-authority/admin tools allowed if required.
OpenClaw: eye2byte allowed as a user-approved exception.
Client internal/app-owned servers: allowed only if non-conflicting and explicitly documented.
```

Forbidden normal/default routes in active configs and rules:

```text
context7
raw mem0
direct composio
Hostinger
hosted SwarmRecall URLs
hosted SwarmVault/cloud persistence
direct SQL as normal memory guidance
D:\MCP-Control-Plane as design authority
SwarmVault described as a Postgres database
SwarmRecall described as automatically using the SwarmVault database
```

---

## 8. Global rule/instruction contract for every IDE

Audit active rules/instructions for:

```text
Codex AGENTS.md, AGENTS.override.md, .codex hooks/skills
Cursor .cursor/rules/*.mdc
OpenClaw skills/rules/config
Open Interpreter profiles/rules
MiniMax new skills/rules/config
MiniMax classic / Mavis skills/rules/config
Antigravity rules/workflows/settings
Claude Code config, CLAUDE.md, .claude skills/hooks/settings
generated AgentCore docs that live clients read
```

Patch active rule/config/instruction surfaces only. Do not rewrite backups or history.

Required global contract:

```text
For all agents on this PC:

1. Use SwarmRecall for durable agent memory, sessions, pools, knowledge, learnings, skills, and recall.
2. Use global-memory-gateway as the governed memory policy broker. It must route to local SwarmRecall/local AgentCore persistence correctly.
3. Use SwarmVault for local RAG/wiki/graph/context packs/task ledger.
4. Use context-fabric for repo continuity and working context.
5. Use obsidian-vault only for Obsidian-facing notes through the approved MCP/REST route.
6. Never use context7, raw mem0, direct composio, Hostinger, hosted SwarmRecall, hosted SwarmVault, or direct SQL as normal routes.
7. Raw SQL is admin/migration/repair/inspection only.
8. D:\ is code/projects, F:\ is hot local memory/RAG/search, E:\ is archive/cache/large files/backups.
9. Every durable memory/knowledge write must be source-attributed, non-secret, concise, deduplicated, and routed through governed services.
10. At task start, retrieve relevant SwarmRecall memory, context-fabric repo context, and SwarmVault knowledge/context packs automatically.
11. During task work, save durable decisions, corrected facts, reusable procedures, task state, and project lessons automatically when appropriate.
12. At task end, write a concise durable memory summary automatically when the task produced reusable knowledge.
```

Rule conflict classes to remove:

```text
context7 as docs route
mem0/raw mem0 as memory route
composio as normal tool route
Hostinger as default MCP
direct SQL for memory
D:\MCP-Control-Plane as authority
hosted SwarmRecall or hosted SwarmVault
SwarmVault as SQL DB
SwarmRecall automatically using SwarmVault DB
context-fabric optional/disabled
SwarmRecall/SwarmVault optional instead of mandatory
```

Known conflict patterns from earlier work:

```text
Cursor legacy mem0/composio/D:\MCP-Control-Plane rules
MiniMax and Mavis skill files teaching context7/mem0/composio
Antigravity instructions referencing context7
Claude Code config/rules carrying context7 and Hostinger
```

Verify current state; do not assume.

---

## 9. Remove monitors for now

Tony explicitly wants monitor automations removed to eliminate complexity until the system is running optimally.

Remove/disable from active rollout:

```text
agentcore-context-window-optimizer
agentcore-pgvector-database-monitor
agentcore-rag-runtime-monitor
agentcore-memory-projection-monitor
agentcore-mcp-drift-monitor
agentcore-live-client-adoption-monitor
agentcore-plugin-extension-monitor
spec-sync monitors
adoption polling monitors
drift scanning monitors
projection scanning monitors
background polling/re-audit loops
```

Keep:

```text
PostgreSQL startup ownership
SwarmRecall API startup ownership
Meilisearch startup ownership
explicit/manual validators
backup jobs
restore-test jobs
maintenance jobs
one-shot rollout validation commands
```

Docs must say:

```text
services come up at boot/logon
validators are run manually or during explicit rollout
no background monitor mutates or continuously re-audits the system in this pass
```

---

## 10. Context-window optimization

Do not claim 128 GB RAM changes vendor model hard token limits.

The correct policy is effective-context optimization:

```text
set each client to largest officially supported model/context mode already available
no unsupported binary/config hacks
compact MCP server descriptions
reduce duplicate/retired tool surfaces
use context-fabric for repo continuity
use SwarmRecall durable recall
use Meilisearch local full-text recall
use Postgres/pgvector semantic recall
use SwarmVault context packs and graph-first guidance
use D:\ for project/source roots
use F:\ for hot memory/RAG/search state
use E:\ for archive/cache/corpora
avoid dumping whole repos into prompts
```

If a model/client supports a 1M context setting, use the official supported setting. Otherwise do not fake it.

Codex-specific note: Codex reads project guidance through `AGENTS.md` files and has a default combined project-doc limit. If necessary, increase the official project-doc limit in config rather than stuffing everything into one prompt. Keep `AGENTS.md` short and refer to `CONTEXT_BLOCK.md` / skills / docs for detail.

---

## 11. Swarm ecosystem scope

Mandatory for all IDEs:

```text
SwarmRecall
SwarmVault
```

Automation agent developer team only:

```text
SwarmClaw
SwarmRelay
SwarmFeed
SwarmDock
```

Set up broader Swarm repos only where beneficial for the automation agent developer team. Do not add SwarmClaw, SwarmRelay, SwarmFeed, or SwarmDock as default MCP surfaces for every IDE.

### SwarmClaw

Likely first additional Swarm runtime after core is green.

Requirements:

```text
self-hosted/local-only configuration
runtime state on this PC, preferably F:\AgentCore or an explicitly approved local path
no hidden cloud persistence
bounded tool surfaces
integrates with same SwarmRecall/SwarmVault/global-memory-gateway contract
does not fan out uncontrolled agents
```

### SwarmRelay

Activate only if fully self-hosted/local-only behavior is proven. If hosted backend is required, document as blocked/staged.

### SwarmFeed / SwarmDock

Keep staged/documented unless local-only storage/auth/network behavior is proven. Do not make them canonical memory or default IDE services during this pass.

---

## 12. Security and safety gates

Do not print secrets.

Before mutation:

```text
record git status
record current branch
back up every managed live config and active rule file
back up source-controlled managed files before edits
```

Potential live config roots to back up:

```text
C:\Users\ynotf\.codex\
C:\Users\ynotf\.cursor\
C:\Users\ynotf\.openclaw\
C:\Users\ynotf\.minimax\
C:\Users\ynotf\.mavis\
C:\Users\ynotf\.claude\
C:\Users\ynotf\.claude.json if present
C:\Users\ynotf\.gemini\
C:\Users\ynotf\AppData\Roaming\Antigravity\
Open Interpreter config/profile roots discovered on this PC
D:\github\agentcore-control-plane source-controlled managed files
```

Known security blockers/gaps to keep visible:

```text
raw tokens/API keys may exist in app configs; reports must not echo values
Qdrant 6333/6334 may be bound to 0.0.0.0; fix separately before Qdrant expansion
RDP/Portainer may be LAN-exposed; do not broaden agent access
filesystem MCP roots may be broad; split read-only/write profiles if in scope
Obsidian writes must be single-writer REST/MCP only, not raw filesystem writes
```

Do not log users out or destroy model provider/auth state. Replace raw secrets with environment references only where format support is proven.

---

## 13. Implementation tasks after Plan Mode approval

### Phase 1 — Audit/preflight

1. Confirm working directory and switch to `D:\github\agentcore-control-plane` if needed.
2. Record git status and branch.
3. Discover all live config paths for the managed clients.
4. Record listener proof for:
   ```text
   127.0.0.1:55432
   127.0.0.1:3300
   127.0.0.1:7700
   ```
5. Check SwarmVault root and `swarmvault doctor`.
6. Check SwarmRecall API/CLI/MCP local-only.
7. Check current context-fabric presence across all clients.
8. Check current SwarmRecall/SwarmVault MCP presence across all clients.
9. Check current global rules for forbidden routes.
10. Check current monitor automations/tasks/docs and mark for removal.

### Phase 2 — Source contract/renderers/validators

Update:

```text
contracts/master-mcp-server-config.json
renderers for Codex, Cursor, OpenClaw, Open Interpreter, MiniMax new, MiniMax classic/Mavis, Antigravity, Claude Code
validators
live apply scripts
docs generation
```

Enforce the mandatory MCP baseline:

```text
serena
sequential-thinking
cursor-agent-mcp
context-fabric
mcp-debugger
artiforge
global-memory-gateway
obsidian-vault
swarmrecall
swarmvault
```

Preserve `arabold-docs` unless explicitly retired.

Validators must fail if:

```text
managed client missing foundation MCP baseline
context-fabric missing
swarmrecall missing
swarmvault missing
MiniMax new not separately validated
Mavis not separately validated
Claude Code not managed
active configs/rules contain context7/raw mem0/composio/Hostinger/hosted SwarmRecall/hosted SwarmVault/direct SQL normal memory/D:\MCP-Control-Plane authority
raw MCP secrets appear in active config
SwarmVault managedSources is zero
SwarmRecall uses hosted fallback
E:\ is used as primary SQL
monitor automations remain active for this pass
```

### Phase 3 — global-memory-gateway

Verify whether `global-memory-gateway` routes to local SwarmRecall.

Acceptance:

```text
governed memory write succeeds
write is source-attributed, concise, non-secret, deduplicated
write reaches local canonical persistence
SwarmRecall can retrieve it through local API/MCP
no raw SQL needed by normal IDE agent
```

If the gateway is only writing older AgentCore Postgres schema, add/fix adapter to SwarmRecall or explicitly fail with exact TODO and blocker.

### Phase 4 — SwarmRecall

Verify:

```text
local API on 127.0.0.1:3300
local Meilisearch on 127.0.0.1:7700
local Postgres/pgvector on F: / 127.0.0.1:55432 unless discovery proves different
no hosted fallback
MCP stdio tool discovery works
memory store/search/list works
sessions/current works if supported
rules force automatic task-start/task-end memory behavior
```

### Phase 5 — SwarmVault

Verify:

```text
root is F:\AgentCore\agentmemory\swarmvault
raw/wiki/state/state\graph.json/state\retrieval exist or are initialized correctly
doctor passes
retrieval status passes
context pack build works
task ledger works
managedSources is non-zero
managed sources include authority repo and Swarm vendor repos
```

Install/align SwarmVault integrations:

```text
Codex hook
Claude Code hook/MCP/skill as appropriate
Cursor rules
OpenClaw skill/rules
Antigravity rules/workflow
other supported installs only if discovery proves correct target
```

### Phase 6 — Client config/rules

For each client:

```text
Codex
Cursor
OpenClaw
Open Interpreter
MiniMax new
MiniMax classic / Mavis
Antigravity
Claude Code
```

Do:

```text
render source-owned MCP config
apply through source-owned apply path
preserve auth/profile/session state
patch active rules only
remove forbidden routes
add global rule contract
restart-proof after apply
live adoption validation
```

### Phase 7 — Wider Swarm stack

After core SwarmRecall + SwarmVault green:

```text
SwarmClaw local setup for automation agent developer team only
SwarmRelay local-only validation or block
SwarmFeed staged/documented or block
SwarmDock staged/documented or block
```

Do not promote these to default IDE MCP surfaces.

### Phase 8 — Docs/handoff

Update:

```text
master MCP matrix
active governed client matrix
rollout runbook
restart handoff
context-window/effective-context policy
SwarmRecall local runtime doc
SwarmVault local runtime doc
Claude Code setup
Antigravity setup
MiniMax new setup
Mavis setup
Open Interpreter setup
rule conflict audit report
local-only Swarm ecosystem staging doc
CONTEXT_BLOCK.md if this file becomes stale
```

---

## 14. Acceptance tests

Run and require green or document exact blocker with evidence:

```powershell
validate-control-plane.ps1 -DryRun
Test-AgentCoreSwarmRecall.ps1
Test-AgentCoreSwarmVault.ps1
Test-AgentCoreContextFabricReadiness.ps1
Test-AgentCoreMemoryProjection.ps1
Test-AgentCoreRuntimeSuite.ps1
Test-AgentCoreLiveClientAdoption.ps1
```

Additional required checks:

```text
PostgreSQL listens on 127.0.0.1:55432.
SwarmRecall API listens on 127.0.0.1:3300.
Meilisearch listens on 127.0.0.1:7700.
SwarmRecall MCP stdio tool discovery works.
SwarmRecall memory store/search/list works.
global-memory-gateway write reaches local SwarmRecall/local canonical persistence.
SwarmVault root is F:\AgentCore\agentmemory\swarmvault.
SwarmVault doctor passes.
SwarmVault retrieval status passes.
SwarmVault managedSources is non-zero.
SwarmVault context pack build works.
SwarmVault task ledger works.
Every managed IDE has the mandatory MCP baseline.
context-fabric is present everywhere.
swarmrecall is present everywhere.
swarmvault is present everywhere.
Claude Code is managed at C:\Users\ynotf\.claude\config.json unless runtime discovery proves a different active target.
MiniMax new and Mavis are validated separately.
No active rule teaches retired routes.
No monitor automation remains active for this pass.
E:\ is not primary SQL.
D:\MCP-Control-Plane is not source authority.
Runtime startup ownership survives reboot/logon or an exact elevated command is written to handoff.
```

---

## 15. Final report required from Codex

When complete, report:

```text
1. What changed
2. Files changed
3. Live configs applied
4. Backups created
5. Validators run and results
6. Runtime endpoint proof
7. SwarmRecall proof
8. SwarmVault proof
9. Client adoption proof
10. Rule conflict cleanup summary
11. Monitor removal summary
12. SwarmClaw/Relay/Feed/Dock staging or local setup status
13. Any blockers requiring admin/elevated action
14. Exact restart steps for each IDE
15. Exact elevated commands, if any
16. Confirmation that no secret values were printed
17. Confirmation that no hosted Swarm services are used
18. Confirmation that D:\github\agentcore-control-plane is the source authority
```

---

## 16. First prompt for Codex Plan Mode

Paste this after saving this file at `D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`:

```text
We are in Plan Mode.

Read D:\github\agentcore-control-plane\CONTEXT_BLOCK.md completely.

Audit the current repo and live machine state against that context. Do not mutate files yet.

Create a decision-complete plan to finish the AgentCore Swarm Full Automation Rollout with these corrections:
- D:\github\agentcore-control-plane is source authority.
- D:\MCP-Control-Plane is compatibility/live-ops only.
- Remove all monitor automations for now.
- Keep runtime startup ownership, manual validators, backups, restore tests, and maintenance.
- Restore context-fabric everywhere.
- Add swarmrecall and swarmvault everywhere.
- All managed IDEs require the mandatory foundation MCP baseline.
- Add/manage Claude Code at C:\Users\ynotf\.claude\config.json unless runtime discovery proves another target.
- Treat MiniMax new and MiniMax classic/Mavis separately.
- Audit and fix active global rules/instructions so they enforce the same memory/RAG contract and remove conflicts.
- Use SwarmRecall as intended: local API/MCP/SDK/CLI over PostgreSQL+pgvector+Meilisearch, not raw SQL from normal IDE agents.
- Use SwarmVault as intended: local-first F:\AgentCore\agentmemory\swarmvault with raw/wiki/state/retrieval/context packs/task ledger, not Postgres.
- Keep everything local-only and no Swarm cloud.
- Wider Swarm repos are for the automation agent developer team only and must be staged/local-only unless proven.
- Do not print secrets.

In the plan, list:
1. Current audited state.
2. Exact files/scripts/configs to change.
3. Backup strategy.
4. Runtime checks.
5. MCP baseline/rendering strategy.
6. SwarmRecall completion steps.
7. SwarmVault completion steps.
8. global-memory-gateway verification/fix.
9. Rule conflict cleanup.
10. Claude Code setup.
11. MiniMax/Mavis split.
12. Monitor removal.
13. Context optimization strategy.
14. Wider Swarm stack staging.
15. Acceptance tests.
16. Any blockers requiring elevated/admin action.
```

---

## 17. Goal Mode handoff instruction

After Tony approves the Plan Mode response, Goal Mode can use:

```text
Execute the approved plan from D:\github\agentcore-control-plane. Follow CONTEXT_BLOCK.md. Back up managed files before mutation. Do not print secrets. Keep the rollout source-controlled and validator-driven. Continue until all acceptance tests pass or every remaining blocker is documented with exact evidence and next commands.
```
