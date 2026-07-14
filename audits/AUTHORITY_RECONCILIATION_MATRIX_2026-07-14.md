# Authority Reconciliation Matrix — 2026-07-14

Repository-wide classification of every instruction-bearing document, produced from the
full audit (root docs, docs/ tree, rule folders, contracts, Bifrost runtime evidence).

Columns: current claim → classification → replacement authority → treatment → executable/validator impact.

Treatments: `update` (edited to current policy) | `banner` (historical banner added) |
`evidence` (compatibility evidence label) | `swarm-only` (Swarm-ecosystem label) |
`pointer` (body replaced/pointed to authority) | `current` (no change needed).

## Root documents

| File | Stale claim (evidence) | Class | Replacement authority | Treatment | Impact |
| -- | -- | -- | -- | -- | -- |
| `PROJECT_ANCHOR.md` | Pointer to `database-plan.md` as schema design (line 5) | current, minor fix | `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` | update (pointer + §0.1 added) | validator: anchor conflict check |
| `DOC_AUTHORITY.md` | `database-plan.md` classified authoritative-stable; rewritten `CONTEXT_BLOCK.md` classified historical; stale root docs unindexed | current, corrected | itself (one hierarchy, 6 levels) | update | validator: read-order + classification checks |
| `CONTEXT_BLOCK.md` | Stray full-file code fence; no Bifrost composition; "provision H:" would destroy live Bifrost runtime; stale worktree framing | current after repair | itself | update | validator: no-fence check; H:-format ban |
| `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` | Swarm-first pipeline; SwarmRecall/SwarmVault in every IDE (lines 135–181); memory_append/search/state (222–247); drives missing H/I/J | historical | Bifrost handoff + execution plan | banner | validator: banner presence |
| `AGENTS.md` | Mandates reading `AGENT_DATABASE_BOOTSTRAP.md` + old DB contract (line 20); PG16 database-contract block (52–56) | current, residue fixed | memory-platform plan | update | mirrored workspace rule must match |
| `CLAUDE.md` | `DEPWIRE_NO_TELEMETRY=1` (27–28); drive list omits H/I/J; Swarm runtime facts uncaveated | current, residue fixed | MASTER_CONFIG §12, PROJECT_ANCHOR §2 | update | validator: telemetry-off check |
| `MASTER_CONFIG_AND_PROMPT.md` | Point-in-time counts; no project-execution standard reference | current | docs/agent-policy | update (add references) | none |
| `database-plan.md` | PG16.6 + pgvector 0.8.2 canonical (99); Swarm planes active (166–167, 553–554); Swarm in every IDE (1361); memory_append tools (566+) | historical schema evidence | `MEMORY_PLATFORM_EXECUTION_PLAN.md` | banner (extended) | validator: not-current check |
| `AGENT_DATABASE_BOOTSTRAP.md` | PG16.6 (19–20); `F:\AgentCore\agents_workspace` roots (33–41); memory_append as current tools (69–73); Swarm memory roles (89–99); direct-SQL ingest runner (103–109) | historical | `MEMORY_PLATFORM_EXECUTION_PLAN.md` | banner | validator: banner presence; AGENTS.md mandate removed |
| `SECURITY.md` | `D:\MCP-Control-Plane` as live-ops root (16); `global-memory-gateway` route (19) | current, 2-line fix | PROJECT_ANCHOR | update | none |
| `openmemory.md` | `E:\AgentCoreBackups` vs `E:\AgentCoreArchive`; Swarm runtime zone uncaveated | current, minor fix | CONTEXT_BLOCK (E:\AgentCoreArchive) | update | none |
| `Global-memory-and-context-system-revised-2.md` | Wrong hardware (RTX 5070, wrong drive map, line 11); PG on E:, backups on H: (83); Memory Broker bypassing Bifrost (7, 77, 134–137); reformat invitations (195–222) | historical research input | CONTEXT_BLOCK + execution plan | banner (do-not-execute) | validator: banner presence |
| `DEPWIRE.md` | Direct IDE MCP entries (48–63, 103–135); literal-key advice (65); `D:\MCP-Control-Plane` wrapper (82+); depwire-cloud green expectation (227) | current, body fixed | docs/bifrost/DEPWIRE_RECONCILIATION.md | update | none |
| `ECOSYSTEM_ARCHITECTURE.md` | Banner pointers name `database-plan.md`/Swarm handoff as current (6–7); un-struck authority claim (824); direct-DB appendix (793–808) | historical (banner fixed) | DOC_AUTHORITY | update (banner pointers) | none |
| `MILESTONES.md` (root) | none — operator-authored locked Milestones | operator evidence | rendered into execution plan | pointer (note added) | source of M0–M8 |
| `reports/` (10 research reports) | pre-decision architecture options | historical research | CONTEXT_BLOCK + MILESTONES | indexed historical in DOC_AUTHORITY | none |
| `Set-AgentCoreSwarmBaseline.ps1`, `swarmvault.config.json`, `swarmvault.schema.md` | Swarm baseline installers/config | swarm-only | n/a | swarm-only label | must not run for non-Swarm IDEs |

## docs/ tree

