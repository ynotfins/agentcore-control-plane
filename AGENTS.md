# CHAOSCENTRAL MCP Control Plane Agent Contract

This repository, `D:\github\agentcore-control-plane`, is the canonical Git source repo for MCP governance, Bifrost gateway contracts/renderers, and repo validators.

Runtime and machine-state authority is classified by `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, and current evidence/handoff documents. Do not treat compatibility/live-ops roots as design authority.

**Start here (read in this order):** `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `BLUEPRINT.md` → `CONTEXT_BLOCK.md` → `contracts/bifrost-upstream-mcp-registry.json` + `contracts/agentcore-gateway-client.json` → `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md` → `MASTER_CONFIG_AND_PROMPT.md`. For memory/database work, also read `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` (implementation authority). Project execution policy: `docs/agent-policy/`.

## Operating Rules

- Work primarily in this repository unless the user explicitly authorizes live rollout.
- Do not edit live client configs during repo-only phases.
- Create a timestamped rollback copy before editing existing managed files.
- Use unlock -> edit -> validate -> re-lock for managed files.
- Patch Bifrost renderers/`scripts/bifrost/render_bifrost_config.py` (and `scripts/mcp_control_plane.py` when still relevant) first when generated outputs would otherwise drift.
- Keep contracts, Bifrost renderers, gateway-client renderers, ops scripts, and validators aligned.
- Use deterministic validators before reporting completion (`scripts/bifrost/validate_contracts.py`, project validators).
- AgentCore does not use `.env` files for secrets or local runtime configuration. Use Windows environment variables only.
- Persistent memory writes go through `agentcore-gateway` → `agentcore-memory` only. Memory/database implementation follows `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`. (`AGENT_DATABASE_BOOTSTRAP.md` and `contracts/global-memory-database-contract.json` are historical PG16-era evidence; read them only for live PG16 cluster facts, never as current instructions.)
- **Git policy:** Push after every completed task. Run the narrowest relevant validation, run a secret/junk scan, stage only source-controlled files, commit with a concise message, push `origin main` (or the active task branch). Do not pull, fetch, merge, rebase, or remote-update unless the operator explicitly asks. Never force-push without explicit operator approval. See `docs/GIT_PUSH_ONLY_POLICY.md`.
- On every new project/repo, the agent MUST create `AGENTS.md` and `CLAUDE.md` at the project root if missing (seed from the Root Agent Rules Template in `MASTER_CONFIG_AND_PROMPT.md`), and must read/verify both at the start of every session and update them when project rules or wiring change.

## Tool Routing (non-Swarm / control-plane work)

- **IDE MCP primary:** use the single Bifrost `agentcore-gateway` entry defined by `PROJECT_ANCHOR.md` and `contracts/agentcore-gateway-client.json`. Do not paste the full upstream registry into each IDE.
- **Planning:** `sequential-thinking` (via gateway).
- **Repo code work:** Serena via **project router** (`agentcore-project-router` activate → Serena wrapper). Prefer project-scoped cwd.
- **Depwire:** Prefer Depwire **through agentcore-gateway** after cutover. Local Depwire CLI/MCP remains available for diagnostics and exact workspace graphs; Depwire Cloud stays deferred until enabled/healthy in the registry.
- **Tentra:** Local mode only; launch via project-router wrapper and follow current classified evidence for mutable data paths.
- **Docs:** `arabold-docs` first for current library/SDK/docs answers. Keep Bifrost docs indexed (`bifrost` / `2.0.0-prerelease1`).
- **Memory (non-Swarm):** `agentcore-memory` stable identity via gateway (may be degraded until memory platform lands). Do not route normal non-Swarm IDE work through SwarmRecall/SwarmVault.
- **Project continuity:** `context-fabric` only for approved Git-managed workspaces via project router; do not initialize under Swarm or runtime memory roots.
- **Architecture scans:** `artiforge` for high-leverage scans only.
- **Connected app workflows:** keep Composio quarantined until explicitly re-enabled.

