# Document Authority Index — AgentCore Control Plane

**Source authority:** `D:\github\agentcore-control-plane`
**Bifrost runtime (current):** `F:\AgentCore\runtime\bifrost` (not design authority; historical `H:\AgentRuntime\bifrost` is vacated for Bifrost — remaining H: vacation is Milestone M9)
**Compatibility/live-ops evidence only:** `D:\MCP-Control-Plane`
**Updated:** 2026-08-04 (`AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION`; current-release truth, LangGraph runtime ownership, and documentation drift controls)

This file is the document hierarchy. It tells a new agent what to read, what is authoritative, and what must not be followed as current instructions.

---

## Authority hierarchy (one chain; nothing else overrides it)

1. `PROJECT_ANCHOR.md` — stable constitution and non-negotiable boundaries
2. `DOC_AUTHORITY.md` — this file: exact read order and classification
3. `BLUEPRINT.md` — locked goal, architecture, storage roles, lossless guarantees, and Milestone exit criteria (operator-approved; change requires explicit approval)
4. `CONTEXT_BLOCK.md` — current mutable system state and implementation progress
5. `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` — detailed Milestone execution guidance (derives from BLUEPRINT.md; BLUEPRINT wins on conflicts)
6. Current Bifrost contracts and ops runbooks (`contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json`, `docs/bifrost/`, `docs/operations/OPENROUTER_MCP.md`, `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md`, and `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md`). Handoffs are point-in-time evidence unless this file explicitly classifies one as current; dates never confer authority or live readiness.
7. `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md` — machine-fact authority (hardware, drives, installed software, runtime snapshots)

No other root or docs file may silently override this chain. If a document conflicts with a higher level, the higher level wins and the document must be reconciled or reclassified.

`D:\github\memory-context-database` contains supporting corpus/template planning (`DOCS_PLAN.md`, `DEPWIRE.md`) — it is **not** the controlling memory architecture.

---

## What to attach to a new chat

**Minimum (always attach):**

1. `PROJECT_ANCHOR.md` — immutable project constitution (includes Bifrost Gateway Override §0)
2. `DOC_AUTHORITY.md` — this hierarchy
3. `BLUEPRINT.md` — locked architecture, storage roles, lossless guarantees, Milestone exit criteria
4. `CONTEXT_BLOCK.md` — current system state + implementation progress
5. `contracts/bifrost-upstream-mcp-registry.json` — canonical upstream MCP registry
6. `contracts/agentcore-gateway-client.json` — single IDE gateway client contract
7. `MASTER_CONFIG_AND_PROMPT.md` — root setup guide with embedded reusable IDE prompt
8. `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` — current-state evidence synthesis (not architecture authority)

**For memory/context/database work, additionally attach:**

- `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` — detailed Milestone execution guidance
- `docs/handoffs/AGENTCORE_FULL_RECOVERY_SOURCE_HANDOFF_2026-07-16.md` — effectively-unbounded durable-memory and bounded recovery source handoff
- `docs/handoffs/AGENTCORE_FULL_RECOVERY_LIVE_ROLLOUT_HANDOFF_2026-07-17.md` — point-in-time M3.002 rollout evidence (`agentcore-memory` v0.6.0); current version/status comes from `CONTEXT_BLOCK.md` and `memory_status`
- `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md` — M6 LangGraph production + Studio runbook
- `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md` — exact `python -m agentcore workflow …` commands from control-plane
- `audits/M8/UNBOUNDED_DURABLE_MEMORY_RELEASE_ACCEPTANCE.md` — final release acceptance report with validator matrix and HEAD reference
- `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md` — point-in-time Context Engine v0.2.0/native-host/RUN11 acceptance; it does **not** certify the later v0.2.1 release candidate
- `audits/AGENTCORE_LANGGRAPH_AUTHORITY_RECONCILIATION_2026-08-04.md` — current release/runtime/documentation reconciliation and launch gates
- `docs/adr/ADR-2026-08-02-agentcore-bifrost-context-alignment.md` — current responsibility model, transport-plane separation, and future-extension gates

**Add as needed:**

