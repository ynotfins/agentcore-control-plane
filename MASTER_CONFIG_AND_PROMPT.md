# MASTER_CONFIG_AND_PROMPT.md

**Updated:** 2026-07-12 — Bifrost MCP Gateway rebuild
**Authority:** `PROJECT_ANCHOR.md` §0 Bifrost Gateway Override
**Contracts:** `contracts/agentcore-gateway-client.json`, `contracts/bifrost-upstream-mcp-registry.json`

Reusable root-level master setup guide for AgentCore after the Bifrost cutover. Normal non-Swarm IDE architecture is a **single** `agentcore-gateway` entry. Upstream MCP servers live behind Bifrost — not pasted into each IDE.

```text
IDE -> agentcore-gateway (127.0.0.1:8080/mcp)
    -> Bifrost native Gateway (H:\AgentRuntime\bifrost)
    -> upstream MCP registry (contracts)
```

Secrets live only in Windows User-scope environment variables. No `.env` files.

---

## 1. Authority


| Role                                   | Path                                |
| -------------------------------------- | ----------------------------------- |
| Source / config authority              | `D:\github\agentcore-control-plane` |
| Bifrost runtime                        | `H:\AgentRuntime\bifrost`           |
| Compatibility / live-ops evidence only | `D:\MCP-Control-Plane`              |


Constitution: `PROJECT_ANCHOR.md`
Document hierarchy: `DOC_AUTHORITY.md`
Current state / target architecture: `CONTEXT_BLOCK.md`
Memory/database implementation authority: `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`
Project execution policy: `docs/agent-policy/`
Agent contract: `AGENTS.md`
Handoff: `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md`

**Operator approval:** Bifrost cutover task (2026-07-12) authorized this rebuild. The Go SDK smoke under `experiments/bifrost-go-sdk-smoke/` is **not** the MCP gateway.

Drive map:

```text
C: OS/apps/live IDE configs
D: source repos / config authority
E: docs archive / cold backups / exports
F: PostgreSQL / hot indexes / hot DB+search runtime
G: backup target
H: Bifrost runtime / models / caches / AgentRuntime
I: disposable scratch
J: portable
```

Forbidden: `:65432`, whole-drive filesystem MCP roots, Postgres credentials in IDE configs, requiring Swarm MCP in non-Swarm IDEs.

---

## 2. Machine evidence pointer

Canonical machine facts live in ChaosCentral / AgentCore evidence docs — not in ad-hoc chat memory:

- `docs/evidence/PC-Master-Hardware-Software-Specs.md` — hardware/software baseline (facts)
- `DOC_AUTHORITY.md` — what is authoritative vs historical
- `PROJECT_ANCHOR.md` — constitution endpoints and drive roles
- `.agentcore/docs/DOCS_INDEX.md` — arabold-docs library index (includes Bifrost)

Treat `D:\MCP-Control-Plane` as evidence only.

---

## 3. Bifrost gateway architecture

```text
Non-Swarm IDE
  -> HTTP MCP agentcore-gateway
     url:  http://127.0.0.1:8080/mcp
     auth: Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
  -> bifrost-http.exe (v2.0.0-prerelease1) at H:\AgentRuntime\bifrost
     config.json + sqlite config/logs stores
     mcp_server_auth_mode: headers
     content logging disabled; metadata logs bounded
  -> upstream stdio/http/router MCP clients from registry
```

Ops scripts: `ops/bifrost/` (Install/Start/Stop/Test/Backup/Restore/IdeGatewayCutover).
Render: `scripts/bifrost/render_bifrost_config.py` → `H:\AgentRuntime\bifrost\config.json` + sanitized `renderers/bifrost/`.
No Docker for the Gateway runtime. Bind localhost only.

Persistent Windows startup owner:

```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Stop-ScheduledTask  -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Get-ScheduledTask   -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Get-ScheduledTaskInfo -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
```

The scheduled task runs `ops\bifrost\Launch-AgentCoreBifrostGateway.ps1`, which keeps
`bifrost-http.exe` in the foreground so Task Scheduler can restart it on failure. Logs:
`H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log` and
`H:\AgentRuntime\bifrost\logs\bifrost-gateway.stderr.log`.

ADRs:

- `docs/adr/ADR-2026-07-12-bifrost-mcp-gateway.md`
- `docs/adr/ADR-2026-07-12-configuration-source-of-truth.md`

---

## 4. Canonical upstream registry

**File:** `contracts/bifrost-upstream-mcp-registry.json`
**Schema:** `contracts/schemas/bifrost-upstream-mcp-registry.schema.json`

Validate:

```powershell
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
```