## Swarm exclusion boundary

SwarmRecall, SwarmVault, and SwarmClaw are a **separate ecosystem**. This control plane's non-Swarm IDE baseline must not depend on them. Do not modify Swarm product code or require Swarm MCP entries in Cursor/Codex/Claude/MiniMax/Mavis/Antigravity/Open Interpreter for AgentCore gateway work. OpenClaw/ClawX are outside Bifrost IDE cutover scope.

## Stop Policy

For `agentcore-gateway` / Bifrost, `arabold-docs`, `artiforge`, `sequential-thinking`, and Depwire when structural verification is required: do not silently downgrade. If the primary fails and no high-quality fallback exists, stop and notify the user. Local Depwire CLI may be used as a diagnostic fallback when the gateway path is down — say so explicitly.

## Project Execution (all managed projects)

- Follow `docs/agent-policy/DOCUMENTATION_READ_ORDER.md` for the per-project read sequence.
- New projects run Milestone 0 (Bootstrap) per `docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md` before broad implementation.
- Milestones use entry/exit gates per `docs/agent-policy/MILESTONE_EXECUTION_STANDARD.md`; Micro steps require evidence per `docs/agent-policy/CHECKLIST_STANDARD.md`.
- Progressive tool disclosure per `docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`: only currently needed tools exposed; tool audits at every Milestone entry and exit. Runtime lease enforcement arrives with memory-platform M6; until then `TOOL_MANIFEST.yaml` records policy/desired state only.

## Database Contract

- Canonical Git source repo: `D:\github\agentcore-control-plane`
- Mutable machine, service, database, Milestone, and runtime state belongs in the generated STATE projections, current handoff/evidence, and `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md` classified documents. Do not duplicate mutable runtime facts as permanent AGENTS.md rules.
- **Memory/database implementation authority:** `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`
- Normal non-Swarm IDE memory identity: `agentcore-memory` via gateway (no direct SQL; no Postgres credentials in IDE configs)
- Trusted direct SQL is limited to explicitly approved ingest/admin runners.

## Learned User Preferences

- When checkpointing inherited dirty state, inventory/classify files, scan for secrets/junk/generated/oversized artifacts, and commit the checkpoint separately.
- Keep authority-reconciliation tasks scoped to rules, validators, profiles, and handoffs; defer runtime platform work until the required memory-platform milestone exists.
- Exclude unrelated runtime files, live configs, credentials, databases, caches, backups, and raw config dumps from repository commits.

## Learned Workspace Facts

- `BLUEPRINT.md` is the locked implementation authority for all memory-platform Milestones. Read the generated project `STATE.md` and current handoff/evidence for the active Milestone, branch, commit, and runtime status.
- LangGraph checkpoint tables live in the `public` schema of `agent_core` DB: `public.checkpoints`, `public.checkpoint_blobs`, `public.checkpoint_writes` — created by `PostgresSaver.setup()`; there is no separate `checkpoints` schema.
- M6 workflow tables use the `wf_` prefix (not `workflow_`) to avoid naming collision with M2 identity tables.
- Deep Agents is approved only as a bounded worker harness inside AgentCore-managed LangGraph nodes. It must not own canonical memory, workflow authority, policy, capability leases, STATE projections, Bifrost configuration, or IDE configuration. Deep Agents MemoryMiddleware and independent LangSmith ownership remain disabled unless current authority explicitly changes that decision.
- `agentcore_workflow/db.py` uses `admin=True` (postgres superuser) for all DB ops because `agentcore_worker` role must call `set_config('agentcore.current_project_id', ...)` before SECURITY DEFINER functions like `create_capability_lease` are accessible.
- Engineering Constitution at `docs/engineering/CONSTITUTION.md`; dependency catalog at `docs/engineering/dependency-catalog/catalog.yaml`.
- Approved Copier templates must set `_templates_suffix: ""` in `copier.yml` when full-file Jinja rendering is required.