- `docs/handoffs/AGENTCORE_SWARM_DUAL_ECOSYSTEM_HANDOFF_2026-07-25.md` — point-in-time dual-ecosystem handoff; current paths/status come from each control plane's current context block
- `docs/operations/OPENROUTER_MCP.md` — OpenRouter MCP (≠ API provider); OAuth + JIT bridge
- `docs/handoffs/OPENROUTER_MCP_OAUTH_BIND_HANDOFF_2026-07-20.md` — OpenRouter OAuth bind topic handoff
- `docs/handoffs/AGENTCORE_AUTONOMOUS_WORKFLOW_STUDIO_HANDOFF_2026-07-17.md` — workflow/Studio productization handoff (prefer runbook for commands)
- `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md` — zero-default-exposure dormant catalog
- `audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md` / `audits/CHERRY_MEMORY_LIFECYCLE_2026-07-20.json` / `audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md` — client enrollment + lifecycle evidence
- `docs/operations/CHERRY_STUDIO_AGENTCORE.md` — Cherry enroll/Agent/rollback runbook
- `docs/operations/AGENTCORE_CONTINUAL_LEARNING.md` — continual-learning vs AgentCore memory boundary
- `docs/prompts/cherry-agentcore-workspace-agent.md` — governed Cherry Agent prompt
- `audits/CHERRY_RUNTIME_FAILURE_2026-07-20.md` — Cherry PE/runtime repair evidence
- `audits/CONTINUAL_LEARNING_AUTOMATION_2026-07-20.md` — mystery-prompt / stop-hook trace
- `audits/CURSOR_HOOK_SKILL_RULE_INVENTORY_2026-07-20.md` — hooks/skills/rules inventory
- `docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md` — Cursor Stage A hook recovery runbook
- `audits/CURSOR_HOOK_LOCKOUT_2026-07-20.md` / `audits/CURSOR_NEW_CHAT_RECOVERY_2026-07-20.md` — hook lockout recovery evidence
- Historical cutover/implementation handoffs under `docs/operations/archive/handoffs/` (Bifrost 2026-07-12, Memory-platform 2026-07-14, Swarm 2026-06-30) — evidence only
- `docs/agent-policy/` — global New Project / Milestone / checklist / tool-lifecycle policy
- `docs/prompts/install-agentcore-gateway-in-ide.md` — standalone reusable IDE install prompt
- `docs/adr/ADR-2026-07-12-bifrost-mcp-gateway.md` — deployment ADR
- `docs/adr/ADR-2026-07-12-configuration-source-of-truth.md` — config authority ADR
- `docs/bifrost/` — classification matrix, profiles, Tentra, Depwire, migration/rollback runbooks
- `docs/evidence/PC-Master-Hardware-Software-Specs.md` — hardware/software facts
- `SECURITY.md` — secret/security policy
- `artifacts/bifrost-gateway-cutover-2026-07-12/` — cutover evidence / backup manifest
- Historical Swarm rollout packs only when working **inside** the Swarm ecosystem

---

## Authoritative — stable (safe to follow; change rarely, with approval)

| File | Purpose |
| -- | -- |
| `PROJECT_ANCHOR.md` | Immutable constitution: Bifrost gateway override, drives (incl. H/I/J), endpoints, memory path, baseline, forbidden routes |
| `BLUEPRINT.md` | **Locked implementation blueprint** — final goal, architecture, responsibility model, drive roles, lossless guarantees, STATE model, Milestone exit criteria (M0–M9), tool policy, security boundaries, change-control list. Operator-approved; no execution lead or specialist may change locked items without explicit approval. |
| `AUTHORITY_LOCK.md` / `contracts/authority-lock.yaml` | Authority-lock classification and enforcement manifest for operator-locked, governed mutable, generated read-only, and normal workstream files. |
| `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` | Detailed Milestone execution guidance; derives from BLUEPRINT.md; BLUEPRINT wins on conflicts |
| `docs/agent-policy/*.md` | Global New Project Bootstrap, Milestone execution, checklist, tool-lifecycle, and read-order policy |
| `contracts/global-agent-policy.yaml` | Canonical machine-readable semantic agent policy (source for per-IDE rule profiles) |
| `MASTER_CONFIG_AND_PROMPT.md` | Controlling IDE MCP/rules setup after Bifrost rebuild |
| `contracts/bifrost-upstream-mcp-registry.json` | Canonical upstream MCP servers + capability profiles |
| `contracts/agentcore-gateway-client.json` | Single `agentcore-gateway` client connection contract |
| `docs/adr/ADR-2026-07-12-bifrost-mcp-gateway.md` | Why native Windows Bifrost Gateway, auth, pin (original H: placement is historical evidence; current runtime is `F:\AgentCore\runtime\bifrost`) |
| `docs/adr/ADR-2026-07-12-configuration-source-of-truth.md` | Contracts → renderer → live Bifrost config; IDEs get gateway entry only (current live root `F:\AgentCore\runtime\bifrost`) |
| `docs/adr/ADR-2026-08-01-neutral-shared-swarmrecall-context-engine.md` | Neutral semantic-memory exception and portable Context Engine boundary |
| `docs/adr/ADR-2026-08-02-agentcore-bifrost-context-alignment.md` | AgentCore/Bifrost/Context Engine/Recall/Context Fabric/Arabold responsibility model and benchmark-gated future extensions |
| `docs/superpowers/specs/2026-08-02-agentcore-bifrost-context-alignment-design.md` | Approved design details subordinate to BLUEPRINT/ADR |
| `SERENA.md` | Current Serena project configuration, dormant shared-gateway disposition, safe host-local usage, and recovery boundary |
| `docs/bifrost/*.md` | Classification, profiles, Tentra local mode, Depwire reconciliation, migration/rollback |
| `SECURITY.md` | Secret and security policy |
| `AGENTS.md` | Source-controlled agent operating contract |