Implemented registry posture (as of docs update; re-run validator for live truth):

- **12 enabled** upstream clients rendered into Bifrost
- **4 deferred/disabled:** `mcp-debugger`, `artiforge`, `depwire-cloud`, `github-mcp`
- Bifrost client names use underscores; AgentCore IDs keep hyphens
- Swarm IDs listed under `swarm_exclusion` must not appear in non-Swarm IDE baselines

Repaired runtime validation (2026-07-14):

- Authenticated direct MCP `initialize`, `notifications/initialized`, `tools/list`, and `arabold_docs-list_libraries` passed.
- Builder VK visible tool count: **127**.
- Expected prefixes present: `arabold_docs`, `depwire`, `tentra`, `sequential_thinking`, `context_fabric`, `filesystem`, `playwright`, `cursor_agent_mcp`, `agentcore_memory`, `agentcore_project_router`.
- Forbidden patterns absent: Swarm, raw Postgres/psql, whole-drive filesystem, Bifrost admin.
- Current upstream caveats: `obsidian_vault` and `serena` are disconnected/time out at the Bifrost upstream layer; the gateway itself remains healthy.

Classification matrix: `docs/bifrost/MCP_CLASSIFICATION_MATRIX.md`

---

## 5. Stable agentcore-memory identity

**Canonical id:** `agentcore-memory` (Bifrost name `agentcore_memory`)
**Implementation (current):** `scripts/agentcore_memory/server.py`
**Tools (M4 compact surface):** `memory_status`, `startup_context`, `retrieve_context`, `append_event`, `propose_fact`, `expand_source`, `session_open`, `session_close`, `build_handoff`, `docs_search`
**Note:** Health reachability is reported through `memory_status`; keep the server id stable and do not expose raw database/admin tools.

Non-Swarm path:

```text
IDE -> agentcore-gateway -> agentcore-memory
```

Never put `AGENT_CORE_PG*` credentials in IDE configs. Trusted SQL remains ops/admin only (`AGENT_DATABASE_BOOTSTRAP.md`, `contracts/global-memory-database-contract.json`).

---

## 6. Project router

**Canonical id:** `agentcore-project-router`
**Implementation:** `scripts/project_router/server.py`
**State file:** `H:\AgentRuntime\bifrost\state\active-project.json`
**Tools:** `project_list`, `project_activate`, `project_status`, `project_clear`

Project-scoped upstreams launch via wrappers:

```text
scripts/project_router/wrappers/
  serena.cmd
  depwire.cmd
  tentra.cmd
  context-fabric.cmd
  filesystem.cmd
```

Allowed roots: registered `D:\github\...` git worktrees. Reject Swarm / `F:\AgentCore\agentmemory` markers.

---

## 7. Capability profiles

See `docs/bifrost/CAPABILITY_PROFILES.md` and registry `capability_profiles`:


| Profile            | Primary use                    | VK env (name only)                  |
| ------------------ | ------------------------------ | ----------------------------------- |
| builder            | Full coding/planning           | `BIFROST_MCP_VIRTUAL_KEY`           |
| reviewer           | Read-focused review            | `BIFROST_MCP_VK_REVIEWER`           |
| database-validator | Memory/DB health without creds | `BIFROST_MCP_VK_DATABASE_VALIDATOR` |
| docs-knowledge     | Docs + notes                   | `BIFROST_MCP_VK_DOCS_KNOWLEDGE`     |
| operator           | Ops + routing                  | `BIFROST_MCP_VK_OPERATOR`           |


Do not invent profiles outside the registry. Never commit resolved VK values.

---

## 8. Canonical single IDE gateway connection

**Contract:** `contracts/agentcore-gateway-client.json`

Cursor's canonical global MCP file is:

```text
C:\Users\ynotf\.cursor\mcp.json
```

The normal Cursor baseline must contain exactly one AgentCore non-Swarm gateway entry named
`agentcore-gateway` at `http://127.0.0.1:8080/mcp`. Project-level `.cursor\mcp.json` or
`.mcp.json` gateway duplicates are not normal; project-specific behavior is selected through
`agentcore-project-router`, not by adding duplicate gateway entries under individual repos.
`MCP_DOCKER` is not part of the normal Cursor baseline; the former Docker profile overlapped
Bifrost and contained a broken `desktop-commander` server with missing `paths`.

Sanitized canonical entry (env form — never resolve secrets in Git):

### JSON-style clients (Cursor / MiniMax / Mavis / Claude / Antigravity / Open Interpreter)

```json
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      },
      "timeout": 300
    }
  }
}
```

### Codex TOML

