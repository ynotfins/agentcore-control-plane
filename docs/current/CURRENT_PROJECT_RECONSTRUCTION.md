# CURRENT_PROJECT_RECONSTRUCTION.md

**Document type:** Current-state synthesis (evidence reconstruction)  
**Not architecture authority.** This file does not override the locked authority chain.  
**Synthesized:** 2026-07-20  
**Git boundary:** `main` @ `794d9725d0772cb4cf266e96b107e02275e2bf57` (reconstruction baseline); live HEAD may advance after this file.  
**Runtime probes:** 2026-07-20 (Bifrost OPTIONS 200; PG18 service Running; `agentcore-memory` `memory_status` healthy)

---

## Preamble — authority and evidence rules

1. **`PROJECT_ANCHOR.md` and `BLUEPRINT.md` remain higher authority** than this synthesis.
2. **`CONTEXT_BLOCK.md` remains the mutable current-state authority** (especially §0a). This file is the long-form evidence synthesis; it does not replace `CONTEXT_BLOCK.md`.
3. **Machine-readable contracts and validators** beat narrative docs for exact gateway/tool state.
4. **The archived ChatGPT development conversation is evidence only.** It must not override the authority chain. Coverage method and integrity: `docs/operations/archive/development-chat/MANIFEST.md`.
5. **Cursor completion reports and chat claims** are not verified until Git, audits, validators, or runtime probes corroborate them.
6. Distinguish: repository evidence, Git evidence, runtime evidence, conversation-reported evidence, inference, unresolved.

Read order remains:

```text
PROJECT_ANCHOR.md
  > DOC_AUTHORITY.md
  > BLUEPRINT.md
  > CONTEXT_BLOCK.md (§0a for live posture)
  > docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md
  > contracts / runbooks / newest verified audits
  > this reconstruction (synthesis)
  > archived chat (evidence only)
```

---

## 1. Executive Current State

The non-Swarm AgentCore platform is **live and operational** behind one Bifrost gateway.

| Layer | Current fact | Classification |
| --- | --- | --- |
| IDE front door | `agentcore-gateway` → `http://127.0.0.1:8080/mcp` | verified live |
| Memory identity | `agentcore-memory` v0.6.0, exact 10 tools | verified live |
| Canonical DB | PG18 `127.0.0.1:55433`, migrations m2–m8 incl. m3.002 | verified live |
| PG16 `:55432` | Rollback/legacy/Swarm; often not listening | historical / rollback role |
| M0–M8 | Exit evidence PASSED in `audits/M{1–8}/` + M8 release acceptance | implemented and validated (acceptance HEAD `a843cf1`; main has advanced) |
| OpenRouter MCP | Registry `status: dormant`; lifecycle `authenticated_dormant`; JIT leases | implemented and validated |
| Cherry Studio | Gateway enrolled; AgentCore Workspace Agent mounted; memory lifecycle + isolation validated 2026-07-20 | verified live (`audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md`) |
| Cursor | Gateway enrolled; ten-tool surface live-validated | verified live |

**Bottom line:** Architecture and Milestones M0–M8 are done for the memory/workflow platform. Remaining work is **ops/docs/client enrollment reconciliation**, not redesign.

---

## 2. Evidence and Authority Map

```text
PROJECT_ANCHOR.md          constitution (stable)
  > DOC_AUTHORITY.md       hierarchy + classification
  > BLUEPRINT.md           locked architecture + M0–M8 exit criteria
  > CONTEXT_BLOCK.md §0a   mutable live posture (2026-07-20)
  > MEMORY_PLATFORM_EXECUTION_PLAN.md  detailed execution (BLUEPRINT wins)
  > machine-readable contracts/manifests
  > validators / runtime probes
  > audits / handoffs (newest dated for live topic status)
  > archived ChatGPT conversation (evidence only)
```

Machine facts: `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md` (hardware/software identity). Latest ChaosCentral runtime snapshot at reconstruction time was `PC_RUNTIME_SNAPSHOT_20260716-003753` — **stale relative to 2026-07-20 OpenRouter/Cherry work**; do not use it for live MCP claims.

---

## 3. Canonical Architecture

Locked in `BLUEPRINT.md` §§2–3 / `PROJECT_ANCHOR.md` §0:

```text
Non-Swarm IDEs
  -> agentcore-gateway (127.0.0.1:8080/mcp)
       -> agentcore-memory (10 tools) -> PostgreSQL 18 + pgvector + Cognee adapter + projections
       -> other upstream MCPs (profiles)
       -> openrouter (dormant; tools only via M6 lease + JIT VK bridge)
  LangGraph production: PostgresSaver on PG18; Studio = localhost/dev-only
```

