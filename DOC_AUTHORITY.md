# Document Authority Index — AgentCore Control Plane

**Source authority:** `D:\github\agentcore-control-plane`
**Bifrost runtime:** `H:\AgentRuntime\bifrost` (not design authority)
**Compatibility/live-ops evidence only:** `D:\MCP-Control-Plane`
**Updated:** 2026-07-12 (Bifrost MCP Gateway cutover)

This file is the document hierarchy. It tells a new agent what to read, what is authoritative, and what must not be followed as current instructions.

---

## What to attach to a new chat

**Minimum (always attach):**
1. `PROJECT_ANCHOR.md` — immutable project constitution (includes Bifrost Gateway Override §0)
2. `DOC_AUTHORITY.md` — this hierarchy
3. `contracts/bifrost-upstream-mcp-registry.json` — canonical upstream MCP registry
4. `contracts/agentcore-gateway-client.json` — single IDE gateway client contract
5. `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md` — Bifrost cutover handoff
6. `docs/prompts/install-agentcore-gateway-in-ide.md` — reusable IDE install prompt

**Add as needed:**
- `MASTER_CONFIG_AND_PROMPT.md` — controlling IDE/gateway setup baseline after Bifrost rebuild
- `docs/adr/ADR-2026-07-12-bifrost-mcp-gateway.md` — deployment ADR
- `docs/adr/ADR-2026-07-12-configuration-source-of-truth.md` — config authority ADR
- `docs/bifrost/` — classification matrix, profiles, Tentra, Depwire, migration/rollback runbooks
- `database-plan.md` — schema/gateway design (DB platform; does not authorize live DDL)
- `docs/evidence/PC-Master-Hardware-Software-Specs.md` — hardware/software facts
- `SECURITY.md` — secret/security policy
- `artifacts/bifrost-gateway-cutover-2026-07-12/` — cutover evidence / backup manifest
- Historical Swarm rollout packs only when working **inside** the Swarm ecosystem

---

## Authoritative — stable (safe to follow; change rarely, with approval)

| File | Purpose |
|------|---------|
| `PROJECT_ANCHOR.md` | Immutable constitution: Bifrost gateway override, drives (incl. H/I/J), endpoints, memory path, baseline, forbidden routes |
| `MASTER_CONFIG_AND_PROMPT.md` | Controlling IDE MCP/rules setup after Bifrost rebuild |
| `contracts/bifrost-upstream-mcp-registry.json` | Canonical upstream MCP servers + capability profiles |
| `contracts/agentcore-gateway-client.json` | Single `agentcore-gateway` client connection contract |
| `docs/adr/ADR-2026-07-12-bifrost-mcp-gateway.md` | Why native Windows Bifrost Gateway, H: runtime, auth, pin |
| `docs/adr/ADR-2026-07-12-configuration-source-of-truth.md` | Contracts → renderer → H: live config; IDEs get gateway entry only |
| `docs/bifrost/*.md` | Classification, profiles, Tentra local mode, Depwire reconciliation, migration/rollback |
| `database-plan.md` | Finalized schema/gateway design spec (does not authorize live DDL) |
| `SECURITY.md` | Secret and security policy |
| `AGENTS.md` | Source-controlled agent operating contract |

## Current-state — mutable (accurate now; updated as cutover progresses)

| File | Purpose |
|------|---------|
| `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md` | Primary Bifrost gateway handoff |
| `artifacts/bifrost-gateway-cutover-2026-07-12/` | Cutover backups, hashes, evidence |
| `ops/bifrost/` | Install/start/stop/test/backup/restore/cutover scripts |
| `renderers/gateway-clients/` | Per-IDE sanitized gateway-only renderers |
| `renderers/bifrost/` | Sanitized Bifrost config render output |

Supporting contracts/scripts: `contracts/schemas/*`, `scripts/bifrost/`, `scripts/project_router/`, `scripts/agentcore_memory/`, `docs/GIT_PUSH_ONLY_POLICY.md`, `validators/`, `AGENT_DATABASE_BOOTSTRAP.md`.

## Bifrost / upstream docs (Arabold-indexed)

Call arabold-docs **through** `agentcore-gateway` (no direct `user-arabold-docs` after cutover). Pin versions to the live workstation:

| Library | Version | Docs root |
|---------|---------|-----------|
| `bifrost` | `2.0.0-prerelease1` | https://docs.getbifrost.ai |
| `depwire` | `1.8.2` | https://depwire.dev/ |
| `tentra-mcp` | `1.3.3` | https://github.com/rdanieli/tentra-mcp |
| `serena` | `1.5.4` | https://oraios.github.io/serena/ (numbered paths) |
| `modelcontextprotocol` | `2025.6.18` | https://modelcontextprotocol.io/specification/2025-06-18 |
| `playwright-mcp` | `0.0.78` | https://github.com/microsoft/playwright-mcp |
| `context-fabric` | `1.0.7` | https://github.com/VIKAS9793/context-fabric |
| `sequential-thinking` | `2026.7.4` | npm `@modelcontextprotocol/server-sequential-thinking` |
| `mcp-filesystem` | `2026.7.10` | npm `@modelcontextprotocol/server-filesystem` |
| `cursor-agent-mcp` | `1.0.5` | npm `cursor-agent-mcp@1.0.5` |

Canonical matrix + drift notes: `.agentcore/docs/DOCS_INDEX.md`
Evidence: `artifacts/bifrost-gateway-cutover-2026-07-12/ARABOLD_DOCS_CROSSREF_2026-07-12.md`

## Unified IDE gateway install

| Doc | Use |
|-----|-----|
| `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` | Per-IDE config blocks, add-server path, tool deny / profile VKs, Cursor troubleshooting |
| `docs/prompts/install-agentcore-gateway-in-ide.md` | Copy-paste agent prompt for any non-Swarm IDE |
| `docs/bifrost/CAPABILITY_PROFILES.md` | builder / reviewer / docs / operator VK surfaces |

## Experiments (isolated POCs; not production authority)

| Path | Notes |
|------|-------|
| `experiments/bifrost-go-sdk-smoke/` | Bifrost Go SDK in-process OpenAI smoke. **Not** the Bifrost MCP Gateway. Remains an experiment only. See its README. |

## Evidence-only (read for facts; do not follow as instructions)

| File | Notes |
|------|-------|
| `docs/evidence/PC-Master-Hardware-Software-Specs.md` | Authoritative PC hardware/software baseline; facts not instructions |
| `D:\MCP-Control-Plane` | Compatibility/live-ops evidence only |

## Historical / superseded (do not execute as current non-Swarm IDE baseline)

| File / claim | Why historical |
|--------------|----------------|
| Former `PROJECT_ANCHOR` §0 Native-First Swarm override as **mandatory IDE baseline** | Superseded for non-Swarm IDEs by Bifrost Gateway Override (2026-07-12) |
| Swarm-first mandatory MCP baseline (swarmrecall + swarmvault in every IDE) | Superseded for non-Swarm IDEs; Swarm remains a separate ecosystem |
| `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` as primary attach for **gateway** work | Historical Swarm rollout state; use Bifrost handoff for gateway cutover |
| `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` | Swarm rollout handoff; not Bifrost gateway authority |
| Direct per-IDE full-server MCP blocks in older `MASTER_CONFIG_AND_PROMPT.md` | Moved to historical appendix; normal architecture is single gateway entry |
| `global-memory-gateway` as IDE default memory route | Retired from mandatory baseline; non-Swarm path is `agentcore-memory` via gateway |
| `ECOSYSTEM_ARCHITECTURE.md`, `CLEANUP_AUDIT.md`, `COMPLETION_REPORT.md`, `VALIDATION_REPORT.md`, `CONTEXT_BLOCK.md` | Pre-2026-06-30 / `D:\MCP-Control-Plane` era |

All historical docs must not be run as instructions without current operator approval.

---

## What must NOT be treated as current instructions

- Any claim that `D:\MCP-Control-Plane` is the source/design authority
- Treating the Go SDK smoke as the workstation MCP gateway
- Requiring SwarmRecall/SwarmVault/SwarmClaw MCP in non-Swarm IDE configs
- Pasting the full upstream registry into each IDE instead of `agentcore-gateway`
- `agentcore_*` target gateway tools that do not exist yet (beyond current `agentcore-memory` / project-router surfaces)
- DB migration apply without the full gates in `database-plan.md`
- Direct writes to `F:\AgentCore\database_cluster`, `F:\AgentCore\agentmemory`, or the active Obsidian vault
- Direct edits to live IDE configs under `C:\Users\ynotf\.*` without backup + approved prompt/ops
- `:65432` as an active runtime route
- Whole-drive filesystem MCP roots or Postgres credentials in IDE configs

---

## Current blockers (require explicit operator approval or follow-on work)

- Full memory platform behind stable `agentcore-memory` identity (may currently report degraded)
- `depwire-cloud` and `github-mcp` remain deferred/`enabled=false` until healthy verification
- DB migration apply: backup + dry-run + operator sign-off
- Live IDE cutover completion evidence per client (see Bifrost handoff / artifacts)