```toml
[mcp_servers.agentcore-gateway]
url = "http://127.0.0.1:8080/mcp"
bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"
enabled = true
startup_timeout_sec = 300
tool_timeout_sec = 300
```

For Codex, `bearer_token_env_var` is the schema-correct environment-backed
Bearer mechanism. Do not place `${env:BIFROST_MCP_VIRTUAL_KEY}` inside
`http_headers`, because Codex defines `http_headers` as static values. Map the
shared 300-second timeout to `startup_timeout_sec` and `tool_timeout_sec`.

If a client cannot expand `${env:...}` in headers, materialize from Windows User env into the **live** config only during cutover — never commit the live secret-bearing file.

---

## 9. Client-specific renderers

Sanitized renderers (source-controlled):


| Client           | Renderer                                          |
| ---------------- | ------------------------------------------------- |
| cursor           | `renderers/gateway-clients/cursor.json`           |
| codex            | `renderers/gateway-clients/codex.json`            |
| claude-code      | `renderers/gateway-clients/claude-code.json`      |
| claude-desktop   | `renderers/gateway-clients/claude-desktop.json`   |
| minimax          | `renderers/gateway-clients/minimax.json`          |
| mavis            | `renderers/gateway-clients/mavis.json`            |
| antigravity      | `renderers/gateway-clients/antigravity.json`      |
| open-interpreter | `renderers/gateway-clients/open-interpreter.json` |


Live paths are listed in `contracts/agentcore-gateway-client.json` → `client_render_hints`.
Cutover automation: `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1`.
**Out of scope:** OpenClaw / ClawX.

---

## 10. Global IDE setup prompt

Source prompt file: `docs/prompts/install-agentcore-gateway-in-ide.md`.

Copy this prompt into any supported non-Swarm IDE-local agent when configuring MCP on this PC:

```text
Install the AgentCore Bifrost MCP gateway for this IDE.

Authority:
D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
D:\github\agentcore-control-plane\DOC_AUTHORITY.md
D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json
D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json
D:\github\agentcore-control-plane\docs\bifrost\UNIFIED_GATEWAY_SETUP.md
D:\github\agentcore-control-plane\docs\prompts\install-agentcore-gateway-in-ide.md

Goal:
Use exactly one non-Swarm AgentCore MCP baseline entry named agentcore-gateway:
http://127.0.0.1:8080/mcp
Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}

Runtime requirement:
Before editing the IDE config, prove the native Bifrost Gateway is running persistently:
- scheduled task: \AgentCore\AgentCore-Bifrost-Gateway
- app dir: H:\AgentRuntime\bifrost
- bind: 127.0.0.1:8080 only
- health: GET http://127.0.0.1:8080/health returns 200
- direct MCP initialize, initialized notification, tools/list, and one safe read-only tool call succeed

Safety rules:
- Back up the live IDE config before any change and record SHA-256.
- Preserve model, auth, account, sandbox, context, profile, theme, and non-MCP app settings.
- Do not print or commit secret values.
- Do not create .env files.
- Do not touch SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, or ClawX.
- Do not paste the full upstream registry into the IDE.

Steps:
1. Identify the real active MCP config path and schema for this IDE from contracts\agentcore-gateway-client.json.
2. Back up the config outside Git.
3. Remove direct duplicate baseline MCP entries now served by Bifrost.
4. For Cursor, remove MCP_DOCKER unless the operator explicitly approves a documented unique-capability exception.
5. Add or merge only agentcore-gateway using the schema-correct renderer for this IDE.
6. Use Windows User env BIFROST_MCP_VIRTUAL_KEY without printing it.
   For Codex, use bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY" plus startup_timeout_sec = 300 and tool_timeout_sec = 300; do not put the env placeholder in static http_headers.
7. If env-header expansion is unsupported, materialize the secret only into the app-owned live config as a last resort; never commit or report it.
8. Validate JSON/TOML syntax.
9. Fully restart/reload the IDE so environment references are visible.
10. Confirm the IDE shows agentcore-gateway connected/ready.
11. Confirm tools/list includes expected prefixes such as arabold_docs, depwire, tentra, sequential_thinking, context_fabric, filesystem, playwright, cursor_agent_mcp, agentcore_memory, and agentcore_project_router.
12. Confirm Swarm, raw database, whole-drive filesystem, and Bifrost admin tools are absent.
13. Activate the project through agentcore_project_router before project-scoped work.
14. Record sanitized evidence: IDE name, config path, backup path, hashes, discovery/tool count, blockers, rollback.

Canonical Cursor target:
C:\Users\ynotf\.cursor\mcp.json

Canonical Cursor JSON:
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      },
      "timeout": 300
    }
  }
}

Adding future MCP servers:
- Do not add new baseline MCP servers separately to every IDE.
- Add once to contracts\bifrost-upstream-mcp-registry.json.
- Pin version, index exact-version official docs with Arabold, classify scope, define transport/command/env/timeout/health/write risk/rollback.
- Define allowed tools, denied tools, and capability profiles.
- Render Bifrost config, validate schemas, restart Bifrost, test initialize/tools/list and one safe call.
- Update .agentcore/docs/DOCS_INDEX.md and evidence.
- Leave IDE configs unchanged unless the single gateway connection itself changes.

Tool suppression:
- Disable an upstream with enabled=false.
- Use named tools_to_execute allowlists.
- Use an empty allowlist for no tools.
- Use narrower virtual-key profiles.
- Avoid broad wildcard grants unless documented in the registry.

Do not claim completion from config files alone. Direct MCP and IDE discovery must pass.
```