- PostgreSQL is canonical; Markdown projections are generated; Cognee is non-canonical; Mem0 is not installed for v1.
- COMB / Distill / Lossless Claw = reference patterns only (`BLUEPRINT.md` §3).
- Deep Agents = bounded worker harness inside LangGraph nodes only (`docs/decisions/ADR-DEEP-AGENTS-WORKER-HARNESS.md`).

---

## 4. Current Runtime and Tool Topology

| Component | Evidence | Status |
| --- | --- | --- |
| Bifrost pin v2.0.0-prerelease1 | `PROJECT_ANCHOR.md` §0; scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` | verified live |
| Gateway contract | `contracts/agentcore-gateway-client.json` | locked architecture |
| Upstream registry | `contracts/bifrost-upstream-mcp-registry.json` | exact tool state |
| agentcore-memory tools | `memory_status` … `docs_search` (10) | verified live |
| Cognee | `memory_status`: available, backend cognee | verified live |
| LangGraph | `m6_integrated`; `public.checkpoints*` + `agentcore.wf_*` | verified live |
| OpenRouter MCP | `status: dormant`, `enabled: true`, 18 permitted / 2 denied | implemented and validated |
| Transitional wildcards | registry `tool_lifecycle_note` | partially implemented (documented exception) |

Exact ten `agentcore-memory` tools (`PROJECT_ANCHOR.md` §5):

`memory_status`, `startup_context`, `retrieve_context`, `append_event`, `propose_fact`, `expand_source`, `session_open`, `session_close`, `build_handoff`, `docs_search`

---

## 5. Git and Implementation Chronology

**Canonical checkout:** `D:\github\agentcore-control-plane` on `main`.  
**Secondary worktree:** `D:\AgentSwarm\runs\agentcore-memory-v1\worktree` on stale `ai/global-memory-platform-v1` — reconcile before reuse (`CONTEXT_BLOCK.md` §1).  
**Remote:** `origin` → `https://github.com/ynotfins/agentcore-control-plane.git`.

| Era | Commits | What landed |
| --- | --- | --- |
| Bifrost cutover | `f429801`… | Single gateway, authority rewrite |
| BLUEPRINT / M0 | `b427a2e` (2026-07-14) | Locked blueprint |
| M1–M5 | through `47677bb` / `4ca6954` | PG18, evidence, context, gateway, Cognee |
| M6–M7–M8 | `7825207` → `c7894bc` → `5c999c1` / `a843cf1` | Workflow, knowledge, cutover acceptance |
| M3.002 live | `e07708d`…`0953673` | Unbounded durable memory v0.6.0 |
| Studio productization | `7865ee5` | Workflow CLI + Studio runbook |
| Continuity | `fc3fb16` | Durability audits |
| OpenRouter dormant | `96c2528`…`74e1361` | Registry dormant scaffold |
| OpenRouter bind + JIT | `69f9ac6`…`7574e5b` / `f843b97` | OAuth bind, classification, VK bridge |
| Docs reconcile | `794d972` | Authority/docs vs live 2026-07-20 wiring |

**Chat ending vs Git (critical supersession):** Archived chat final status said OpenRouter OAuth pending. **Git + audits win:** lifecycle `authenticated_dormant` (`f843b97`, `docs/operations/OPENROUTER_MCP.md`, `audits/OPENROUTER_MCP_OAUTH_BIND_2026-07-20.md`).

---

## 6. Memory, Context, and Evidence System

- Ten-tool surface locked; live via Bifrost.
- Immutable evidence + compaction without deleting originals; exact expansion via `expand_source`.
- Generated projections: `C:\Users\ynotf\.agentcore\GLOBAL_STATE.md`, `<project>\.agentcore\STATE.md`, etc.
- Project `.agentcore/STATE.md` may show milestone label `gated-integration-recovery` — projection wording, **not** a claim that M0–M8 are unfinished.
- Treat `agentcore-memory` retrieval as corroborating chronology; repo audits win for live client enrollment facts when they conflict.

---

## 7. LangGraph Workflow State