## Current-state — mutable (accurate now; updated as cutover progresses)

| File | Purpose |
| -- | -- |
| `CONTEXT_BLOCK.md` | Current mutable system state and launch gates. It is the only narrative file in this table allowed to claim current runtime readiness. |
| `audits/AGENTCORE_LANGGRAPH_AUTHORITY_RECONCILIATION_2026-08-04.md` | Current AgentCore/LangGraph documentation, runtime, and release-status reconciliation. |
| `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-03.md` | Point-in-time v0.9.1 release-candidate evidence; final exact-SHA reviews were pending in that report. |
| `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md` | Point-in-time v0.2.0 + RUN11 acceptance. Superseded for Context Engine release status by the v0.2.1 release-candidate note and current live validation. |
| `audits/AGENTCORE_BIFROST_CONTEXT_ALIGNMENT_2026-08-02.md` | Point-in-time protected-change, indexing, drift, review, validator, hash, and rollback evidence. |
| `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` | Current evidence synthesis (not architecture authority; live probes and `CONTEXT_BLOCK.md` win). |
| `docs/handoffs/AGENTCORE_FULL_RECOVERY_SOURCE_HANDOFF_2026-07-16.md` | Source-only handoff for model-aware active context, full-history recovery, and M3.002 validation |
| `docs/handoffs/AGENTCORE_FULL_RECOVERY_LIVE_ROLLOUT_HANDOFF_2026-07-17.md` | Point-in-time M3.002 rollout evidence; current memory/host status is superseded by 2026-08-02 acceptance and live probes |
| `docs/handoffs/AGENTCORE_AUTONOMOUS_WORKFLOW_STUDIO_HANDOFF_2026-07-17.md` | Workflow + Studio productization handoff (prefer `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md` for commands) |
| `docs/handoffs/OPENROUTER_MCP_OAUTH_BIND_HANDOFF_2026-07-20.md` | OpenRouter MCP OAuth bind + JIT availability claim |
| `docs/handoffs/AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md` | Previous full-chat handoff snapshot — operator-supplied status snapshot (superseded for dual-ecosystem state by July 25 handoff) |
| `docs/boundaries/SWARM_FOREIGN_BOUNDARY.md` / `contracts/foreign-ecosystem-boundaries.yaml` | Minimal pointer-only Swarm foreign-boundary capsule. Mutable Swarm runtime facts remain owned by `D:\github\swarm-ecosystem-control`. |
| `docs/operations/OPENROUTER_MCP.md` | OpenRouter MCP runbook (registry `dormant` vs lifecycle `authenticated_dormant`) |
| `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md` | M6 LangGraph production + Studio runbook |
| `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md` | Operator quickstart (control-plane cwd only) |
| `audits/LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md` | Studio port 2024 live accept + PNA / browser-credential gate |
| `audits/LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json` | Fixture E2E 17/17 + topology / kill-resume / isolation |
| `audits/MEMORY_GATEWAY_HEALTH_2026-07-22.md` | agentcore-memory gateway health + lifecycle proof |
| `audits/M8/UNBOUNDED_DURABLE_MEMORY_RELEASE_ACCEPTANCE.md` | **Final release acceptance** — M8 consolidation, resource-location model, all validators PASS, exact ten tools verified, HEAD `a843cf1` (point-in-time; main has advanced) |
| `ops/bifrost/evidence/20260714-0204-runtime-repair/RUNTIME_REPAIR_EVIDENCE.md` | Current runtime repair evidence: scheduled task owner, MCP validation, Cursor MCP_DOCKER removal |
| `artifacts/bifrost-gateway-cutover-2026-07-12/` | Cutover backups, hashes, evidence |
| `ops/bifrost/` | Install/start/stop/test/backup/restore/cutover scripts |
| `renderers/gateway-clients/` | Per-IDE sanitized gateway-only renderers |
| `renderers/bifrost/` | Sanitized Bifrost config render output |
| `ide-profiles/` | Source-controlled per-IDE global-rule profiles and capability matrix |