---

## 11. Server-specific operating rules

General:

1. Prefer tools via `agentcore-gateway` after cutover.
2. Activate a project before Serena / Depwire / Tentra / Context Fabric / filesystem.
3. Stop policy: do not silently downgrade Bifrost, arabold-docs, artiforge, sequential-thinking, or required Depwire verification.
4. No Context7, raw Mem0, direct Composio, or Hostinger as baseline routes.

Root Agent Rules Template (seed `AGENTS.md` / `CLAUDE.md` on new repos):

```markdown
# AgentCore Gateway Operating Rules

D:\github\agentcore-control-plane is source authority.
H:\AgentRuntime\bifrost is Bifrost runtime (not design authority).
D:\MCP-Control-Plane is compatibility/live-ops evidence only.

On every new project/repo, create AGENTS.md and CLAUDE.md at the project root if missing
(seed from MASTER_CONFIG_AND_PROMPT.md), read/verify both at session start, and keep them updated.

Non-Swarm IDE MCP baseline is a single agentcore-gateway entry
(http://127.0.0.1:8080/mcp + Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}).
Do not paste the full upstream registry into each IDE.
Do not require SwarmRecall/SwarmVault/SwarmClaw for non-Swarm IDE work.

Use agentcore-memory (stable id; may be degraded) via the gateway for memory health/status.
Use agentcore-project-router before project-scoped tools.
Use arabold-docs for exact version docs; keep .agentcore/docs/DOCS_INDEX.md current.
Use Serena (via project router) before broad code edits.
Use sequential-thinking before architecture/migration/refactor decisions.
Use Depwire via gateway for structural impact; local Depwire CLI is diagnostic fallback.
Use Tentra local mode only (H:\AgentRuntime\tentra\data).
Use context-fabric only on approved Git workspaces via project router.
Use mcp-debugger for runtime/test failures instead of guessing.
Use Artiforge for complex multi-file strategy only.
Use Obsidian for human-readable notes/handoffs.

Project execution: follow docs/agent-policy/ in the control-plane repo —
run New Project Bootstrap (Milestone 0) before broad implementation; use
Milestones with entry/exit gates, Macro/Micro checklists with evidence,
Context Fabric and Arabold checkpoints, and tool audits at every Milestone
boundary. Expose only the tools the current Milestone needs (progressive
tool disclosure); read .agentcore/PROJECT_CHARTER.md, MILESTONES.md, and
TOOL_MANIFEST.yaml per docs/agent-policy/DOCUMENTATION_READ_ORDER.md.

Never put Postgres credentials or whole-drive filesystem roots in IDE configs.
Never use :65432. Never create .env files. Never print secrets.
Push after every completed task per docs/GIT_PUSH_ONLY_POLICY.md.
```

---

## 12. Depwire

- **Primary:** through `agentcore-gateway` → `depwire` (project-router wrapper).
- **Cloud:** registry `depwire-cloud` deferred/`enabled=false` until healthy; auth `Bearer env.DEPWIRE_API_KEY` when enabled.
- **Local diagnostic:** `depwire-cli` / `depwire mcp` still OK offline — see `DEPWIRE.md` and `docs/bifrost/DEPWIRE_RECONCILIATION.md`.
- Do not set `DEPWIRE_NO_TELEMETRY` unless operator requests.
- Ignore `.depwire/` and `depwire-output.json`.

---

## 13. Tentra

Local mode only (`tentra-mcp@1.3.3 --local`). Data: `H:\AgentRuntime\tentra\data`.
Details: `docs/bifrost/TENTRA_LOCAL_MODE.md`.

---

## 14. Arabold Docs

