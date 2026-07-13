# Document Authority Index — AgentCore Control Plane

**Source authority:** `D:\github\agentcore-control-plane`  
**Compatibility/live-ops evidence only:** `D:\MCP-Control-Plane`  
**Updated:** 2026-07-12

This file is the document hierarchy. It tells a new agent what to read, what is authoritative, and what must not be followed as current instructions.

---

## What to attach to a new chat

**Minimum (always attach):**
1. `PROJECT_ANCHOR.md` — immutable project constitution
2. `DOC_AUTHORITY.md` — this hierarchy
3. `database-plan.md` — finalized schema/gateway design authority
4. `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` — current rollout state
5. `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` — self-contained handoff

**Add as needed:**
- `artifacts/rollout-2026-06-30/NATIVE_FIRST_STABILIZATION_FOLLOWUP.md` — latest concise current-state follow-up
- `artifacts/incident-2026-06-30/reconciliation-report.md` — post-incident continuation
- `artifacts/rollout-2026-06-30/ROLLOUT_REPORT.md` — full acceptance review
- `docs/evidence/PC-Master-Hardware-Software-Specs.md` — hardware/software facts
- `SECURITY.md` — secret/security policy
- `docs/prompts/<ide>-cleanup-prompt.md` — only the prompt for the IDE being executed

---

## Authoritative — stable (safe to follow; change rarely, with approval)

| File | Purpose |
|------|---------|
| `PROJECT_ANCHOR.md` | Immutable project constitution: authority, drives, endpoints, memory path, baseline, forbidden routes, hard gates |
| `MASTER_CONFIG_AND_PROMPT.md` | Controlling IDE MCP/rules setup baseline + verified canonical launchers (§4a) + per-IDE prompts |
| `database-plan.md` | Finalized schema/gateway design spec (does not authorize live DDL) |
| `SECURITY.md` | Secret and security policy |
| `AGENTS.md` | Source-controlled agent operating contract (points to the anchors) |

## Current-state — mutable (accurate now; updated as the rollout progresses)

| File | Purpose |
|------|---------|
| `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` | Current rollout state, acceptance results, blockers, next actions |
| `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` | Primary next-agent handoff |
| `artifacts/rollout-2026-06-30/NATIVE_FIRST_STABILIZATION_FOLLOWUP.md` | Latest concise current-state follow-up (native-first status) |
| `artifacts/incident-2026-06-30/reconciliation-report.md` | P0 incident reconciliation findings |
| `artifacts/rollout-2026-06-30/ROLLOUT_REPORT.md` | Rollout implementation evidence and acceptance state |

Supporting current/source-controlled references: `contracts/master-mcp-server-config.json`, `contracts/global-memory-database-contract.json`, `AGENT_DATABASE_BOOTSTRAP.md`, `docs/GIT_PUSH_ONLY_POLICY.md`, `swarmvault.schema.md`, `migrations/` (dry-run only), `validators/validate-control-plane.ps1`, `ops/Test-AgentCore*.ps1`, `docs/prompts/`.

## Experiments (isolated POCs; not production authority)

| Path | Notes |
|------|-------|
| `experiments/bifrost-go-sdk-smoke/` | Bifrost Go SDK (`core@v1.7.0`) in-process OpenAI smoke. **Not** the Bifrost MCP Gateway. See its README. |

## Evidence-only (read for facts; do not follow as instructions)

| File | Notes |
|------|-------|
| `docs/evidence/PC-Master-Hardware-Software-Specs.md` | Authoritative PC hardware/software baseline; facts not instructions |

## Historical-only (do not execute; not current authority)

| File | Why historical |
|------|----------------|
| `ECOSYSTEM_ARCHITECTURE.md` | `D:\MCP-Control-Plane` ecosystem audit, 2026-06-20; paths/authority superseded |
| `CLEANUP_AUDIT.md` | `D:\MCP-Control-Plane` cleanup evidence, 2026-06-20 |
| `COMPLETION_REPORT.md` | `D:\MCP-Control-Plane` audit completion, 2026-06-20 |
| `VALIDATION_REPORT.md` | Initial bootstrap validation, 2026-06-24; superseded by current docs/validators |
| `CONTEXT_BLOCK.md` | Earlier (2026-06-28) rollout context block; superseded by `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` |

All historical docs carry a warning banner. Do not run commands from them without current operator approval.

---

## What must NOT be treated as current instructions

- Any claim that `D:\MCP-Control-Plane` is the source/design authority, or any `D:\MCP-Control-Plane\...` edit target
- `agentcore_*` target gateway tools (do not exist yet; only `memory_append`/`memory_search`/`memory_state` are current)
- DB migration apply without the full gates in `database-plan.md §13`
- Any command from `CLEANUP_AUDIT.md`, `COMPLETION_REPORT.md`, or `ECOSYSTEM_ARCHITECTURE.md` without re-evaluation
- Direct writes to `F:\AgentCore\database_cluster`, `F:\AgentCore\agentmemory`, `F:\VectorDB`, or the active Obsidian vault
- Direct edits to live IDE configs under `C:\Users\ynotf\.*`
- `:65432` as an active runtime route (retired; use `:55432`)
- `no_fetch://push-only` remote posture (removed; normal GitHub remotes now, no pull/fetch without explicit user request)

---

## Current blockers (require explicit operator approval)

- Live IDE cleanup prompts run per IDE, starting with Claude Code (`CONTEXT7_API_KEY` rotation)
- DB migration apply: backup + dry-run + operator sign-off
- Scheduled-task de-registration of removed monitors: elevated shell
- SwarmVault query validator: interactive isolation before relying on `Test-AgentCoreSwarmVault.ps1`