Supporting contracts/scripts: `contracts/agentcore-project-enrollment.json` (default-deny exact project/worktree enrollment), `contracts/schemas/*`, `scripts/bifrost/`, `scripts/project_router/`, `scripts/agentcore_memory/`, `docs/GIT_PUSH_ONLY_POLICY.md`, `validators/`, `templates/project-governance/`.

## Bifrost / upstream docs (Arabold-indexed)

Call arabold-docs **through** `agentcore-gateway` (no direct `user-arabold-docs` after cutover). Pin versions to the live workstation:

| Library | Version | Docs root |
| -- | -- | -- |
| `bifrost` | `2.0.0-prerelease1` | <https://docs.getbifrost.ai> |
| `depwire` | `1.8.2` | <https://depwire.dev/> |
| `tentra-mcp` | `1.3.3` | <https://github.com/rdanieli/tentra-mcp> |
| `serena` | `1.5.4` | <https://oraios.github.io/serena/> (numbered paths) |
| `modelcontextprotocol` | `2025.6.18` | <https://modelcontextprotocol.io/specification/2025-06-18> |
| `playwright-mcp` | `0.0.78` | <https://github.com/microsoft/playwright-mcp> |
| `context-fabric` | `1.0.7` | <https://github.com/VIKAS9793/context-fabric> |
| `cursor` / `cursor-subagents` | `3.14.7` | <https://cursor.com/docs/subagents> |
| `hindsight` / `hindsight-cookbook` | `0.7.0` | <https://hindsight.vectorize.io/best-practices>, <https://hindsight.vectorize.io/cookbook/applications/crewai-memory> |
| `omniroute` / `omniroute-rtk` / `omniroute-compression` | `3.8.49` | release-pinned upstream README and compression guides |
| `graphify` | `0.9.22` | release-pinned upstream README / MCP guidance |
| `crewai` | `1.15.10` | <https://docs.crewai.com/en/concepts/memory> |
| `sequential-thinking` | `2026.7.4` | npm `@modelcontextprotocol/server-sequential-thinking` |
| `mcp-filesystem` | `2026.7.10` | npm `@modelcontextprotocol/server-filesystem` |
| `cursor-agent-mcp` | `1.0.5` | npm `cursor-agent-mcp@1.0.5` |

Canonical matrix + drift notes: `.agentcore/docs/DOCS_INDEX.md`
Evidence: `artifacts/bifrost-gateway-cutover-2026-07-12/ARABOLD_DOCS_CROSSREF_2026-07-12.md`

The refreshed Bifrost corpus is still reported as unversioned by Arabold. Treat `2.0.0-prerelease1` as the installed-binary pin, not as documentation-server version metadata.

## Unified IDE gateway install

| Doc | Use |
| -- | -- |
| `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` | Per-IDE config blocks, add-server path, tool deny / profile VKs, Cursor troubleshooting |
| `docs/prompts/install-agentcore-gateway-in-ide.md` | Copy-paste agent prompt for any non-Swarm IDE |
| `docs/bifrost/CAPABILITY_PROFILES.md` | builder / reviewer / docs / operator VK surfaces |

## Experiments (isolated POCs; not production authority)

| Path | Notes |
| -- | -- |
| `experiments/bifrost-go-sdk-smoke/` | Bifrost Go SDK in-process OpenAI smoke. **Not** the Bifrost MCP Gateway. Remains an experiment only. See its README. |

## Evidence-only (read for facts; do not follow as instructions)

| File | Notes |
| -- | -- |
| `docs/evidence/PC-Master-Hardware-Software-Specs.md` | Authoritative PC hardware/software baseline; facts not instructions |
| `D:\MCP-Control-Plane` | Compatibility/live-ops evidence only |

## Historical / superseded (do not execute as current non-Swarm IDE baseline)