Primary docs MCP for libraries/SDKs/APIs (replaces Context7).
Index Bifrost docs as library `bifrost` version `2.0.0-prerelease1` from [https://docs.getbifrost.ai](https://docs.getbifrost.ai) — see `.agentcore/docs/DOCS_INDEX.md`.
Keep project manifests under `.agentcore/docs/` when indexing project-relevant libraries.

---

## 15. Serena

Pinned launcher via project-router wrapper (`serena.exe start-mcp-server ...`).
Always activate the target `D:\github\...` project first. Do not emit git-based `uvx` launch commands as the governed path.

---

## 16. Context Fabric

Project-scoped only via router wrapper. Approved Git-managed workspaces only.
Do not initialize under `F:\AgentCore\agentmemory` or Swarm roots.

---

## 17. Artiforge

HTTP upstream; connection string is `env.ARTIFORGE_MCP_URL` (compose PAT locally into User env — never commit). High-leverage scans/refactor strategy only.

---

## 18. Obsidian

Long-form human notes, decisions, runbooks. Launcher uses Windows env names (`OBSIDIAN_API_KEY`, `OBSIDIAN_BASE_URL`, etc.). REST default host `https://127.0.0.1:27124`. Never embed key values in Git.

---

## 19. Security

- Windows User-scope env vars only; no `.env` files.
- Never print or commit secrets, resolved VKs, PATs, DB passwords, or live secret-bearing IDE configs.
- Bifrost: headers VK auth; content logging disabled.
- Localhost bind only for gateway.
- No whole-drive filesystem roots; filesystem MCP is project-worktree scoped.
- No direct Postgres credentials in IDE MCP configs.
- See `SECURITY.md`.

---

## 20. Validation

Minimum deterministic checks:

```powershell
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
# Optional ops smoke (record actual results; do not fabricate):
# ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

Also: secret/junk scan before commit; IDE JSON/TOML parse after cutover; confirm single gateway entry per migrated client.

**Docs update note:** Contract schema validation and `ops\bifrost\Test-AgentCoreBifrostGateway.ps1` pass for the repaired runtime (12 enabled / 4 disabled-deferred). Live IDE acceptance remains evidenced only where ops tests and cutover evidence files exist — do not invent pass/fail beyond that.

---

## 21. Backup and rollback

- Backup root example: `E:\AgentCore-Backups\bifrost-gateway-cutover-20260712-223149`
- Hash manifest: `artifacts/bifrost-gateway-cutover-2026-07-12/BACKUP_MANIFEST.md`
- Runbooks: `docs/bifrost/MIGRATION_RUNBOOK.md`, `docs/bifrost/ROLLBACK_RUNBOOK.md`
- Ops: `Backup-AgentCoreBifrostConfig.ps1`, `Restore-AgentCoreBifrostConfig.ps1`

---

## 22. Swarm exclusion boundary

SwarmRecall, SwarmVault, and SwarmClaw are a **separate ecosystem**.

- Non-Swarm IDEs must not depend on Swarm MCP.
- Bifrost cutover must not modify Swarm product installs (exclude-only from IDE baselines).
- OpenClaw/ClawX are outside this IDE gateway cutover.
- Historical Swarm-first baseline docs are superseded for non-Swarm IDE work (`DOC_AUTHORITY.md`).

---

## APPENDIX: Historical direct per-IDE full-server blocks

> **ROLLBACK / HISTORICAL ONLY — NOT NORMAL ARCHITECTURE.**
> Before Bifrost, each IDE carried a full direct MCP server list (arabold-docs, serena, sequential-thinking, swarmrecall, swarmvault, filesystem with broad roots, etc.). That model drifted and is superseded by the single `agentcore-gateway` entry.
> Keep backups under `E:\AgentCore-Backups\...` for emergency restore. Do not present the blocks below as the current baseline. Prefer restore-from-backup over re-authoring a hybrid.

### Historical pattern (illustrative — do not deploy as normal)

```json
{
  "mcpServers": {
    "arabold-docs": { "command": "...", "args": ["..."] },
    "serena": { "command": "...", "args": ["..."] },
    "sequential-thinking": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sequential-thinking@..."] },
    "swarmrecall": { "url": "..." },
    "swarmvault": { "command": "...", "args": ["..."] }
  }
}
```

Per-IDE cleanup prompts under `docs/prompts/*-cleanup-prompt.md` may still describe older direct-server remediation; for gateway install use `docs/prompts/install-agentcore-gateway-in-ide.md` instead.

Experiment note: `experiments/bifrost-go-sdk-smoke/` remains an isolated Go SDK POC — not a rollback path for the MCP gateway.