- CLI: `python -m agentcore workflow {init,start,status,pause,approve,reject,resume,cancel,logs,evidence,topology,studio}`
- Runbook: `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
- Production: PostgresSaver @ PG18; Studio: localhost/dev-only, `LANGSMITH_TRACING=false`, isolated checkpointer
- Shared MCP: `scripts/agentcore_workflow/mcp_client.py` → localhost gateway (`audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md`)

---

## 8. Capability Profiles and Lease Model

- Profiles: builder / reviewer / database-validator / docs-knowledge / operator — `docs/bifrost/CAPABILITY_PROFILES.md`
- M6 PostgreSQL leases + `scripts/bifrost/jit_vk_bridge.py` grant exact OpenRouter tool groups
- Zero OpenRouter tools without an active lease (expected default)
- Transitional `permitted_tools: ["*"]` remains on some non-OpenRouter servers

---

## 9. OpenRouter MCP versus OpenRouter API

| Aspect | MCP (tools) | API (inference) |
| --- | --- | --- |
| Endpoint | `https://mcp.openrouter.ai/mcp` via Bifrost | `https://openrouter.ai/api/v1` |
| Auth | OAuth in Bifrost `config.db` | `OPENROUTER_API_KEY` (and client-specific keys) |
| IDE exposure | Zero until M6 lease + JIT | Configured per client as LLM provider |
| Registry | `status: dormant` | N/A |
| Lifecycle | `authenticated_dormant` when OAuth bound | N/A |
| Completion claim | `OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY` | Separate model-selection proofs |

**Vocabulary:** registry `status: dormant` ≠ lifecycle `authenticated_dormant`. See `docs/operations/OPENROUTER_MCP.md`.

---

## 10. IDE Enrollment Status

| Client | Status | Evidence |
| --- | --- | --- |
| Cursor | live_validated | M8 exit + live gateway |
| Codex | configured_restart_required | M8 matrix |
| Claude Code/Desktop, MiniMax, Antigravity, Mavis, Open Interpreter | awaiting_operator_import or restart | M8 matrix / DOC_AUTHORITY blockers |
| Cherry Studio | gateway active in store (2026-07-20 evening) | `audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md` |
| LangGraph | gateway client enrolled | `audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md` |

---

## 11. Storage and Machine Placement

| Drive | Role |
| --- | --- |
| C: | OS / live IDE configs |
| D: | Canonical repos (`D:\github\agentcore-control-plane`) |
| E: | Cold archive / backups |
| F: | PG18 hot data (`F:\PostgreSQL18\data`); PG16 path legacy |
| G: | Backup target |
| H: | Bifrost / AgentRuntime (`H:\AgentRuntime\bifrost`) |
| I: | Scratch |
| J: | Portable |

Forbidden: `:65432` active route; whole-drive FS MCP; Postgres credentials in IDE configs; `.env` secret files.

---

## 12. Swarm Exclusion Boundary

SwarmRecall / SwarmVault / SwarmClaw are a **separate ecosystem**. Non-Swarm IDEs must not require Swarm MCP (`PROJECT_ANCHOR.md` §0/§7). Swarm rollout handoff is historical only and must not be executed.

---

## 13. M0–M8 Evidence Matrix

| Milestone | Exit evidence | Classification |
| --- | --- | --- |
| M0 | BLUEPRINT install `b427a2e` | implemented and validated |
| M1 | `audits/M1/M1-EXIT-EVIDENCE.md` PASSED | implemented and validated |
| M2 | `audits/M2/M2-EXIT-EVIDENCE.md` PASSED | implemented and validated |
| M3 / M3.002 | M3-EXIT + live rollout handoff | implemented and validated |
| M4 | M4-EXIT PASSED; 10 tools live | verified live |
| M5 | M5-EXIT PASSED; Cognee available | verified live |
| M6 | M6-EXIT PASSED + Studio runbook; leases live | implemented and validated |
| M7 | M7-EXIT 19/19 | implemented and validated |
| M8 | M8-EXIT + `audits/M8/UNBOUNDED_DURABLE_MEMORY_RELEASE_ACCEPTANCE.md` @ `a843cf1` | implemented and validated; non-Cursor enrollment ops remain |

---

## 14. Handoff Classification Matrix

| Handoff | Class | Disposition |
| --- | --- | --- |
| Bifrost gateway 2026-07-12 | Historical cutover evidence | Archived under `docs/operations/archive/handoffs/` with pointer stub |
| Memory-platform implementation 2026-07-14 | Historical implementation (superseded for live facts) | Archived with pointer stub |
| Swarm rollout 2026-06-30 | Swarm-only historical | Archived with pointer stub |
| Full recovery source 2026-07-16 | Topic-specific source evidence | Keep in `docs/handoffs/` |
| Full recovery live rollout 2026-07-17 | Live rollout evidence (M3.002) | Keep in `docs/handoffs/` |
| Autonomous workflow / Studio 2026-07-17 | Topic handoff; prefer runbook for commands | Keep in `docs/handoffs/` |
| OpenRouter OAuth bind 2026-07-20 | Current topic handoff | Keep in `docs/handoffs/` |