| File / claim | Why historical |
| -- | -- |
| Former `PROJECT_ANCHOR` §0 Native-First Swarm override as **mandatory IDE baseline** | Superseded for non-Swarm IDEs by Bifrost Gateway Override (2026-07-12) |
| Swarm-first mandatory MCP baseline (swarmrecall + swarmvault in every IDE) | Superseded for non-Swarm IDEs; Swarm remains a separate ecosystem |
| `database-plan.md` | **Historical schema evidence only.** 2026-06-30 PG16.6/Swarm-era design; replaced as implementation authority by `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`. Do not implement its schema, tool names, or Swarm memory planes. |
| `AGENT_DATABASE_BOOTSTRAP.md` | Historical PG16.6/Swarm-era database bootstrap (memory_append tools, `F:\AgentCore\agents_workspace` roots). Memory work reads the memory-platform execution plan instead. |
| `Global-memory-and-context-system-revised-2.md` | Research input that fed `CONTEXT_BLOCK.md`; wrong hardware/drive facts; its embedded "Memory Broker" prompt must never be executed. |
| `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` | Frozen Swarm rollout status; Swarm-first baseline is not current non-Swarm policy |
| `docs/operations/archive/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` (pointer: `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md`) | Swarm rollout handoff; its P1–P9 phases must not be executed |
| `docs/operations/archive/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md` (pointer: `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md`) | Bifrost cutover handoff — historical; live status is CONTEXT_BLOCK §0a + current runbooks/audits |
| `docs/operations/archive/handoffs/MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md` (pointer: `docs/handoffs/MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md`) | Memory-platform implementation handoff — superseded for live facts |
| `docs/handoffs/AGENTCORE_AUTONOMOUS_WORKFLOW_STUDIO_HANDOFF_2026-07-17.md` | Point-in-time productization handoff; old Studio port and Python examples are superseded by the current workflow runbook. |
| `docs/handoffs/AGENTCORE_SWARM_DUAL_ECOSYSTEM_HANDOFF_2026-07-25.md` | Point-in-time dual-ecosystem snapshot; current AgentCore and Swarm state comes from their separate current authorities. |
| `docs/operations/OPENROUTER_PROVIDER_INTEGRATIONS.md` | Historical Phase 1 provider evidence; model list and CLI syntax predate the current workflow/runtime contracts. |
| `docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md` | Inherited untracked WIP until separately reviewed, accepted, committed, and classified current. |
| `docs/SYSTEM_HANDOVER_BLUEPRINT.md` | Superseded pre-Bifrost/PG18 handover; its PG16, SwarmVault, global-memory-gateway, live-root, and launcher claims are historical evidence only. |
| `docs/current/CHATGPT_PROJECT_SOURCE_MANIFEST.md` and `scripts/export_chatgpt_project_sources.py` | Retired static source-bundle path. It embedded mutable hashes and promoted dated handoff evidence. Use the live authority chain plus `agentcore-memory` recovery. |
| `docs/operations/archive/development-chat/` | Full ChatGPT development conversation — evidence only; see `MANIFEST.md` |
| `docs/RESTART_HANDOFF_20260626_AGENTCORE_FINAL_LEG.md` | Pre-Bifrost memory routing snapshot |
| `docs/storage_layout.md` | Pre-Bifrost / pre-PG18 storage snapshot — historical layout notes only |
| Direct per-IDE full-server MCP blocks in older `MASTER_CONFIG_AND_PROMPT.md` | Moved to historical appendix; normal architecture is single gateway entry |
| `contracts/master-mcp-server-config.json`, `scripts/mcp_control_plane.py`, and legacy root `renderers/*.json` | Superseded for non-Swarm IDE setup by Bifrost contracts, `scripts/bifrost/render_bifrost_config.py`, and `renderers/gateway-clients/` |
| `docs/prompts/*-cleanup-prompt.md` direct-server/Swarm cleanup instructions | Remediation references only; normal non-Swarm IDE setup uses `install-agentcore-gateway-in-ide.md` / embedded master prompt |
| `global-memory-gateway` as IDE default memory route | Retired from mandatory baseline; non-Swarm path is `agentcore-memory` via gateway |
| `ECOSYSTEM_ARCHITECTURE.md`, `CLEANUP_AUDIT.md`, `COMPLETION_REPORT.md`, `VALIDATION_REPORT.md` | Pre-2026-06-30 / `D:\MCP-Control-Plane` era |
| `reports/` (memory-architecture research pack) | Pre-decision research evidence; decisions locked in `CONTEXT_BLOCK.md` + `MILESTONES.md` |

