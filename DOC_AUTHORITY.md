# Document Authority Index — AgentCore Control Plane

**Source authority:** `D:\github\agentcore-control-plane`  
**Compatibility/live-ops evidence only:** `D:\MCP-Control-Plane`  
**Updated:** 2026-06-30

This file tells a new agent exactly what to read, what is authoritative, and what must not be followed as current instructions.

---

## What to attach to a new chat

Minimum required reads for a rollout-continuation agent:

1. `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` — self-contained handoff; start here
2. `database-plan.md` — finalized schema/gateway design authority
3. `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` — current rollout state, runtime wiring, blockers, next steps
4. `AGENTS.md` — operating rules and tool routing

For specific phases:
- `artifacts/incident-2026-06-30/reconciliation-report.md` — P0 incident findings
- `artifacts/rollout-2026-06-30/ROLLOUT_REPORT.md` — implementation evidence and acceptance state
- `docs/prompts/<ide>-cleanup-prompt.md` — only the prompt for the IDE being cleaned up

---

## Authoritative docs (safe to follow as current instructions)

| File | Purpose |
|------|---------|
| `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` | Primary next-agent handoff; self-contained runtime facts, phase list, blockers |
| `database-plan.md` | Finalized schema/gateway design spec (does not authorize live DDL) |
| `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` | Current rollout state, acceptance results, next actions |
| `AGENTS.md` | Source-controlled agent operating contract |
| `SECURITY.md` | Secret and security policy |
| `artifacts/incident-2026-06-30/reconciliation-report.md` | P0 incident reconciliation findings |
| `artifacts/rollout-2026-06-30/ROLLOUT_REPORT.md` | Rollout implementation evidence, validators, blockers |
| `contracts/master-mcp-server-config.json` | Canonical MCP server contract |
| `contracts/global-memory-database-contract.json` | Machine-readable DB/memory contract |
| `docs/prompts/` | Per-IDE cleanup prompts (use only inside the matching IDE) |
| `migrations/` | Authored migration SQL (dry-run only; apply requires backup + operator sign-off) |
| `validators/validate-control-plane.ps1` | Current source-state gate |
| `ops/Test-AgentCore*.ps1` | Current runtime validators |
| `AGENT_DATABASE_BOOTSTRAP.md` | Memory/database bootstrap contract with two-tier gateway |
| `docs/GIT_PUSH_ONLY_POLICY.md` | Git remote and pull/fetch policy |
| `swarmvault.schema.md` | AgentCore-specific SwarmVault vault schema and exclusions |
| `DOC_AUTHORITY.md` | This file |

---

## Evidence-only docs (useful context; do not follow as instructions)

| File | Notes |
|------|-------|
| `docs/evidence/PC-Master-Hardware-Software-Specs.md` | Authoritative PC hardware/software baseline; read for facts, not instructions |
| `CONTEXT_BLOCK.md` | Earlier rollout context block; superseded by `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` |

---

## Historical-only docs (do not execute; do not treat as current authority)

| File | Why historical |
|------|----------------|
| `ECOSYSTEM_ARCHITECTURE.md` | `D:\MCP-Control-Plane` ecosystem audit from 2026-06-20; paths and authority claims are superseded |
| `CLEANUP_AUDIT.md` | `D:\MCP-Control-Plane` cleanup evidence from 2026-06-20 |
| `COMPLETION_REPORT.md` | `D:\MCP-Control-Plane` audit completion from 2026-06-20 |
| `VALIDATION_REPORT.md` | Initial bootstrap validation pass from 2026-06-24; superseded by current validators and handoff |

All historical docs have a warning banner at the top. Do not run commands from them without current operator approval.

---

## What must not be treated as current instructions

- Any claim that `D:\MCP-Control-Plane` is the source authority or design authority
- Any path like `D:\MCP-Control-Plane\...` as a target for edits
- `agentcore_*` target gateway tools — these do not exist yet; only `memory_append`, `memory_search`, `memory_state` are confirmed current
- DB migration apply without the full gates in `database-plan.md §13`
- Any command from `CLEANUP_AUDIT.md`, `COMPLETION_REPORT.md`, or `ECOSYSTEM_ARCHITECTURE.md` without re-evaluation
- Direct writes to `F:\AgentCore\database_cluster`, `F:\AgentCore\agentmemory`, or active Obsidian vault
- Direct edits to live IDE configs under `C:\Users\ynotf\.*`
- `:65432` as an active runtime route (retired; use `:55432` only)

---

## Current blockers (require explicit operator approval)

- Live IDE cleanup prompts must be run per IDE, starting with Claude Code (`CONTEXT7_API_KEY` rotation)
- DB migration apply: backup + dry-run + operator sign-off required
- Scheduled-task de-registration of removed monitors: elevated shell required
- SwarmVault query validator: interactive isolation needed before relying on `Test-AgentCoreSwarmVault.ps1`