Active topic handoffs for agents: OpenRouter bind, Full Recovery Live, Autonomous Workflow (prefer runbook), Full Recovery Source.

---

## 15. Root/Docs Classification (selected)

- Constitutional / locked: `PROJECT_ANCHOR.md`, `BLUEPRINT.md`, `DOC_AUTHORITY.md`, `AGENTS.md`, `CLAUDE.md`
- Current mutable: `CONTEXT_BLOCK.md` (§0a wins over Phase checklists)
- Current ops runbooks: `docs/operations/OPENROUTER_MCP.md`, `AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, `DORMANT_MCP_CAPABILITY_CATALOG.md`
- Historical / superseded (banners present): `AGENT_DATABASE_BOOTSTRAP.md`, `database-plan.md`, Swarm context, research essays, pre-Bifrost MCP refs
- `docs/storage_layout.md`: historical snapshot — banner added 2026-07-20

---

## 16. Supersession Ledger

| Topic | Earlier | Later / current | Winner | Confidence |
| --- | --- | --- | --- | --- |
| Canonical repo | MCP-Control-Plane / memory-context-database | `D:\github\agentcore-control-plane` | PROJECT_ANCHOR | high |
| Gateway | Portkey / UTCP / direct MCP | Bifrost single gateway | constitution + Git | high |
| Memory IDE route | global-memory-gateway / Swarm MCP | agentcore-memory via gateway | constitution 2026-07-12 | high |
| PostgreSQL | PG16 `:55432` canonical | PG18 `:55433` | PROJECT_ANCHOR 2026-07-17 + live | high |
| Mem0 vs Cognee | debate | Cognee v1; no Mem0 | BLUEPRINT | high |
| Deep Agents | possible authority | Bounded harness only | ADR + BLUEPRINT | high |
| OpenRouter OAuth | chat end: pending | authenticated_dormant | audits `f843b97`+ | high |
| Cherry enrolled | memory Gate C pass | store may be empty; re-enroll | CHERRY audit / enroll ops | high |
| M8 “final HEAD” | acceptance `a843cf1` | main advanced (`794d972`+) | Git HEAD for current; acceptance for M8 gate | high |
| Leases | “until M6” framing | leases + JIT live | CONTEXT_BLOCK §0a + registry | high |

---

## 17. Contradictions and Document Drift (resolved or recorded)

1. DOC_AUTHORITY Current-state vs historical handoff labels — **reconciled 2026-07-20** (this pass).
2. OpenRouter handoff registry status vocabulary — **fixed 2026-07-20**.
3. Chat final OpenRouter OAuth-pending claim — **superseded** by Git/audits.
4. Memory Cherry “enrolled” events vs empty live store — **ops gap**; enroll when empty.
5. CONTEXT_BLOCK Phase 0–10 incomplete wording — do not misread; §0a wins.
6. STATE.md milestone label lag — not architecture rewind.
7. ChaosCentral runtime snapshot stale for 2026-07-20 MCP facts — recorded.
8. Archived chat previously untracked — now under `docs/operations/archive/development-chat/` with MANIFEST.

---

## 18. Remaining Work and Blockers

**Operator-gated / live:**

- Cherry Studio: if `mcp.servers=[]`, quit Cherry → `python scripts/cherry/enroll_agentcore_gateway.py`
- Complete non-Cursor IDE cutover evidence (M8 matrix)
- Optional PG16 start only for Swarm/rollback needs

**Docs/governance:**

- Broader dormant MCP catalog implementations still pending (`docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md`)
- Replace transitional wildcards with named inventories over time
- Inherited Studio-interrupt / Cherry WIP: see `audits/INHERITED_WIP_DISPOSITION_2026-07-20.md` — keep separate from authority commits

**Do not treat as remaining platform build:** redesign Bifrost/Portkey, rebuild PG18, re-decide Cognee, re-open Swarm-in-IDE baseline.

---

## 19. Safest Next Steps After This Document

1. Keep `CONTEXT_BLOCK.md` §0a updated when live posture changes.
2. Finish or discard Studio-interrupt WIP in a **separate** task/commit from authority docs.
3. Refresh ChaosCentral runtime snapshot when operator wants machine-fact currency for MCP.
4. Continue progressive enrollment evidence for non-Cursor IDEs.

---

## 20. Related artifacts

- Chat archive MANIFEST: `docs/operations/archive/development-chat/MANIFEST.md`
- Dirty WIP disposition: `audits/INHERITED_WIP_DISPOSITION_2026-07-20.md`
- OpenRouter runbook: `docs/operations/OPENROUTER_MCP.md`
- Workflow runbook: `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