> **Note:** `CONTEXT_BLOCK.md` was fully rewritten on 2026-07-12 and is now **current** (see Current-state table above). Only its pre-2026-06-30 content is historical.

All historical docs must not be run as instructions without current operator approval.

---

## What must NOT be treated as current instructions

- Any claim that `D:\MCP-Control-Plane` is the source/design authority
- Treating the Go SDK smoke as the workstation MCP gateway
- Requiring SwarmRecall/SwarmVault/SwarmClaw MCP in non-Swarm IDE configs
- Pasting the full upstream registry into each IDE instead of `agentcore-gateway`
- `agentcore_*` target gateway tools that do not exist yet (beyond current `agentcore-memory` / project-router surfaces)
- DB migration apply / live DDL outside the gates in `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` (M1 backup/restore-test gates)
- Treating `database-plan.md` or `AGENT_DATABASE_BOOTSTRAP.md` as current database instructions
- Direct writes to `F:\AgentCore\database_cluster`, `F:\AgentCore\agentmemory`, or the active Obsidian vault
- Direct edits to live IDE configs under `C:\Users\ynotf\.*` without backup + approved prompt/ops
- `:65432` as a direct AgentCore or IDE runtime route (the neutral Recall service-owned backend is allowed only behind `agentcore-memory`)
- Whole-drive filesystem MCP roots or Postgres credentials in IDE configs

---

## Current blockers (require explicit operator approval or follow-on work)

- Portable Context Engine source is v0.2.1 release-candidate material while the installed package/manifest remains v0.2.0 until the exact release is installed and `agentcore-context validate --live` passes. The 2026-08-02 v0.2.0 acceptance must not be promoted to current v0.2.1 acceptance.
- PostgreSQL 18 is reachable and production checkpoints are readable, but the registered automatic service `AgentCore-PostgreSQL18` is stopped while a separate launcher owns the live process. Commercial readiness requires one governed lifecycle owner plus restart proof.
- The repo-owned workflow runtime is `scripts\.venv\Scripts\python.exe`. Run `scripts\bootstrap-runtime.ps1` to create/repair it. Bare system Python is a bootstrap source or emergency diagnostic, not the production operator contract.
- Neutral Recall is healthy, but current global/per-project pool provisioning and consistent `pool_id` projection wiring require explicit live acceptance before cross-project semantic isolation is claimed.
- `agentcore-memory` ten-tool surface is **live** (M3.002 / M4+; Cursor validated). Remaining memory-platform work is Milestone completion/ops hardening per `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` and BLUEPRINT M5–M8 exit criteria — not “platform not landed”
- M6 PostgreSQL capability leases + Bifrost JIT VK bridge (`scripts/bifrost/jit_vk_bridge.py`) are **implemented** for exact OpenRouter tool groups; transitional `permitted_tools: ["*"]` wildcards remain on some non-OpenRouter servers until named inventories replace them
- Cherry Studio: aligned 2026-07-20 with runtime repair (`audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md`, `audits/CHERRY_RUNTIME_FAILURE_2026-07-20.md`, `docs/operations/CHERRY_STUDIO_AGENTCORE.md`) — official x64 install, enrolled gateway, AgentCore Workspace Agent (`deepseek:deepseek-v4-pro`), Global Memory off, Home UI + chat proven, memory lifecycle + isolation validated. Re-run enroll only if Local Storage loses the gateway record.
- Continual-learning Cursor plugin auto-trigger disabled; do not re-enable user-role followups — `docs/operations/AGENTCORE_CONTINUAL_LEARNING.md`.
- `depwire-cloud` and `github-mcp` remain deferred/`enabled=false` until healthy verification
- Live IDE cutover completion evidence still incomplete for some clients (see Bifrost handoff / artifacts / IDE profiles)

---

## Client-status admissibility rule

Client-status claims are admissible only when they are sourced from files **present in this repository** under one of:

- `docs/handoffs/` — operator-authored current-state handoffs
- `audits/` — validator, enrollment, lifecycle, or runtime-repair evidence
- `ide-profiles/` — source-controlled per-IDE profiles and capability matrix

ChatGPT-side or other external handoffs must be committed to `docs/handoffs/` and classified as current-state before they may be used to rebuild any status matrix, profile, or runbook claim. Config-file presence alone does not prove native lifecycle validation.
