# MAF Recall Realignment Package

In-repo operator package for aligning Microsoft Agent Framework (MAF) planning with
AgentCore / SwarmRecall / Bifrost realities on this PC. This directory is documentation,
policy, checklists, and bounded spikes — not a second production memory plane.

## What this package is

| Artifact | Role |
|----------|------|
| `common_mcp_policy.yaml` | Machine policy: single gateway, forbid raw Recall/OpenRouter MCP |
| `architecture.md` | Corrected layers vs Copilot-style mistakes (ports, drives, ownership) |
| `install_checklist.md` | Ordered install / cutover checklist |
| `tool_context_registry.md` | Where each tool/context surface actually lives |
| `memory_contract.md` | SwarmRecall semantic store vs LangGraph PG18 checkpoints |
| `devin_outpost/` | Isolated Devin worker image notes (binds on `I:/LocalApps`) |
| `maf_host/` | Optional MAF SDK spike (pin 1.15.0 later); does not own memory |
| `foundry_local_notes.md` | Local GPU (4070 SUPER) inference notes — not Foundry cloud memory |
| `agentcore_freeze_note.md` | Freeze AgentCore feature work until MAF/Recall adapter is behind `:8080` |
| `post_build_audit.md` | Post-build audit template |
| `inventory_ide_mcp.ps1` | Inventory IDE MCP configs (orchestration entrypoint) |
| `enroll_gateway_clients.ps1` | Enroll `agentcore-gateway` only (orchestration entrypoint) |
| `docker_tune.ps1` | Docker/WSL VHDX placement checks (orchestration entrypoint) |

Audit / status companions (outside this folder):

- `audits/MAF_RECALL_REALIGNMENT_AUDIT_2026-08-26.json`
- `docs/handoffs/MAF_RECALL_REALIGNMENT_STATUS_2026-08-26.md`

## Non-negotiable facts

1. **Docker engine disk** — WSL2 VHDX for Docker Desktop lives under `F:/Docker/wsl` (AgentCore hot disk), **not** on `C:` or `D:`. App bind mounts for neutral local apps use `I:/LocalApps`.
2. **Ecosystem isolation** — Swarm hot runtime stays on `H:`; AgentCore / LangGraph hot runtime stays on `F:`. Do not cross-mount production roots into Devin/MAF containers by default.
3. **Common MCP** — Non-Swarm IDEs use one entry: `agentcore-gateway` at `http://127.0.0.1:8080/mcp` (Bifrost). Auth via User-scope `BIFROST_MCP_VIRTUAL_KEY`. No raw SwarmRecall MCP, no Recall keys in IDE configs, no direct `127.0.0.1:65432`.
4. **MAF is SDK later** — Microsoft Agent Framework is adopted as a **host SDK** behind the existing gateway later (pin `agent-framework==1.15.0` when activated). MAF does **not** replace Bifrost, does **not** invent a new Postgres on `F:`, and does **not** become a second MCP aggregator in IDE baselines.

## Professional baseline decisions

- **Shared external capability** goes through `agentcore-gateway`. That is the common control point for memory, policy, and cross-IDE visibility.
- **Vendor-native built-ins** may remain only when they are documented, local to the app, and do not create a second shared memory/database plane. Current Devin and Codex extras are transition exceptions, not the long-term target.
- **Local Devin is the default coder path.** No token is required for ordinary local code execution in Devin Next / CLI. Outpost tokens are only for optional isolated worker sessions managed by Devin Cloud.
- **OneDrive-backed Desktop is not a professional home for active repos.** Use `D:/github` or `D:/devin-workspace` for project roots. Keep Desktop for shortcuts, notes, and light files only.
- **Docker cleanup must stay bounded.** Do not broad-prune live project images or SwarmRecall quarantine volumes just to make Docker look tidy.

## Vibe-coder support model

This package assumes an operator who writes large natural-language prompts and wants agents to
finish work with minimal babysitting.

- Non-trivial tasks should automatically use planning/reasoning helpers such as `sequential-thinking`.
- Cross-file code changes should use `Serena` or an equivalent project-local semantic tool before editing.
- Structural work should use `Depwire` / Depra-class graph tooling and `Tentra` when architecture evidence is required.
- Durable memory and handoff artifacts should carry the rolling context so prompt length does not force repeated human restatement.
- The right fix for long prompts is better tool-assisted recovery and orchestration, not more ad-hoc MCP servers or a second memory database.

## Read order

1. `architecture.md` then `memory_contract.md` then `common_mcp_policy.yaml`
2. `tool_context_registry.md` then `install_checklist.md`
3. Spikes: `devin_outpost/README.md`, `maf_host/README.md`
4. Operator freeze / audit: `agentcore_freeze_note.md`, `post_build_audit.md`

## Authority

Conflicts resolve to `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `BLUEPRINT.md`, and
`docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`. Swarm mutable facts remain under
`D:/github/swarm-ecosystem-control`.