| File | Stale claim | Class | Treatment | Impact |
| -- | -- | -- | -- | -- |
| `docs/GLOBAL_AGENT_RULES.md` | `global-memory-gateway` only (30, 59–66); `E:\AgentCoreBackups`; drives missing H/I/J | stale-update | update; superseded by `rules/canonical/GLOBAL_AGENT_RULES.md` + pointer | validator: gateway-identity check |
| `docs/memory_system.md` | `global-memory-gateway` surface (10, 34–35, 109, 116); Swarm mixed in (58–109) | stale-update | update (identity + Swarm caveat) | none |
| `docs/storage_layout.md` | gateway in diagram (122); drives missing H/I/J; Swarm layout uncaveated (32–46) | stale-update | update | none |
| `docs/DRIVE_WRITE_BOUNDARY_RULE.md` | `D:\MCP-Control-Plane` is authority (3); forbids writes to D:/H:/I: (12–18); required reads under `D:\MCP-Control-Plane` (64–68) | stale-update | update | validator: MCP-Control-Plane-authority check |
| `docs/CONTEXT_WINDOW_OPTIMIZATION_POLICY.md` | gateway + Swarm-first memory routes (14–26); master-mcp-server-config budgets (30); removed optimizer monitor (36–44) | stale-update | update | none |
| `docs/AGENTCORE_AUTOMATION_OPERATIONS.md` | gateway writer (157); removed monitors listed as live (96–127) | stale-update | update | none |
| `docs/agent_integration_boundaries.md` | gateway rules (37, 78, 232); Swarm component sections (100–166) | stale-update + swarm-only sections | update | none |
| `docs/AGENTCORE_STORAGE_DESIGN.md` | gateway (94); `D:\MCP-Control-Plane` as approver (95) | stale-update | update | none |
| `docs/MCP_SERVER_CONFIGURATION_REFERENCE.md` | Swarm in per-client surfaces (64–72); master contract pointer (9–13) | stale-update | update | validator: Swarm-baseline check |
| `docs/contract-catalog.md` | pre-Bifrost probe snapshot | historical | banner | none |
| `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` | mandates Swarm baseline in every IDE (220–234, 264); instructs executing P1–P9 (594) | historical — highest risk | banner | validator: banner presence |
| `docs/RESTART_HANDOFF_20260626_AGENTCORE_FINAL_LEG.md` | gateway-only write path + Swarm substrate (12–15) | historical | banner | none |
| `docs/AGENTCORE_LOCAL_MEMORY_HANDOFF.md`, `docs/SYSTEM_HANDOVER_BLUEPRINT.md`, `docs/database_overview.md`, `docs/prompts/*-cleanup-prompt.md` | already banner-patched (2026-07-14 inherited work) | historical, patched | none (verified) | none |
| `docs/SWARMVAULT_SOURCE_REGISTRATION.md` | Swarm registration procedure | swarm-only | swarm-only label | none |
| `docs/PC-Master-Hardware-Software-Specs.md` (untracked root dup) | duplicate of `docs/evidence/` copy, diverged | duplicate | not committed; reconcile to single evidence copy | none |
| `docs/bifrost/*`, `docs/adr/*`, `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md`, `docs/prompts/install-agentcore-gateway-in-ide.md`, `docs/prompts/README.md` | none | current | none | anchor set |

## Rule folders

| File | Stale claim | Class | Treatment | Impact |
| -- | -- | -- | -- | -- |
| `rules/global-mcp-routing.md` | `global-memory-gateway` route (9); `DEPWIRE_NO_TELEMETRY=1` (18); `D:\MCP-Control-Plane` pointer (34); artiforge in critical set (38) | stale-update | update (Bifrost-first rewrite) | validator: telemetry + gateway checks |
| `rules/environment-and-secrets.md` | none (already reconciled) | current | none | none |
| `.cursor/rules/agentcore-env-policy.mdc` | `global-memory-gateway` (18, 22) | stale-update | update | derived from canonical policy |
| `.serena/memories/agentcore/local-memory-handoff-20260626.md` | pre-Bifrost routing + stale blocker | stale memory | update (historical note) | none |
| `.agentcore/docs/DOCS_INDEX.md` | none (2026-07-14 refresh) | current | none | none |
| `.agents/`, `.codex/` | empty | n/a | seed pointer to canonical policy | none |

## Contracts / machinery

| File | Claim | Class | Treatment | Impact |
| -- | -- | -- | -- | -- |
| `contracts/bifrost-upstream-mcp-registry.json` | 14/16 servers `permitted_tools: ["*"]` | current, transitional | document wildcard grants as transitional (M6 replaces) | validator: wildcard-documented check |
| `contracts/master-mcp-server-config.json` | legacy direct-mode catalog | historical (already indexed) | none further | none |
| `contracts/global-memory-database-contract.json` | PG16.6 contract | historical after memory platform M1; still describes live PG16 cluster | evidence note | AGENTS.md mandate softened |
| `schemas/tools/global-memory-gateway/*` | retired server schemas | historical | leave (evidence); noted in matrix | none |
| `registry/tool-registry.json`, `supervisor/*` | legacy generated model | historical (already indexed) | none further | none |
