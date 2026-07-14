# CHAOSCENTRAL MCP Control Plane Agent Contract

This repository, `D:\github\agentcore-control-plane`, is the canonical Git source repo for MCP governance, Bifrost gateway contracts/renderers, and repo validators.

`H:\AgentRuntime\bifrost` is the Bifrost runtime root (not design authority).
`D:\MCP-Control-Plane` is compatibility/live-ops evidence only — not a design authority.

**Start here (read in this order):** `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `contracts/bifrost-upstream-mcp-registry.json` + `contracts/agentcore-gateway-client.json` → `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md` → `docs/prompts/install-agentcore-gateway-in-ide.md` → `MASTER_CONFIG_AND_PROMPT.md`.

## Operating Rules

- Work primarily in this repository unless the user explicitly authorizes live rollout.
- Do not edit live client configs during repo-only phases.
- Create a timestamped rollback copy before editing existing managed files.
- Use unlock -> edit -> validate -> re-lock for managed files.
- Patch Bifrost renderers/`scripts/bifrost/render_bifrost_config.py` (and `scripts/mcp_control_plane.py` when still relevant) first when generated outputs would otherwise drift.
- Keep contracts, Bifrost renderers, gateway-client renderers, ops scripts, and validators aligned.
- Use deterministic validators before reporting completion (`scripts/bifrost/validate_contracts.py`, project validators).
- AgentCore does not use `.env` files for secrets or local runtime configuration. Use Windows environment variables only.
- Agents must read `AGENT_DATABASE_BOOTSTRAP.md` and `contracts/global-memory-database-contract.json` before persistent memory writes or database ingestion that touch `agent_core`.
- **Git policy:** Push after every completed task. Run the narrowest relevant validation, run a secret/junk scan, stage only source-controlled files, commit with a concise message, push `origin main` (or the active task branch). Do not pull, fetch, merge, rebase, or remote-update unless the operator explicitly asks. Never force-push without explicit operator approval. See `docs/GIT_PUSH_ONLY_POLICY.md`.
- On every new project/repo, the agent MUST create `AGENTS.md` and `CLAUDE.md` at the project root if missing (seed from the Root Agent Rules Template in `MASTER_CONFIG_AND_PROMPT.md`), and must read/verify both at the start of every session and update them when project rules or wiring change.

## Tool Routing (non-Swarm / control-plane work)

- **IDE MCP primary:** Bifrost `agentcore-gateway` at `http://127.0.0.1:8080/mcp` with `Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`. Do not paste the full upstream registry into each IDE.
- **Planning:** `sequential-thinking` (via gateway).
- **Repo code work:** Serena via **project router** (`agentcore-project-router` activate → Serena wrapper). Prefer project-scoped cwd.
- **Depwire:** Prefer Depwire **through agentcore-gateway** after cutover. Local Depwire CLI/MCP remains available for diagnostics and exact workspace graphs; Depwire Cloud stays deferred until enabled/healthy in the registry.
- **Tentra:** Local mode only; data under `H:\AgentRuntime\tentra\data`; launch via project-router wrapper.
- **Docs:** `arabold-docs` first for current library/SDK/docs answers. Keep Bifrost docs indexed (`bifrost` / `2.0.0-prerelease1`).
- **Memory (non-Swarm):** `agentcore-memory` stable identity via gateway (may be degraded until memory platform lands). Do not route normal non-Swarm IDE work through SwarmRecall/SwarmVault.
- **Project continuity:** `context-fabric` only for approved Git-managed workspaces via project router; do not initialize under Swarm/`F:\AgentCore\agentmemory`.
- **Architecture scans:** `artiforge` for high-leverage scans only.
- **Connected app workflows:** keep Composio quarantined until explicitly re-enabled.

## Swarm exclusion boundary

SwarmRecall, SwarmVault, and SwarmClaw are a **separate ecosystem**. This control plane's non-Swarm IDE baseline must not depend on them. Do not modify Swarm product code or require Swarm MCP entries in Cursor/Codex/Claude/MiniMax/Mavis/Antigravity/Open Interpreter for AgentCore gateway work. OpenClaw/ClawX are outside Bifrost IDE cutover scope.

## Stop Policy

For `agentcore-gateway` / Bifrost, `arabold-docs`, `artiforge`, `sequential-thinking`, and Depwire when structural verification is required: do not silently downgrade. If the primary fails and no high-quality fallback exists, stop and notify the user. Local Depwire CLI may be used as a diagnostic fallback when the gateway path is down — say so explicitly.

## Database Contract

- Canonical Git source repo: `D:\github\agentcore-control-plane`
- Bifrost runtime: `H:\AgentRuntime\bifrost`
- Current live deployed ops evidence root: `D:\MCP-Control-Plane` (not design authority)
- Bootstrap contract: `AGENT_DATABASE_BOOTSTRAP.md`
- Machine contract: `contracts/global-memory-database-contract.json`
- Database: PostgreSQL `agent_core` on `127.0.0.1:55432`
- Vector store: `global_vector_memory_store` with pgvector `VECTOR(1536)`
- Normal non-Swarm IDE memory identity: `agentcore-memory` via gateway (no direct SQL; no Postgres credentials in IDE configs)
- Trusted direct SQL path: explicit ingest/admin runners approved by the control plane
- Gateway/ops credentials (never in IDE configs): `AGENT_CORE_PGUSER=agent_ingest` and `AGENT_CORE_PGPASSWORD` from Windows User env `AGENT_CORE_AGENT_INGEST_PASSWORD`
